import argparse
import categoriser as cat
import mover
from pathlib import Path
import logging

def init_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        filename='file_organiser.log',
        filemode='w'
    )

    logging.info('File Organiser script started.')

def main():
    init_logger()

    organised_files = {}

    target_path = Path(input("Choose the directory to organise: "))
    logging.info(f'Target directory selected: {target_path}')

    new_dir = target_path.parent / f'{target_path.name} (organised)'
    new_dir.mkdir(exist_ok=True)
    logging.info(f'Output directory set to: {new_dir}')

    cat.scan_directory(organised_files, target_path)
    mover.create_new_paths(organised_files, new_dir)

    logging.info('Script finished successfully.')
    print(organised_files)

if __name__ == "__main__":
    main()