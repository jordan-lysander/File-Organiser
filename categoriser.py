import os
import mimetypes
import filetype
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)

def get_mime(file: Path):
    try:
        mime = mimetypes.guess_type(file)[0]
        if mime == None:
            mime = filetype.guess_mime(file)
        return mime
    except (PermissionError, OSError, TypeError):
        return None

def categorise(organised_files: dict[str, list], file: Path):
    mime = get_mime(file)

    if mime:
        category = mime.split('/')[0]
    else:
        category = 'other'
        logger.warning(f"Unable to determine MIME type for '{file.name}'. Placing in 'other'.")

    if category not in organised_files.keys():
        organised_files[category] = [file]
    else:
        organised_files[category].append(file)
    logger.debug(f"Categorised '{file.name}' as '{category}'")

def scan_directory(organised_files: dict, path: Path):
    logger.info(f"Scanning directory: {path}")
    for file in path.rglob("*"):
        if not file.is_file():
            continue

        print(f"File: {file.name}")

        file = clean_filename(file)

        categorise(organised_files, file)

def clean_filename(file: Path):
    filename = str(file.stem)
    print(f"Original: {filename}")

    # remove all numbers 7 or more characters long
    clean_filename = re.sub(r'\d{7,}', '', filename)

    # remove all instances of domain names
    clean_filename = re.sub(r'\b[a-zA-Z0-9-]+\.(com|net|org|co\.uk)\b', '', clean_filename)

    # replace delimiters with spaces
    clean_filename = re.sub(r'[-_\.]+', ' ', clean_filename)

    # remove any extra spaces
    clean_filename = re.sub(r'\s+', ' ', clean_filename).strip()

    # capitalise the first letter of each word IF the word is all lowercase
    clean_filename = re.sub(r'\b\w+\b',
                            lambda m: m.group(0).capitalize() if m.group(0).islower() else m.group(0),
                            clean_filename)

    print(f"Cleaned: {clean_filename}")
    return file.with_stem(clean_filename)

if __name__ == "__main__":
    clean_filename()