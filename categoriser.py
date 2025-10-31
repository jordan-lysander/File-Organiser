import mimetypes
import filetype
from pathlib import Path
from renamer import clean_filename
from ai_renamer import rename_with_ai
import logging
from rules import EXTENSION_TO_CATEGORY as ext_to_cat

logger = logging.getLogger(__name__)

def get_mime(file: Path):
    """
    Determines the MIME type of a file. There are two layers to improve accuracy:
        #### Layer 1:
        Uses filetype.guess() to analyse the first 261 bytes of the given file and return the inferred MIME type.
        #### Layer 2:
        Uses mimetypes.guess_type() to check the file extension and match it to a MIME type.
    """
    try:
        # --- LAYER 1: Guess the file by its content
        # --- This is the most accurate method and will even identify files with invalid extensions
        kind = filetype.guess(file)
        if kind is not None:
            return kind.mime
        
        # --- LAYER 2: Guess the file by its extension
        # --- This is the fallback method - quicker, but not as accurate
        mime = mimetypes.guess_type(file)[0]
        if mime is not None:
            return mime
        
        # --- LAYER 3: If all else fails, return None
        return None
    
    except (PermissionError, OSError):
        logger.warning(f"Permission denied while trying to read '{file.name}'")
        return None
    
    except TypeError:
        logger.warning(f"Could not process file of unknown type: '{file.name}'")

def categorise(organised_files: dict[str, list], file: Path):
    category = None
    mime = get_mime(file)

    # --- LAYER 1: Use the result from get_mime()
    if mime:
        type = mime.split('/')[0]
        if type in ['image', 'video', 'audio', 'text', 'font']:
            category = type

    # --- LAYER 2: If get_mime returned None, fall back to the rules
    if not category:
        extension = file.suffix.lstrip('.').lower()
        category = ext_to_cat.get(extension)
    
    # --- LAYER 3: If all else fails, assign to 'other'
    if not category:
        category = 'other'
        logger.warning(f"Could not determine a specific category for '{file.name}'. Defaulting to 'other'")
    
    # Add the file to the dictionary
    if category not in organised_files:
        organised_files[category] = []
    organised_files[category].append(file)

    logger.debug(f"Categorised '{file.name}' as '{category}'")

def scan_directory(organised_files: dict, path: Path, settings: dict):
    logger.info(f"Scanning directory: {path}")
    for file in path.rglob("*"):
        if not file.is_file():
            continue

        print(f"File: {file.name}")

        if settings.get('ai_mode'):
            new_name = rename_with_ai(file, settings.get('ai_model'))
            if new_name:
                file = file.with_stem(new_name)
        else:
            file = clean_filename(file)

        categorise(organised_files, file)

if __name__ == "__main__":
    clean_filename()