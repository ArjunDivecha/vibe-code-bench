"""LM Studio local model adapter (OpenAI-compatible)."""

import os
from typing import Optional

import openai

from .base import BaseModel, Message, ModelResponse


class LMStudioModel(BaseModel):
    """LM Studio local model adapter using OpenAI-compatible API."""
    
    def __init__(
        self, 
        model_id: str = "local",
        max_tokens: int = 8192,
        temperature: Optional[float] = 0.7,
        base_url: Optional[str] = None
    ):
        """
        Initialize LM Studio adapter.
        
        Args:
            model_id: Model name (for display purposes)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            base_url: LM Studio server URL (default: http://localhost:1234/v1)
        """
        self.base_url = base_url or os.environ.get(
            "LMSTUDIO_BASE_URL", 
            "http://localhost:1234/v1"
        )
        
        self.client = openai.OpenAI(
            api_key="lm-studio",  # LM Studio doesn't need real API key
            base_url=self.base_url
        )
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    def complete(self, messages: list[Message]) -> ModelResponse:
        """Send messages and get completion from LM Studio."""
        
        # Convert to OpenAI format
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        response = self.client.chat.completions.create(
            model=self.model_id,  # LM Studio uses loaded model
            messages=formatted_messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        
        # Handle potential missing usage data from local models
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
        return f"local:{self.model_id}"
    
    @property
    def provider(self) -> str:
        return "lmstudio"
