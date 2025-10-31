from pathlib import Path
import re

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