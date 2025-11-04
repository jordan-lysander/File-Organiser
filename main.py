import sys
import argparse
import logging
from pathlib import Path
from collections import defaultdict

from metadata import get_category
from renamer import get_clean_name

from llm_handler.client import Client
from llm_handler.planner import Planner

from executor import execute_plan
import config
from file_operation import FileOperation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    filename='file_organiser.log',
    filemode='w'
)
logging.info('File Organiser script started.')
logger = logging.getLogger(__name__)

def init_argparser():
    parser = argparse.ArgumentParser(description="Organise files in a directory by category.")
    parser.add_argument("source", type=Path, help="The source directory to organise.")
    parser.add_argument("-d", "--destination", type=Path, default=None, help="The destination directory for organised files.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate the organisation without affecting files.")
    return parser

def scan_files(path: Path):
    """Generator that scans a directory and yields the files"""
    logger.info(f"Scanning directory: '{path}'")
    for file in path.rglob('*'):
        if file.is_file():
            yield file

def main():
    parser = init_argparser()
    op_mode = config.OPERATION_MODE

    # If command line arguments were provided...
    if len(sys.argv) > 1:
        # --- Non-interactive mode (Command-line arguments) ---
        args = parser.parse_args()
        target_path = args.source
        dry_run = args.dry_run or config.DRY_RUN

        if op_mode == 'rename':
            new_dir = target_path
        elif args.destination:
            new_dir = args.destination
        elif config.DESTINATION:
            new_dir = Path(config.DESTINATION)
        else:
            new_dir = target_path.parent / f'{target_path.name} (organised)'
    else:
        # --- Interactive mode (CLI prompts) ---
        print("--- File Organiser ---")
        target_path = Path(input("Enter the path of the directory to organise: "))
        dry_run = False

        if op_mode == 'rename':
            new_dir = target_path
        else:
            new_dir = target_path.parent / f'{target_path.name} (organised)'
        print(f"Output will be placed in: {new_dir}")

    if not target_path.is_dir():
        logging.error(f"Source path '{target_path}' is not a valid directory. Exiting...")
        print(f"Error: '{target_path}' is not a valid directory.")
        return
    
    logging.info(f"Target directory selected: '{target_path}'")
    if dry_run:
            logging.info("--- DRY RUN MODE ENABLED ---")

    # --- 1. Build the plan
    plan: list[FileOperation] = []
    print("\nScanning and planning operations...")
    if config.AI_MODE:
        # initialise the llm client and planner
        llm_client = Client(base_url=config.AI_SERVER, model=config.AI_MODEL)
        planner = Planner(llm_client)

        # Holistic AI path: collect all files, ask AI for categories and per-category consistent renames
        all_files = [f for f in scan_files(target_path)]
        file_by_name = {f.name: f for f in all_files}
        logger.info(f"Scanned files: {len(all_files)}")

        global_plan = planner.plan_global(all_files)

        assignments = global_plan.get("assignments", {})
        # Build id->Path map identical to planner
        import hashlib
        def _make_id(path: Path) -> str:
            h = hashlib.blake2b(digest_size=8)
            try:
                h.update(path.name.encode("utf-8", "ignore"))
                st = path.stat()
                h.update(str(st.st_size).encode())
                h.update(str(int(st.st_mtime)).encode())
            except Exception:
                pass
            return h.hexdigest()

        by_id = {_make_id(p): p for p in all_files}
        plan: list[FileOperation] = []

        for fid, a in assignments.items():
            p = by_id.get(fid)
            if not p:
                continue
            rel_folder = a["folder"]  # e.g., "Documents/Essays"
            stem = a["stem"]
            final_name = f"{stem}{p.suffix}"
            # Use nested folder path via category field (executor joins with dest_root)
            plan.append(FileOperation(source_path=p, category=rel_folder, final_name=final_name))

        execute_plan(plan, new_dir, op_mode, dry_run)


        print("  - Asking AI to plan categories holistically...")
        category_plan = planner.plan_categories(all_files)
        if not category_plan:
            logger.error("AI category planning failed; aborting.")
            return

        # Group by category according to AI plan
        grouped: dict[str, list[Path]] = defaultdict(list)
        for fname, cat in category_plan.items():
            p = file_by_name.get(fname)
            if p is not None:
                grouped[cat].append(p)

        logger.info(f"Planned by category: " + ", ".join(f"{k}={len(v)}" for k, v in grouped.items()))

        print("  - Asking AI to plan renames per category...")
        rename_plan = planner.plan_renames(grouped)

        # Build operations from AI plans
        for cat, paths in grouped.items():
            for p in paths:
                stem = rename_plan.get(p.name)
                new_name = f"{stem}{p.suffix}" if stem else None
                plan.append(FileOperation(source_path=p, category=cat, new_name=new_name))

        logger.info(f"Total operations planned: {len(plan)}")
    else:
        # Rule-based path: process file-by-file
        for file in scan_files(target_path):
            print(f"  - Processing: {file.name}")
            category = get_category(file)
            new_name = None if op_mode == 'shortcut' else get_clean_name(file)
            plan.append(FileOperation(source_path=file, category=category, new_name=new_name))

    # --- 2. Execute the plan
    print("\nExecuting plan...")
    execute_plan(plan, new_dir, op_mode, dry_run)

    logging.info('Script finished successfully.')
    print("\nOperation complete. Check file_organiser.log for details.")

if __name__ == "__main__":
    main()