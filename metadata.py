import logging
from pathlib import Path
import mimetypes

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import filetype as _filetype
except ImportError:
    _filetype = None

from rules import EXTENSION_TO_CATEGORY as ext_to_cat

logger = logging.getLogger(__name__)

def get_mime(file: Path) -> str | None:
    """Determines the MIME type of a file using multiple strategies for accuracy."""
    try:
        if _filetype:
            kind = _filetype.guess(file)
            if kind:
                return kind.mime
        
        mime, _ = mimetypes.guess_type(file)
        if mime:
            return mime
        
        return None
    except (PermissionError, OSError):
        logger.warning(f"Permission denied while trying to read '{file.name}'")
        return None

def get_category(file: Path) -> str:
    """Determines the category for a file using rule-based logic with MIME fallback."""
    extension = file.suffix.lstrip('.').lower()
    category = ext_to_cat.get(extension)

    if not category:
        mime = get_mime(file)
        if mime:
            primary_type = mime.split('/')[0]
            if primary_type in ext_to_cat.values():
                category = primary_type
            else:
                category = ext_to_cat.get(mime)

    if not category:
        category = "Other"
        logger.warning(f"Could not determine a specific category for '{file.name}'. Defaulting to 'Other'")

    logger.debug(f"Categorised '{file.name}' as '{category}'")
    return category

def _get_image_resolution(path: Path) -> str | None:
    if not Image:
        return None
    try:
        with Image.open(path) as img:
            w, h = img.size
            return f"{w}x{h}"
    except Exception:
        return None

def get_metadata(file: Path) -> dict:
    """Gathers comprehensive metadata for a file, used for AI planning."""
    try:
        size_kb = round(file.stat().st_size / 1024, 1)
    except Exception:
        size_kb = None

    mime = get_mime(file)
    metadata = {
        'name': file.name,
        'ext': file.suffix.lstrip('.').lower(),
        'size_kb': size_kb,
        'mime': mime,
    }

    if mime and mime.startswith('image/'):
        res = _get_image_resolution(file)
        if res:
            metadata['image_resolution'] = res

    return metadata