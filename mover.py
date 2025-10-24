from pathlib import Path
import win32com.client

def create_new_paths(organised_files: dict, root: Path):
    shell = win32com.client.Dispatch("WScript.Shell")
    for category, files in organised_files.items():
        new_dir = root / category
        new_dir.mkdir(exist_ok=True)

        for file in files:
            shortcut_path = new_dir / (file.name + ".lnk")

            if not shortcut_path.exists():
                shortcut = shell.CreateShortCut(str(shortcut_path))
                shortcut.TargetPath = str(file.absolute())
                shortcut.save()