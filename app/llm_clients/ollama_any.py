# app/llm_clients/ollama_any.py
import time
import requests
from typing import Tuple, Dict, Any
from app.llm_clients.base import TargetLLMClient

class OllamaAnyClient(TargetLLMClient):
    def __init__(self, base_url: str, model: str, timeout_s: int = 600):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = int(timeout_s)

    def generate(self, prompt: str, **kwargs) -> Tuple[str, int, Dict[str, Any]]:
        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": False}

        t0 = time.time()
        r = requests.post(url, json=payload, timeout=self.timeout_s)
        latency_ms = int((time.time() - t0) * 1000)

        r.raise_for_status()
        js = r.json()

        return js.get("response", ""), latency_ms, js