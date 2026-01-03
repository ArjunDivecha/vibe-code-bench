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
      - any/model-id → OpenRouterModel
      - any/model-id@Provider → OpenRouterModel with provider hint
    """
    from .claude import ClaudeModel
    from .openai import OpenAIModel
    from .gemini import GeminiModel
    from .lmstudio import LMStudioModel
    from .openrouter import OpenRouterModel
    
    model_lower = model_id.lower()
    
    # Check for provider hint (model@Provider format)
    provider = None
    if "@" in model_id:
        model_id, provider = model_id.rsplit("@", 1)
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
    else:
        # Default to OpenRouter for any other model ID
        # This handles: qwen/qwen3, anthropic/claude-haiku, google/gemini-*, etc.
        return OpenRouterModel(model_id=model_id, provider=provider)
