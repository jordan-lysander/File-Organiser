import openai
import logging

logger = logging.getLogger(__name__)

class Client:
    """A client for interacting with an OpenAI-compatible LLM API."""
    def __init__(self, base_url: str, api_key: str = 'not-needed', model: str = 'local-model'):
        """
        Initialises the LLM client.

        Args:
            base_url (str): The base URL of the LLM server (e.g. "http://localhost:1234/v1").
            api_key (str): The API key for the service. Defaults to "not-needed".
            model (str): The model name to use for completions.
        """
        self.model = model
        try:
            self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
            logger.info(f"LLM client initialised for model '{model}' at '{base_url}'")
        except Exception as e:
            logger.error(f"Failed to initialise OpenAI client: {e}")
            self.client = None

    def chat_completion(self, messages: list[dict], temperature: float=  0.5) -> str | None:
        """
        Calls the chat completions endpoint of the LLM.

        Args:
            messages (list[dict]): A list of message dictionaries (e.g. [{"role": "user", "content": "..."}]).
            temperature (float): The sampling temperature to use.

        Returns:
            The content of the response message as a string, or None if an error occurred.
        """
        if not self.client:
            logger.error("LLM client is not initialised. Cannot make API call.")
            return None
        
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            completion = self.client.chat.completions.create(**params)
            response_content = completion.choices[0].message.content
            return response_content.strip() if response_content else None
        except openai.APIConnectionError as e:
            logger.error(f"Failed to connect to the LLM server: {e.__cause__}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during the LLM call: {e}")
            return None