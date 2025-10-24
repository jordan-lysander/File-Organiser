import shutil
import argparse
import categoriser as cat
import rules
import mover
from pathlib import Path

def main():
    organised_files = {}

    target_path = Path(input("Choose the directory to analyse: "))

    new_dir = target_path.parent / f'{target_path.name} (organised)'
    new_dir.mkdir(exist_ok=True)

    cat.scan_directory(organised_files, target_path)
    mover.create_new_paths(organised_files, new_dir)

    print(organised_files)

    # for stem, suffix in files:
        # print(f"{stem}{suffix}")