"""Anthropic Claude model adapter with extended thinking support."""

import os
from typing import Optional

import anthropic

from .base import BaseModel, Message, ModelResponse


# Model ID mappings for convenience
CLAUDE_MODELS = {
    "claude-sonnet-4": "claude-sonnet-4-20250514",
    "claude-opus-4": "claude-opus-4-20250514",
    "claude-sonnet-4.5": "claude-sonnet-4-5-20250929",
    "claude-opus-4.5": "claude-opus-4-5-20251101",
    "claude-haiku-4.5": "claude-haiku-4-5-20251001",
    "claude-sonnet-3.5": "claude-3-5-sonnet-20241022",
}

# Default parameters optimized for each model
MODEL_DEFAULTS = {
    # Opus 4.5: Enable extended thinking with generous budget
    "claude-opus-4.5": {
        "thinking_budget": 16000,  # High budget for complex reasoning
        "temperature": None,  # Cannot use temp with thinking
    },
    # Opus 4: Also benefits from extended thinking
    "claude-opus-4": {
        "thinking_budget": 12000,
        "temperature": None,
    },
    # Sonnet 4.5: Temperature 0.7 optimal for coding creativity
    "claude-sonnet-4.5": {
        "thinking_budget": 8000,  # Medium budget
        "temperature": None,  # Cannot use temp with thinking
    },
    # Sonnet 4: Good balance
    "claude-sonnet-4": {
        "thinking_budget": 0,  # No thinking for faster responses
        "temperature": 0.7,
    },
    # Haiku: Fast, no thinking
    "claude-haiku-4.5": {
        "thinking_budget": 0,
        "temperature": 0.5,
    },
}


class ClaudeModel(BaseModel):
    """Anthropic Claude model adapter with extended thinking support."""
    
    def __init__(
        self, 
        model_id: str = "claude-sonnet-4",
        max_tokens: int = 20480,
        temperature: Optional[float] = None,
        thinking_budget: Optional[int] = None
    ):
        """
        Initialize Claude adapter.
        
        Args:
            model_id: Model identifier (e.g., "claude-sonnet-4" or full ID)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (None = use model default)
            thinking_budget: Tokens for extended thinking (None = use model default)
        """
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        # Map short names to full IDs
        self.model_id = CLAUDE_MODELS.get(model_id, model_id)
        self.max_tokens = max_tokens
        self._name = model_id  # Store original name for display
        
        # Get model-specific defaults
        defaults = MODEL_DEFAULTS.get(model_id, {})
        
        # Use provided values or fall back to model defaults
        self.temperature = temperature if temperature is not None else defaults.get("temperature")
        self.thinking_budget = thinking_budget if thinking_budget is not None else defaults.get("thinking_budget", 0)
    
    def complete(self, messages: list[Message]) -> ModelResponse:
        """Send messages and get completion from Claude."""
        
        # Separate system message from conversation
        system_content = None
        conversation = []
        
        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
            else:
                conversation.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Build request kwargs
        kwargs = {
            "model": self.model_id,
            "max_tokens": self.max_tokens,
            "messages": conversation,
        }
        
        if system_content:
            kwargs["system"] = system_content
        
        # Extended thinking mode - mutually exclusive with temperature
        if self.thinking_budget and self.thinking_budget > 0:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.thinking_budget
            }
            # Note: temperature cannot be used with extended thinking
        elif self.temperature is not None:
            kwargs["temperature"] = self.temperature
        
        response = self.client.messages.create(**kwargs)
        
        # Extract text content (may have thinking blocks + text)
        text_content = ""
        for block in response.content:
            if hasattr(block, 'text'):
                text_content += block.text
        
        return ModelResponse(
            content=text_content,
            model=self.model_id,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        )
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def provider(self) -> str:
        return "anthropic"
