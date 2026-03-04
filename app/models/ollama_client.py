import time
import requests
from app.config import SETTINGS
from .base import LLMClient

class OllamaClient(LLMClient):
    def __init__(self, base_url: str | None = None, timeout_s: int = 600):
        self.base_url = base_url or SETTINGS.ollama_base_url
        self.timeout_s = timeout_s

    def generate(self, model_name: str, prompt: str) -> tuple[str, int, dict]:
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            # IMPORTANT: prevent very long generations
            "options": {
                "num_predict": 256,   # max tokens to generate (tune 128–512)
                "temperature": 0.2
            }
        }

        t0 = time.time()
        r = requests.post(url, json=payload, timeout=self.timeout_s)
        t1 = time.time()
        r.raise_for_status()
        data = r.json()

        return data.get("response", "").strip(), int((t1 - t0) * 1000), {
            "eval_count": data.get("eval_count"),
            "prompt_eval_count": data.get("prompt_eval_count"),
        }