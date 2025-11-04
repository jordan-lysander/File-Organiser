from pathlib import Path
import json
import logging
import hashlib
import re
from metadata import get_metadata
from .jsonparser import extract_json, parse_json
from .client import Client
from .prompts import CATEGORISATION_PROMPT, RENAMING_PROMPT, GLOBAL_PLANNING_PROMPT

logger = logging.getLogger(__name__)

class Planner:
    def __init__(self, client: Client):
        self.client = client
        self.MAX_FILES_IN_PROMPT = 500
        self._generic_stems = {
            "image","jpeg","jpg","png","tiff","tif","webp","svg",
            "video","audio","document","file","ppt","pptx","pdf","zip","archive"
        }

    def plan_global(self, files: list[Path]):
        """
        Holistic planning: descriptions + taxonomy + per-file assignments (by id).
        Returns: plan dict with keys 'descriptions', 'folders', 'assignments'.
        """
        if not files:
            return {"descriptions": {}, "folders": [], "assignments": {}}

        # 1) Build manifest with stable IDs
        id_map: dict[str, Path] = {}
        manifest: list[dict] = []
        for f in files[:self.MAX_FILES_IN_PROMPT]:
            fid = self._make_id(f)
            id_map[fid] = f
            m = get_metadata(f) or {}
            m.update({
                "id": fid,
                "name": f.name,
                "ext": f.suffix.lstrip(".").lower(),
            })
            manifest.append(m)
        trunc_note = "" if len(files) <= self.MAX_FILES_IN_PROMPT else f"\nNOTE: Only the first {self.MAX_FILES_IN_PROMPT} of {len(files)} files are shown."

        messages = [
            {"role": "system", "content": GLOBAL_PLANNING_PROMPT},
            {"role": "user", "content": f"Manifest (JSON array):\n{json.dumps(manifest, ensure_ascii=False)}{trunc_note}"},
        ]

        # 2) Call LLM and parse
        response = self.client.chat_completion(messages)
        if not response:
            logger.error("Global planning LLM call failed.")
            return {"descriptions": {}, "folders": [], "assignments": {}}

        js = extract_json(response)
        plan = parse_json(js)
        if not isinstance(plan, dict):
            logger.error("Global planning JSON parse failed.")
            return {"descriptions": {}, "folders": [], "assignments": {}}

        # 3) Validate and repair
        assignments = plan.get("assignments") or {}
        if not isinstance(assignments, dict):
            assignments = {}

        all_ids = set(id_map.keys())
        got_ids = set(assignments.keys())
        missing = all_ids - got_ids

        # Normalize, sanitize, and enforce rules
        safe_assignments: dict[str, dict] = {}
        used_by_folder: dict[str, set[str]] = {}

        for fid, a in assignments.items():
            if fid not in id_map or not isinstance(a, dict):
                continue
            folder = str(a.get("folder") or "Unsorted").strip().strip("/\\.")
            stem = str(a.get("stem") or id_map[fid].stem)

            # sanitize folder segments and stem
            folder = self._sanitize_rel_path(folder)
            stem = self._sanitize_stem(stem, original_stem=id_map[fid].stem)

            # enforce per-folder uniqueness
            folder_key = folder or "Unsorted"
            used = used_by_folder.setdefault(folder_key.lower(), set())
            base = stem
            i = 1
            while stem.lower() in used:
                i += 1
                stem = f"{base} ({i})"
            used.add(stem.lower())

            safe_assignments[fid] = {"folder": folder_key, "stem": stem}

        # Fill missing ids
        if missing:
            logger.warning(f"Global plan missing {len(missing)} items; applying fallback.")
            for fid in missing:
                f = id_map[fid]
                folder_key = "Unsorted"
                stem = self._sanitize_stem(f.stem, original_stem=f.stem)
                used = used_by_folder.setdefault(folder_key.lower(), set())
                base = stem
                i = 1
                while stem.lower() in used:
                    i += 1
                    stem = f"{base} ({i})"
                used.add(stem.lower())
                safe_assignments[fid] = {"folder": folder_key, "stem": stem}

        # Keep folders (optional) but ensure Windows-safe segments
        folders = plan.get("folders") or []
        folders = [self._sanitize_rel_path(str(p)) for p in folders if isinstance(p, str)]
        descriptions = plan.get("descriptions") or {}
        if not isinstance(descriptions, dict):
            descriptions = {}

        result = {
            "descriptions": descriptions,
            "folders": folders,
            "assignments": safe_assignments,
        }
        logger.info(f"Global plan coverage: {len(safe_assignments)}/{len(all_ids)}")
        return result

    # Helpers

    def _make_id(self, path: Path) -> str:
        h = hashlib.blake2b(digest_size=8)
        try:
            h.update(path.name.encode("utf-8", "ignore"))
            st = path.stat()
            h.update(str(st.st_size).encode())
            h.update(str(int(st.st_mtime)).encode())
        except Exception:
            pass
        return h.hexdigest()

    def _sanitize_rel_path(self, rel: str) -> str:
        # Normalize separators, remove invalid chars per segment
        parts = [p for p in re.split(r"[\\/]+", rel) if p]
        cleaned = []
        for p in parts:
            q = re.sub(r'[<>:"/\\|?*\x00-\x1F]', " ", p)
            q = re.sub(r"\s+", " ", q).strip(". ").strip()
            q = q[:60] if q else "Folder"
            cleaned.append(q or "Folder")
        return "/".join(cleaned)

    def _sanitize_stem(self, stem: str, original_stem: str) -> str:
        s = re.sub(r'[<>:"/\\|?*\x00-\x1F]', " ", stem)
        s = re.sub(r"\s+", " ", s).strip().strip(".")
        if not s:
            s = original_stem
        if s.casefold() in self._generic_stems:
            s = original_stem
        return s[:120] or original_stem

    def plan_categories(self, files: list[Path]) -> dict[str, str] | None:
        """Ask the LLM for a holistic categorisation plan."""
        manifest, total = self._build_manifest(files)
        truncation_note = self._get_truncation_note(total)

        messages = [
            {"role": "system", "content": CATEGORISATION_PROMPT},
            {"role": "user", "content": f"Manifest (JSON array):\n{manifest}{truncation_note}"},
        ]

        response = self.client.chat_completion(messages)
        if not response:
            return None
        
        logger.info(f"Category planning result: {response}")
        
        json_string = extract_json(response)
        return parse_json(json_string)

    def plan_renames(self, categorised_files: dict[str, list[Path]]) -> dict[str, str]:
        """Ask the LLM for per-category consistent renaming plans."""
        full_plan: dict[str, str] = {}
        for category, files in categorised_files.items():
            if not files:
                continue
            
            manifest, total = self._build_manifest(files)
            truncation_note = self._get_truncation_note(total)
            prompt = RENAMING_PROMPT.format(category=category)

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Here are the files in this category:\n{manifest}{truncation_note}"},
            ]

            response = self.client.chat_completion(messages)
            if not response:
                processed = self._fallback_rename_plan(files, {})
                full_plan.update(processed)
                continue
            
            json_string = extract_json(response)
            category_plan = parse_json(json_string)
            
            if not isinstance(category_plan, dict):
                logger.warning(f"Could not parse rename plan for category '{category}'")
                category_plan = {}

            processed = self._postprocess_rename_plan(files, category_plan)            
            full_plan.update(category_plan)

        return full_plan
    
    def _postprocess_rename_plan(self, files: list[Path], plan: dict[str, str]) -> dict[str, str]:
        """Ensure every file has a descriptive, unique, Windows-safe stem."""
        stems: dict[str, str] = {}
        used: set[str] = set()

        for f in files:
            suggested = (plan.get(f.name) or f.stem).strip()

            # Remove illegal filename chars and collapse spaces
            suggested = re.sub(r'[<>:"/\\|?*\x00-\x1F]', ' ', suggested)
            suggested = re.sub(r'\s+', ' ', suggested).strip()
            if not suggested:
                suggested = f.stem

            # Avoid generic stems
            if suggested.lower() in self._generic_stems:
                suggested = f.stem

            # Enforce uniqueness within this category batch
            base = suggested
            i = 1
            while suggested.lower() in {s.lower() for s in used}:
                i += 1
                suggested = f"{base} ({i})"

            used.add(suggested)
            stems[f.name] = suggested

        return stems

    def _fallback_rename_plan(self, files: list[Path], plan: dict[str, str]) -> dict[str, str]:
        # Simple fallback to original stems with uniqueness
        return self._postprocess_rename_plan(files, plan)

    def _build_manifest(self, files: list[Path]) -> tuple[str, int]:
        total = len(files)
        subset = files[:self.MAX_FILES_IN_PROMPT]  # Limit to 500 files
        manifest = [get_metadata(f) for f in subset]
        return json.dumps(manifest, ensure_ascii=False), total

    def _get_truncation_note(self, total_files: int) -> str:
        if total_files > self.MAX_FILES_IN_PROMPT:
            return f"\nNOTE: Only the first {self.MAX_FILES_IN_PROMPT} of {total_files} files are shown."
        return ""