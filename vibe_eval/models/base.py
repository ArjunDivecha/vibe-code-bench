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

    V2: ALL models route through OpenRouter (single API key).

    Supported formats:
      - local, local:model-name → LMStudioModel (local only)
      - Everything else → OpenRouterModel

    Model ID formats for OpenRouter:
      - anthropic/claude-sonnet-4.5, anthropic/claude-opus-4.5
      - openai/gpt-4o, openai/o1
      - google/gemini-2.0-flash, google/gemini-2.5-pro
      - meta-llama/llama-3.1-8b-instruct
      - any/model-id@Provider (provider hint)
    """
    from .lmstudio import LMStudioModel
    from .openrouter import OpenRouterModel

    model_lower = model_id.lower()

    # Check for provider hint (model@Provider format)
    provider = None
    if "@" in model_id:
        model_id, provider = model_id.rsplit("@", 1)
        model_lower = model_id.lower()

    # Only local models bypass OpenRouter
    if model_lower.startswith("local"):
        # Support "local" or "local:model-name"
        if ":" in model_id:
            name = model_id.split(":", 1)[1]
            return LMStudioModel(model_id=name)
        return LMStudioModel()

    # V2: Everything else goes through OpenRouter
    # Auto-prefix common model names if no provider specified
    if "/" not in model_id:
        # Map shorthand names to OpenRouter format
        # Use actual OpenRouter model IDs (not dated versions)
        model_map = {
            "claude-opus-4.5": "anthropic/claude-opus-4.5",
            "claude-sonnet-4.5": "anthropic/claude-sonnet-4.5",
            "claude-sonnet-4": "anthropic/claude-sonnet-4",
            "claude-haiku-4.5": "anthropic/claude-haiku-4.5",
            "gpt-4o": "openai/gpt-4o",
            "gpt-4o-mini": "openai/gpt-4o-mini",
            "gpt-oss": "openai/gpt-oss-120b",
            "gpt-oss-120b": "openai/gpt-oss-120b",
            "o1": "openai/o1",
            "o3-mini": "openai/o3-mini",
            "gemini-2.0-flash": "google/gemini-2.0-flash-001",
            "gemini-2.5-pro": "google/gemini-2.5-pro-preview-06-05",
            "gemini-3-flash": "google/gemini-3-flash",
            "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct",
            "llama-3.1-70b": "meta-llama/llama-3.1-70b-instruct",
        }
        model_id = model_map.get(model_lower, model_id)

    return OpenRouterModel(model_id=model_id, provider=provider)
