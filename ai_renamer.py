import openai
import logging
from pathlib import Path
from datetime import datetime
import base64
from PIL import Image
import io
from rules import FILE_TYPES

logger = logging.getLogger(__name__)

#region Constants & Client Initialisation

# Access the locally running LLM though LM Studio's default port
client = openai.OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

SYSTEM_PROMPT = (
    "You are a file renaming utility. Your task is to create a clean, descriptive, "
    "and concise filename stem (without the extension) based on the context provided. "
    "If an image is provided, base the name on its content. Otherwise, use the text metadata. "
    "The new name should be in Title Case.\n\n"
    "IMPORTANT: Your response must contain ONLY the new filename stem and nothing else."
)

#endregion

#region Public Functions

def rename_with_ai(file: Path, model: str) -> str | None:
    """Uses a locally running LLM to suggest a new filename."""
    stem = file.stem
    type = file.suffix.lstrip('.').lower()
    try:
        time = datetime.fromtimestamp(file.stat().st_birthtime)
    except AttributeError:
        time = datetime.fromtimestamp(file.stat().st_ctime)
    date = time.strftime("%Y-%m-%d")

    is_image = type in FILE_TYPES.get('image', [])
    new_name = None

    if is_image:
        logger.info(f"Attempting multimodal renaming for '{file.name}'")
        img_base64 = _encode_image_to_base64(file)
        if img_base64:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': f"Rename this file.\nOriginal Name: '{stem}'\nCreation Date: '{date}'"},
                        {'type': 'image_url', 'image_url': {'url': f"data:image/jpeg;base64,{img_base64}"}}
                    ]
                }
            ]
            new_name = _call_llm(messages, model)

    if new_name is None or new_name == "VISION_FALLBACK":
        logger.info(f"Using text-only renaming for '{file.name}'")
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Rename this file.\nOriginal Name: '{stem}'\nFile Type: '{type}'\nCreation Date: '{date}'"}
        ]
        new_name = _call_llm(messages, model)

    if new_name and new_name != "VISION_FALLBACK":
        logger.info(f"Suggested new name: '{new_name}'")
        return new_name
    
    return None

#endregion

#region Private Functions

def _encode_image_to_base64(file: Path) -> str | None:
    """Encodes an image file to a base64 string for API consumption."""
    try:
        with Image.open(file) as img:
            buffered = io.BytesIO()
            img.convert("RGB").save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        logger.error(f"Could not process image file '{file.name}': {e}")
        return None
    
def _call_llm(messages: list, model: str) -> str | None:
    """Calls the loaded LLM with the message payload given as an argument."""
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=80,
        )
        return completion.choices[0].message.content.strip().replace('"', '')

    except openai.APIConnectionError:
        logger.error("Renaming failed: Could not connect to the local LLM server")
        return None
    
    except openai.BadRequestError as e:
        logger.warning(f"Multimodal request failed (model may not support images). Falling back to text only. Error: {e}")
        return "VISION_FALLBACK"
    
    except Exception as e:
        logger.error(f"An unexpected error occurred during text-only processing: {e}")
        return None

#endregion
    
if __name__ == "__main__":
    test_path = Path("Root/f32-xt.PNG")
    if test_path.exists():
        suggested_name = rename_with_ai(test_path)
        if suggested_name:
            print(f"Original: {test_path.name}")
            print(f"Suggested: {suggested_name}")
    else:
        print(f"Test file not found: '{test_path}'")