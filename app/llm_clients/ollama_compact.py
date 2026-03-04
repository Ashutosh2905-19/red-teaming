# app/llm_clients/openai_compat.py
import time
import requests
from typing import Tuple, Dict, Any

from app.llm_clients.base import TargetLLMClient


class OpenAICompatClient(TargetLLMClient):
    """
    OpenAI-compatible Chat Completions client.
    Expects:
      base_url: e.g. https://api.openai.com
      api_key:  sk-...
      model:    e.g. gpt-4o-mini
      timeout_s: int
    """

    def __init__(self, base_url: str, api_key: str, model: str, timeout_s: int = 180):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_s = int(timeout_s)

        # Most OpenAI-compatible servers expose /v1/chat/completions
        self.url = f"{self.base_url}/v1/chat/completions"

    def generate(self, prompt: str, **kwargs) -> Tuple[str, int, Dict[str, Any]]:
        """
        Returns: (text, latency_ms, meta)
        """
        # Keep token usage low by default:
        max_tokens = int(kwargs.get("max_tokens", 300))
        temperature = float(kwargs.get("temperature", 0.2))

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        t0 = time.time()
        r = requests.post(self.url, headers=headers, json=payload, timeout=self.timeout_s)
        latency_ms = int((time.time() - t0) * 1000)

        r.raise_for_status()
        data = r.json()

        text = ""
        try:
            text = data["choices"][0]["message"]["content"]
        except Exception:
            text = str(data)

        meta = {
            "provider": "openai_compat",
            "endpoint": self.url,
            "status_code": r.status_code,
            "usage": data.get("usage", {}),
            "model": data.get("model", self.model),
        }
        return text, latency_ms, meta