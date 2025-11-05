from pathlib import Path
from config import AI_MODEL, AI_SERVER
from keybert import KeyBERT

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
    
    def generate(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=self.temperature,
            **kwargs
        )
        return response.choices[0].message.content.strip()
    
    def summarise_text(self, text: str, **kwargs):
        prompt = f"Summarise the following text:\n\n{text}"
        keywords = self.get_keywords(text)

        return self.generate(prompt, **kwargs), keywords
    
    def summarise_image(self, image_path: str, **kwargs) -> str:
        prompt = f"Describe the contents of the image at: {image_path}"
        return self.generate(prompt, **kwargs)
    
    def get_keywords(self, text: str, top_n: int = 5):
        if not text.strip():
            return []
        
        kw_model = KeyBERT(model="all-MiniLM-L6-v2")
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=top_n
        )
        return [kw for kw, _ in keywords]