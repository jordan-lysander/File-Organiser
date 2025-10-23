from pathlib import Path
import mimetypes
import filetype
import win32com.client

def get_mime(file: Path):
    mime = mimetypes.guess_type(file)[0]
    if mime == None:
        mime = filetype.guess_mime(file)
    
    return mime

def categorise(organised_files: dict[str: list], file: Path):
    category, suffix = get_mime(file).split('/')
    if category not in organised_files.keys():
        organised_files[category] = [file]
    else:
        organised_files[category].append(file)

def scan_directory(organised_files: dict, path: Path):
    for file in path.rglob("*"):
        if not file.is_file():
            continue

        print(f"File: {file.name}")

        categorise(organised_files, file)

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
        
def main():
    organised_files = {}

    target_path = Path(input("Choose the directory to analyse: "))

    new_dir = target_path.parent / 'Root (organised)'
    new_dir.mkdir(exist_ok=True)

    scan_directory(organised_files, target_path)
    create_new_paths(organised_files, new_dir)

    print(organised_files)

    # for stem, suffix in files:
        # print(f"{stem}{suffix}")

if __name__ == "__main__":
    main()
        
