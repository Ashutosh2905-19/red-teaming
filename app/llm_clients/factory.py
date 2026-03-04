# app/llm_clients/factory.py
from app.llm_clients.ollama_any import OllamaAnyClient
from app.llm_clients.openai_compat import OpenAICompatClient
from app.llm_clients.generic_rest import GenericRestClient
from app.llm_clients.universal_http import UniversalHttpClient


def make_target_client(provider: str, cfg: dict):
    provider = (provider or "").strip().lower()

    if provider == "ollama":
        return OllamaAnyClient(
            base_url=cfg["base_url"],
            model=cfg["model"],
            timeout_s=int(cfg.get("timeout_s", 600)),
        )

    if provider == "openai_compat":
        return OpenAICompatClient(
            base_url=cfg["base_url"],
            api_key=cfg["api_key"],
            model=cfg["model"],
            timeout_s=int(cfg.get("timeout_s", 180)),
        )

    # Your old generic client (works ONLY for {"prompt": "..."} -> {"text": "..."}). :contentReference[oaicite:1]{index=1}
    if provider == "generic_rest":
        return GenericRestClient(
            url=cfg["url"],
            timeout_s=int(cfg.get("timeout_s", 180)),
        )

    #The “any LLM” solution:
    if provider == "universal_http":
        return UniversalHttpClient(
            url=cfg["url"],
            method=cfg.get("method", "POST"),
            headers_json=cfg.get("headers_json", "{}"),
            body_template_json=cfg.get("body_template_json", ""),
            response_text_path=cfg.get("response_text_path", ""),
            timeout_s=int(cfg.get("timeout_s", 180)),
        )

    raise ValueError(f"Unknown provider: {provider}")