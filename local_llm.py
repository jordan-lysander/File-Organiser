import base64
import mimetypes
import io
from pathlib import Path
from PIL import Image
from config import AI_MODEL, AI_SERVER


TEXT_SUMMARY_PROMPT = """You are an expert document analyst. Your task is to identify the document type and provide a concise, one-sentence summary that is no longer than 20 words.
Your response must start with the document type (e.g., "A portfolio for...", "An invoice detailing...", "An article about..."). Do not use any other introductory phrases.

Text to analyze:
---
{text}
---

Concise Summary:"""

IMAGE_SUMMARY_PROMPT = """You are an expert image analyst. Your task is to provide a concise, one-sentence summary of the provided image that is no longer than 20 words. Do not use any introductory phrases."""

class LocalLLM:
    def __init__(self, temperature: float = 0.7):
        self.model = AI_MODEL
        self.server = AI_SERVER
        self.provider = 'lm-studio'
        self.temperature = temperature
        self.client = self._init_client()

    def _init_client(self):
        from openai import OpenAI
        return OpenAI(base_url=self.server, api_key="not-needed")
    
    def generate(self, messages: list, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            **kwargs
        )
        return response.choices[0].message.content.strip()
    
    def summarise_text(self, text: str, **kwargs):
        prompt = TEXT_SUMMARY_PROMPT.format(text=text)
        messages = [{'role': 'user', 'content': prompt}]
        return self.generate(messages, **kwargs)
    
    def summarise_image(self, image: Path | Image.Image, **kwargs) -> str:
        """Encodes an image to Base64 and sends it to a multimodal LLM for a concise description."""
        if isinstance(image, Path):
            try:
                with open(image, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            except IOError as e:
                return f"Error reading image file: {e}"

            mime_type, _ = mimetypes.guess_type(image)
            if not mime_type:
                mime_type = 'image/jpeg'

        elif isinstance(image, Image.Image):
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            mime_type = 'image/png'

        else:
            return "Error: Invalid type passed to summarise_image. Expected Path or PIL Image."
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": IMAGE_SUMMARY_PROMPT
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        return self.generate(messages, **kwargs)

if __name__ == "__main__":
    llm = LocalLLM()
    file = Path('Root/f32-xt.PNG')
    image_summary = llm.summarise_image(file)
    print(image_summary)