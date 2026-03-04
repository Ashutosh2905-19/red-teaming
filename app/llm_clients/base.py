# app/llm_clients/base.py
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any

class TargetLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> Tuple[str, int, Dict[str, Any]]:
        ...

# Backward-compatible alias (if any file uses BaseLLMClient)
BaseLLMClient = TargetLLMClient