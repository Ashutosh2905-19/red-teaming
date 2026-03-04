from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def generate(self, model_name: str, prompt: str) -> tuple[str,int,dict]:
        ...