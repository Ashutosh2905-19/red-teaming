import time, requests

class OllamaBYOClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def generate(self, model_name: str, prompt: str) -> tuple[str, int, dict]:
        url = f"{self.base_url}/api/generate"
        payload = {"model": model_name, "prompt": prompt, "stream": False}
        t0 = time.time()
        r = requests.post(url, json=payload, timeout=600)
        r.raise_for_status()
        js = r.json()
        latency_ms = int((time.time() - t0) * 1000)
        return js.get("response", ""), latency_ms, js