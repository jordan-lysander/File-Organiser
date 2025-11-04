import logging
import json

logger = logging.getLogger(__name__)

def extract_json(text: str) -> str:
    """
    Extracts a JSON object or array from a string, cleaning markdown fences.

    Args:
        text (str): The input string, potentially containing a JSON block.

    Returns:
        The extracted JSON string, or None if no valid block is found.
    """
    if not text:
        return ""
    
    t = text.strip()

    # find the start of the json block
    json_start = t.find("```json")
    if json_start != -1:
        t = t[json_start + 7:]
    else:
        json_start = t.find("```")
        if json_start != -1:
            t = t[json_start + 3:]

    # find the end of the json block
    json_end = t.rfind("```")
    if json_end != -1:
        t = t[:json_end]

    t = t.strip()

    # find the opening and closing braces '{}' and/or brackets '[]'
    first_brace = t.find('{')
    first_bracket = t.find('[')

    if first_brace == -1 and first_bracket == -1:
        return ""

    if first_brace == -1:
        start = first_bracket
    elif first_bracket == -1:
        start = first_brace
    else:
        start = min(first_brace, first_bracket)

    last_brace = t.rfind('}')
    last_bracket = t.rfind(']')
    end = max(last_brace, last_bracket)

    if start == -1 or end == -1 or start > end:
        return ""
    
    result = t[start : end + 1]
    logger.info(f"JSON extraction succeeded. Extracted data: {result[:500]}...")
    return result
    

def parse_json(json_string: str | None) -> dict | None:
    """
    Safely parses a JSON string into a Python dictionary or list.

    Args:
        json_string (str): The JSON string to parse.

    Returns:
        The parsed Python object, or None if parsing fails.
    """
    logger.info(f"Parsing extracted JSON...")
    if not json_string:
        return None
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding failed: {e}. Content: '{json_string[:100]}...'")
        return None