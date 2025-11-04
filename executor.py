import logging
from pathlib import Path
import shutil
from file_operation import FileOperation as FileOp

logger = logging.getLogger(__name__)

def _create_shortcut(file: Path, shortcut_path: Path):
    """Creates a .lnk shortcut to 'file' at 'shortcut_path'."""
    # Ensure .lnk extension
    if shortcut_path.suffix.lower() != ".lnk":
        shortcut_path = shortcut_path.with_name(shortcut_path.name + ".lnk")

    try:
        import win32com.client
    except Exception as e:
        logger.error(f"win32com is required to create shortcuts: {e}")
        return

    shortcut_path.parent.mkdir(parents=True, exist_ok=True)

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(str(shortcut_path))
    shortcut.TargetPath = str(file.absolute())
    shortcut.WorkingDirectory = str(file.parent)
    # Set icon to the target file when possible (safe default)
    try:
        shortcut.IconLocation = str(file)
    except Exception:
        pass
    shortcut.save()
    logger.info(f"Created shortcut for '{file.name}' at '{shortcut_path}'")

def _handle_duplicates(path: Path) -> Path:
    """
    If 'path' exists, append a numeric suffix before the extension until a free name is found.
    Works for any file type, including .lnk shortcuts.
    """
    if not path.exists():
        return path

    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({counter}){path.suffix}")
        if not candidate.exists():
            logger.warning(f"Destination '{path.name}' already exists. Using '{candidate.name}'.")
            return candidate
        counter += 1

def execute_plan(plan: list[FileOp], dest_root: Path, mode: str, dry_run: bool):
    """Executes the planned file operations based on the operation mode."""
    logger.info(f"Executing plan with mode: '{mode}'. dry_run: {dry_run}")

    for op in plan:
        # Category may be nested like "Documents/Essays"
        category_dir = dest_root / op.category
        final_name = op.resolved_final_name
        base_dest_path = category_dir / final_name

        if dry_run:
            if mode == "shortcut":
                preview_dest = base_dest_path.with_name(base_dest_path.name + ".lnk")
            else:
                preview_dest = base_dest_path
            logger.info(f"[DRY RUN] Plan for '{op.source_path.name}':")
            logger.info(f"  - Category: {op.category}")
            logger.info(f"  - Final Name: {final_name}")
            logger.info(f"  - Operation: {mode}")
            logger.info(f"  - Destination: {preview_dest}")
            continue

        # Ensure destination category directory exists (for all but pure rename-in-place)
        if mode in {"move", "copy", "shortcut"}:
            category_dir.mkdir(parents=True, exist_ok=True)

        try:
            if mode == "move":
                final_dest_path = _handle_duplicates(base_dest_path)
                shutil.move(op.source_path, final_dest_path)
                logger.info(f"Moved '{op.source_path.name}' to '{final_dest_path}'")

            elif mode == "copy":
                final_dest_path = _handle_duplicates(base_dest_path)
                shutil.copy2(op.source_path, final_dest_path)
                logger.info(f"Copied '{op.source_path.name}' to '{final_dest_path}'")

            elif mode == "shortcut":
                link_path = base_dest_path.with_name(base_dest_path.name + ".lnk")
                link_path = _handle_duplicates(link_path)  # dedupe on the .lnk path
                _create_shortcut(op.source_path, link_path)

            elif mode == "rename":
                # Rename in place, ignore category_dir
                renamed_path = op.source_path.with_name(final_name)
                renamed_path = _handle_duplicates(renamed_path)
                op.source_path.rename(renamed_path)
                logger.info(f"Renamed '{op.source_path.name}' to '{renamed_path.name}'")

            else:
                logger.error(f"Unknown operation mode: {mode}")

        except Exception as e:
            logger.error(f"Failed to execute operation for '{op.source_path.name}': {e}")