# This file defines various prompt templates and functions for creating and managing prompts used in LLM calls.

GLOBAL_PLANNING_PROMPT = """
You are an expert file system organiser.

INPUT:
- A JSON array "manifest" of all files. Each entry includes:
  - id: stable identifier (string)
  - name: filename with extension
  - ext: lowercase extension (no dot)
  - size_kb: number or null
  - mime: string or null
  - image_resolution: "WxH" if available (optional)
  - video_resolution: "WxH" if available (optional)
  - duration_s: number of seconds if available (optional)

TASK:
1) Add a short, human-readable description for each file (based on its name, mime, and metadata).
2) Propose a compact, intuitive folder taxonomy (3–12 top-level folders, subfolders allowed) that groups related files meaningfully.
3) Assign EVERY file (by its id) to exactly one relative folder path (e.g., "Documents/Essays") and propose a descriptive filename STEM (no extension).
   - Stems must be Windows-safe: no <>:"/\\|?*, no control chars, no trailing dot, collapse spaces.
   - Stems must not be generic type names (e.g., "Image", "Jpeg", "Png", "Tiff", "Webp", "Audio", "Video", "Document").
   - Make stems unique within their assigned folder; if needed, append " (2)", " (3)", etc.
   - Preserve meaningful words from the original names and optionally add structured details (e.g., resolution for images).

CONSTRAINTS:
- OUTPUT MUST BE VALID JSON ONLY (no markdown fences, no commentary).
- Use the schema below exactly. Use the file ids as keys wherever keys are required.
- Cover ALL input ids exactly once in "assignments".

OUTPUT SCHEMA:
{
  "descriptions": {
    "<id>": "Short description",
    ...
  },
  "folders": [
    "Top",
    "Top/Sub",
    ...
  ],
  "assignments": {
    "<id>": {
      "folder": "Top/Sub",
      "stem": "Descriptive Stem"
    },
    ...
  }
}
"""


CATEGORISATION_PROMPT = """
You are an expert file system organiser.

TASK:
- Given a list of files as a JSON array of objects (the "manifest"), create a minimal, intuitive folder structure.
- Map every file to exactly one category folder.

RULES:
- Output MUST be a valid JSON object (no markdown fences or commentary).
- Keys MUST be the exact 'name' values from the manifest (including extension).
- Values MUST be concise, Title Case folder names (e.g., "Images", "Videos", "Audio", "Documents", "Presentations", "Spreadsheets", "Archives", "Fonts", "Executables", "Other").
- Use 3–12 categories total when reasonable; avoid over-fragmentation.
- Prefer conventional names; if uncertain, use "Other".
- Folder names must be Windows-safe (letters, numbers, spaces, hyphen, underscore only).

RETURN:
- ONLY a JSON object of the form:
  {
    "filename1.ext": "Category Name",
    "filename2.ext": "Category Name",
    ...
  }
"""

RENAMING_PROMPT = """
You are an expert file renaming utility.

TASK:
- Given a manifest of files that all belong to the '{category}' category, produce a consistent, descriptive filename STEM (no extension) for each.
- Enforce a uniform convention for this category (e.g. images may include resolution like 1920x1080; invoices may include Vendor and Invoice Number; fonts may include family and weight).

INPUT:
- A JSON array "manifest" where each entry has at least: name, ext, size_kb, mime. Images may also include image_resolution (e.g., "1920x1080").

RULES:
- Output MUST be a valid JSON object (no markdown fences or commentary).
- Keys MUST be the exact 'name' values from the manifest (including extension).
- Values MUST be filename STEMS only (no extension).
- Stems MUST be Windows-safe: no <>:"/\\|?*, no trailing dots, max ~120 chars, collapse multiple spaces.
- Stems MUST be descriptive (do NOT return generic type names like "Image", "Jpeg", "Png", "Tiff", "Webp", "Audio", "Video", "Document").
- Make stems unique; if duplicates are unavoidable, append a numeric suffix like " (1)".
- Preserve meaningful words from the original filename; add structured details when available (e.g., resolution for images).
- Do not change extensions; you are only returning stems.

RETURN:
- ONLY a JSON object of the form:
  {{
    "filename1.ext": "New Stem 1",
    "filename2.ext": "New Stem 2",
    ...
  }}
"""