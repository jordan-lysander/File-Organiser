import configparser
from pathlib import Path

CONFIG_PATH = Path('config.ini')
_config = configparser.ConfigParser()

if not CONFIG_PATH.exists():
    raise FileNotFoundError(f"Configuration file not found at: {CONFIG_PATH.resolve()}")

_config.read(CONFIG_PATH)

# --- LLM Settings ---
AI_MODE = _config.getboolean('settings', 'ai_mode', fallback=False)
AI_SERVER = _config.get('settings', 'ai_server', fallback='http://localhost:1234/v1')
AI_MODEL = _config.get('settings', 'ai_model', fallback='google/gemma-3-4b')

# --- General Settings ---
OPERATION_MODE = _config.get('settings', 'operation_mode', fallback='shortcut')
DRY_RUN = _config.getboolean('settings', 'dry_run', fallback=False)
DESTINATION = _config.get('settings', 'destination', fallback='')