import json
import time
import requests
from typing import Tuple, Dict, Any, Optional

from app.llm_clients.base import TargetLLMClient


def _json_escape(s: str) -> str:
    """Escape for embedding inside a JSON string value (without adding quotes)."""
    return (
        s.replace("\\", "\\\\")
         .replace('"', '\\"')
         .replace("\n", "\\n")
         .replace("\r", "\\r")
         .replace("\t", "\\t")
    )


def _render_template_json(template_str: str, values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Render a JSON template containing placeholders like {{prompt}}, {{model}}, {{max_tokens}}.
    Assumption (recommended): string placeholders live inside quotes in the template:
       "content": "{{prompt}}"
    and numeric placeholders are unquoted:
       "max_tokens": {{max_tokens}}
    """
    s = template_str

    # String placeholders (replace inside quotes)
    for k in ["prompt", "model", "system", "user"]:
        if f"{{{{{k}}}}}" in s:
            s = s.replace(f"{{{{{k}}}}}", _json_escape(str(values.get(k, ""))))

    # Numeric / bool placeholders (unquoted)
    for k in ["max_tokens", "temperature", "top_p", "seed"]:
        if f"{{{{{k}}}}}" in s:
            v = values.get(k)
            if v is None:
                # Remove placeholder safely by setting a sane default
                v = 0 if k in ["max_tokens", "seed"] else 0.0
            s = s.replace(f"{{{{{k}}}}}", str(v))

    # Optional: any other placeholders
    for k, v in values.items():
        ph = f"{{{{{k}}}}}"
        if ph in s:
            # default to string escaping
            s = s.replace(ph, _json_escape(str(v)))

    try:
        return json.loads(s)
    except Exception as e:
        raise ValueError(
            "Universal HTTP body_template is not valid JSON after rendering. "
            "Fix the template JSON and placeholders.\n\n"
            f"Error: {e}\n\nRendered:\n{s[:2000]}"
        )


def _extract_dotpath(data: Any, path: str) -> Any:
    """
    Extract values using dotpath like: choices.0.message.content
    Works for dict keys and list indexes.
    """
    cur = data
    if not path:
        return cur

    for part in path.split("."):
        if isinstance(cur, list):
            idx = int(part)  # raises if not integer
            cur = cur[idx]
        elif isinstance(cur, dict):
            if part not in cur:
                raise KeyError(f"Key '{part}' not found while extracting '{path}'")
            cur = cur[part]
        else:
            raise TypeError(f"Cannot traverse '{part}' on non-container type while extracting '{path}'")
    return cur


class UniversalHttpClient(TargetLLMClient):
    """
    Universal HTTP LLM Client:
      - user provides URL, method, headers JSON
      - user provides body_template JSON (with placeholders)
      - user provides response_text_path (dotpath) to extract text
    """

    def __init__(
        self,
        url: str,
        method: str = "POST",
        headers_json: Optional[str] = None,
        body_template_json: Optional[str] = None,
        response_text_path: str = "",
        timeout_s: int = 180,
    ):
        self.url = (url or "").strip()
        self.method = (method or "POST").strip().upper()
        self.timeout_s = int(timeout_s)

        self.headers = {}
        if headers_json:
            self.headers = json.loads(headers_json)

        # Must be JSON string
        if not body_template_json:
            raise ValueError("body_template_json is required for UniversalHttpClient")
        self.body_template_json = body_template_json

        # dotpath (or empty = whole response)
        self.response_text_path = (response_text_path or "").strip()

    def generate(self, prompt: str, **kwargs) -> Tuple[str, int, Dict[str, Any]]:
        # Defaults to keep tokens low unless user explicitly raises them
        model = kwargs.get("model", "")
        system = kwargs.get("system", "You are a helpful assistant.")
        max_tokens = int(kwargs.get("max_tokens", 300))
        temperature = float(kwargs.get("temperature", 0.2))

        values = {
            "prompt": prompt,
            "model": model,
            "system": system,
            "user": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        payload = _render_template_json(self.body_template_json, values)

        t0 = time.time()
        if self.method == "POST":
            r = requests.post(self.url, headers=self.headers, json=payload, timeout=self.timeout_s)
        elif self.method == "PUT":
            r = requests.put(self.url, headers=self.headers, json=payload, timeout=self.timeout_s)
        else:
            raise ValueError(f"Unsupported method: {self.method}")

        latency_ms = int((time.time() - t0) * 1000)
        r.raise_for_status()

        # Try JSON; fallback to text
        try:
            js = r.json()
        except Exception:
            txt = r.text or ""
            meta = {
                "provider": "universal_http",
                "url": self.url,
                "status_code": r.status_code,
                "note": "Non-JSON response",
            }
            return txt, latency_ms, meta

        try:
            extracted = _extract_dotpath(js, self.response_text_path) if self.response_text_path else js
        except Exception as e:
            extracted = ""
            meta = {
                "provider": "universal_http",
                "url": self.url,
                "status_code": r.status_code,
                "error": f"Failed to extract response_text_path='{self.response_text_path}': {e}",
                "raw_json": js,
            }
            return extracted, latency_ms, meta

        # normalize extracted to text
        if isinstance(extracted, (dict, list)):
            text = json.dumps(extracted, ensure_ascii=False)
        else:
            text = str(extracted)

        meta = {
            "provider": "universal_http",
            "url": self.url,
            "status_code": r.status_code,
        }
        return text, latency_ms, meta