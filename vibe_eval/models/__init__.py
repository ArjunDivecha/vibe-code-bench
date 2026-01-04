"""Model adapters package.

V2: All models route through OpenRouter (except local LMStudio).
"""

from .base import BaseModel, get_model, Message, ModelResponse
from .openrouter import OpenRouterModel
from .lmstudio import LMStudioModel

__all__ = ["BaseModel", "get_model", "Message", "ModelResponse", "OpenRouterModel", "LMStudioModel"]
