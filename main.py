import sys
import argparse
import categoriser as cat
import mover
from pathlib import Path
import logging
import configparser

def init_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        filename='file_organiser.log',
        filemode='w'
    )

    logging.info('File Organiser script started.')

def init_argparser():
    parser = argparse.ArgumentParser(description="Organise files in a directory by category.")
    parser.add_argument("source", type=Path, help="The source directory to organise.")
    parser.add_argument("-d", "--destination", type=Path, default=None, help="The destination directory for organised files.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate the organisation without affecting files.")
    return parser.parse_args()

def load_settings(config_path='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_path)

    settings = {}

    if 'settings' in config:
        settings['ai_mode'] = config['settings'].getboolean('ai_mode', fallback=False)
        settings['ai_model'] = config['settings'].get('ai_model', fallback='')
        settings['operation_mode'] = config['settings'].get('operation_mode', fallback='shortcut')
        settings['dry_run'] = config['settings'].getboolean('dry_run', fallback=False)
        settings['destination'] = config['settings'].get('destination', fallback='')

    return settings

def main():
    init_logger()
    config_settings = load_settings()
    organised_files = {}

    # If command line arguments were provided...
    if len(sys.argv) > 1:
        # --- Non-interactive mode ---
        args = init_argparser()
        target_path = args.source

        dry_run = args.dry_run or config_settings.get('dry_run', False)

        if args.destination:
            new_dir = args.destination
        else:
            new_dir = target_path.parent / f'{target_path.name} (organised)'

        if dry_run:
            logging.info("--- DRY RUN MODE ENABLED ---")
    else:
        # --- Interactive mode (CLI prompts) ---
        print("--- File Organiser ---")
        target_path = Path(input("Enter the path of the directory to organise: "))
        dry_run = False

        new_dir = target_path.parent / f'{target_path.name} (organised)'

    if not target_path.is_dir():
        logging.error(f"Source path '{target_path}' is not a valid directory. Exiting...")
        print(f"Error: '{target_path}' is not a valid directory.")
        return
    
    logging.info(f"Target directory selected: '{target_path}'")

    new_dir.mkdir(exist_ok=True)
    logging.info(f"Output directory set to: '{new_dir}'")

    cat.scan_directory(organised_files, target_path, config_settings)
    mover.create_new_paths(organised_files, new_dir, dry_run=dry_run)

    logging.info('Script finished successfully.')
    print("Organisation complete. Check file_organiser.log for details.")

if __name__ == "__main__":
    main()