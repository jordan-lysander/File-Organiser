import os
import mimetypes
import filetype
from pathlib import Path
import re

def get_mime(file: Path):
    try:
        mime = mimetypes.guess_type(file)[0]
        if mime == None:
            mime = filetype.guess_mime(file)
        return mime
    except (PermissionError, OSError, TypeError):
        return None

def categorise(organised_files: dict[str, list], file: Path):
    mime = get_mime(file).split('/')

    if mime:
        category = mime.split('/')[0]
    else:
        category = 'other'

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

def clean_filename():
    # file = str(filename.stem)
    file = "483428122_623339390852966_8917901137371630320_n..1741875441878.publer.com"
    print(f"Original: {file}")

    # remove all numbers 7 or more characters long
    new = re.sub(r'\d{7,}', '', file)
    # remove all instances of domain names
    new = re.sub(r'\b[a-zA-Z0-9-]+\.(com|net|org|co\.uk)\b', '', new)
    # replace delimiters with spaces
    new = re.sub(r'[-_\.]+', ' ', new)
    # remove any extra spaces
    new = re.sub(r'\s+', ' ', new).strip()

    print(f"Cleaned: {new}")

if __name__ == "__main__":
    clean_filename()