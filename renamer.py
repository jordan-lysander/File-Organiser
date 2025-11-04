from pathlib import Path
import re

def get_clean_name(file: Path):
    filename = file.stem

    # remove all numbers 7 or more characters long
    clean_filename = re.sub(r'\d{7,}', '', filename)

    # remove all instances of domain names
    clean_filename = re.sub(r'\b[a-zA-Z0-9-]+\.(com|net|org|co\.uk)\b', '', clean_filename)

    # replace delimiters with spaces
    clean_filename = re.sub(r'[-_\.]+', ' ', clean_filename)

    # remove any extra spaces
    clean_filename = re.sub(r'\s+', ' ', clean_filename).strip()

    # capitalise the first letter of each word IF the word is all lowercase
    clean_filename = ' '.join(word.capitalize() for word in clean_filename.split())
    
    if clean_filename and clean_filename != filename:
        return clean_filename + file.suffix
    return None