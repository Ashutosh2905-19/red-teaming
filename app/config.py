import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

def _parse_models() -> list[str]:
    raw = os.getenv("OLLAMA_MODELS", "llama3:latest")
    return [m.strip() for m in raw.split(",") if m.strip()]

@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_models: list[str] = field(default_factory=_parse_models)

    db_path: str = os.getenv("DB_PATH", "outputs/redteam_finance.sqlite3")

    tau_safe: float = float(os.getenv("TAU_SAFE", "0.30"))
    tau_review: float = float(os.getenv("TAU_REVIEW", "0.55"))

SETTINGS = Settings()