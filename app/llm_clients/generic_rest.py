# app/llm_clients/generic_rest.py
import time
import requests
from typing import Tuple, Dict, Any
from app.llm_clients.base import TargetLLMClient

class GenericRestClient(TargetLLMClient):
    """
    For custom LLM services that accept:
      POST <url> with JSON {"prompt": "..."} and return {"text": "..."}
    """
    def __init__(self, url: str, timeout_s: int = 180):
        self.url = url
        self.timeout_s = int(timeout_s)

    def generate(self, prompt: str, **kwargs) -> Tuple[str, int, Dict[str, Any]]:
        payload = {"prompt": prompt}

        t0 = time.time()
        r = requests.post(self.url, json=payload, timeout=self.timeout_s)
        latency_ms = int((time.time() - t0) * 1000)

        r.raise_for_status()
        js = r.json()
        text = js.get("text", "")
        return text, latency_ms, js