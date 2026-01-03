"""Abstract base class for model adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Message:
    """A message in the conversation."""
    role: str  # "system", "user", or "assistant"
    content: str


@dataclass 
class ModelResponse:
    """Response from a model completion."""
    content: str
    model: str
    usage: Optional[dict] = None


class BaseModel(ABC):
    """Abstract base class for LLM model adapters."""
    
    @abstractmethod
    def complete(self, messages: list[Message]) -> ModelResponse:
        """
        Send messages and get a completion.
        
        Args:
            messages: List of Message objects representing the conversation
            
        Returns:
            ModelResponse with the model's reply
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Model identifier for results."""
        pass
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """Provider name (anthropic, openai, google)."""
        pass


def get_model(model_id: str) -> BaseModel:
    """
    Factory function to get a model adapter by ID.
    
    Supported formats:
      - claude-sonnet-4, claude-opus-4 → ClaudeModel
      - gpt-4o, gpt-4o-mini, o1, o3-mini → OpenAIModel  
      - gemini-2.0-flash, gemini-2.5-pro → GeminiModel
      - local, local:model-name → LMStudioModel
      - llama-3.1-8b, openrouter:model/name → OpenRouterModel
    """
    from .claude import ClaudeModel
    from .openai import OpenAIModel
    from .gemini import GeminiModel
    from .lmstudio import LMStudioModel
    from .openrouter import OpenRouterModel
    
    model_lower = model_id.lower()
    
    if model_lower.startswith("claude"):
        return ClaudeModel(model_id)
    elif model_lower.startswith(("gpt", "o1", "o3")):
        return OpenAIModel(model_id)
    elif model_lower.startswith("gemini"):
        return GeminiModel(model_id)
    elif model_lower.startswith("local"):
        # Support "local" or "local:model-name"
        if ":" in model_id:
            name = model_id.split(":", 1)[1]
            return LMStudioModel(model_id=name)
        return LMStudioModel()
    elif model_lower.startswith(("llama", "openrouter", "meta-llama", "cerebras")):
        # OpenRouter models - use full model ID or map short names
        if model_lower.startswith("openrouter:"):
            full_id = model_id.split(":", 1)[1]
        elif model_lower.startswith("llama-3.1-8b"):
            full_id = "meta-llama/llama-3.1-8b-instruct"
        elif model_lower.startswith("llama-3.1-70b"):
            full_id = "meta-llama/llama-3.1-70b-instruct"
        elif model_lower.startswith("cerebras"):
            full_id = "meta-llama/llama-3.1-8b-instruct"
        else:
            full_id = model_id
        return OpenRouterModel(model_id=full_id, provider="Cerebras")
    else:
        raise ValueError(f"Unknown model: {model_id}. Supported prefixes: claude, gpt, o1, o3, gemini, local, llama, openrouter")
