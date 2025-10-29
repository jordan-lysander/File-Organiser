from pathlib import Path
import win32com.client
import logging

logger = logging.getLogger(__name__)

def create_new_paths(organised_files: dict, root: Path):
    # create a shell instance to generate the shortcuts
    shell = win32com.client.Dispatch("WScript.Shell")

    for category, files in organised_files.items():
        new_dir = root / category
        new_dir.mkdir(exist_ok=True)
        logger.info(f"Validated category directory: {new_dir}")

        for file in files:
            base_name = file.name + '.lnk'
            shortcut_path = new_dir / base_name

            # handle duplicate filenames with an appended number
            counter = 1
            while shortcut_path.exists():
                new_name = f'{file.stem} ({counter}){file.suffix}.lnk'
                logger.warning(f"Shortcut '{shortcut_path.name}' already exists. Using '{new_name}'.")
                shortcut_path = new_dir / new_name
                counter += 1

            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.TargetPath = str(file.absolute())
            shortcut.save()
            logger.info(f"Created shortcut for '{file.name}' at '{shortcut_path}'")