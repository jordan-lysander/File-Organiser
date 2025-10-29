from pathlib import Path
import configparser
import logging

logger = logging.getLogger(__name__)

DEFAULT_RULES = {
    'image': ['jpg', 'png', 'gif', 'tif', 'bmp', 'svg'],
    'video': ['mp4', 'avi', 'wmv', 'mov', 'mpeg'],
    'audio': ['mp3', 'wav', 'aac', 'ogg', 'flac', 'midi'],
    'document': ['docx', 'pdf', 'txt', 'odt'],
    'presentation': ['pptx', 'odp'],
    'spreadsheets': ['xlsx', 'csv', 'ods'],
    'archives': ['zip', 'rar', '7z', 'tar', 'gz']
}

def load_rules(config_path='config.ini'):
    config = configparser.ConfigParser()
    if not Path(config_path).exists():
        logger.warning(f"'{config_path}' not found. Using default rules.")
        return DEFAULT_RULES
    
    config.read(config_path)

    rules = {}
    try:
        for category, extensions in config.items('file_types'):
            rules[category] = [e.strip() for e in extensions.split(',')]
        logger.info(f"Successfully loaded rules from '{config_path}'.")
        return rules
    except configparser.NoSectionError:
        logger.error(f"Config file '{config_path}' is missing the [file_types] section. Using default rules.")
        return DEFAULT_RULES
    
#region Rule Constants

# A dictionary mapping each category to its list of extensions as defined by
# the config file or the default rules
FILE_TYPES = load_rules()

# A dictionary that maps each extension to its category for fast lookups
EXTENSION_TO_CATEGORY = {
    ext: category
    for category, extensions in FILE_TYPES.items()
    for ext in extensions
}

#endregion