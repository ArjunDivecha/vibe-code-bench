"""OpenRouter model adapter for accessing various LLMs."""

import os
from typing import Optional

import openai

from .base import BaseModel, Message, ModelResponse


class OpenRouterModel(BaseModel):
    """OpenRouter model adapter using OpenAI-compatible API."""
    
    def __init__(
        self, 
        model_id: str = "meta-llama/llama-3.1-8b-instruct",
        max_tokens: int = 20480,
        temperature: Optional[float] = 0.7,
        provider: Optional[str] = None  # e.g., "Cerebras" for fast inference
    ):
        """
        Initialize OpenRouter adapter.
        
        Args:
            model_id: Full OpenRouter model ID (e.g., "meta-llama/llama-3.1-8b-instruct")
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            provider: Preferred provider (e.g., "Cerebras", "Together", etc.)
        """
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._preferred_provider = provider  # Renamed to avoid conflict with property
    
    def complete(self, messages: list[Message]) -> ModelResponse:
        """Send messages and get completion from OpenRouter."""
        
        # Convert to OpenAI format
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Build request kwargs
        kwargs = {
            "model": self.model_id,
            "messages": formatted_messages,
            "max_tokens": self.max_tokens,
        }
        
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        
        # Add provider preference via extra_body
        if self._preferred_provider:
            kwargs["extra_body"] = {
                "provider": {
                    "order": [self._preferred_provider],
                    "allow_fallbacks": True
                }
            }
        
        response = self.client.chat.completions.create(**kwargs)
        
        # Handle usage data
        usage = None
        if response.usage:
            usage = {
                "input_tokens": response.usage.prompt_tokens or 0,
                "output_tokens": response.usage.completion_tokens or 0,
            }
        
        return ModelResponse(
            content=response.choices[0].message.content,
            model=self.model_id,
            usage=usage
        )
    
    @property
    def name(self) -> str:
        # Return short name for display
        return self.model_id.split("/")[-1] if "/" in self.model_id else self.model_id
    
    @property
    def provider(self) -> str:
        return "openrouter"
