"""OpenAI GPT model adapter."""

import os
from typing import Optional

import openai

from .base import BaseModel, Message, ModelResponse


class OpenAIModel(BaseModel):
    """OpenAI GPT model adapter."""
    
    def __init__(
        self, 
        model_id: str = "gpt-4o",
        max_tokens: int = 8192,
        temperature: Optional[float] = None
    ):
        """
        Initialize OpenAI adapter.
        
        Args:
            model_id: Model identifier (e.g., "gpt-4o", "o1", "o3-mini")
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (None = default)
        """
        self.client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY")
        )
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    def complete(self, messages: list[Message]) -> ModelResponse:
        """Send messages and get completion from OpenAI."""
        
        # Convert to OpenAI format
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Build request kwargs
        kwargs = {
            "model": self.model_id,
            "messages": formatted_messages,
        }
        
        # o1/o3 models don't support max_tokens the same way
        if not self.model_id.startswith(("o1", "o3")):
            kwargs["max_tokens"] = self.max_tokens
            if self.temperature is not None:
                kwargs["temperature"] = self.temperature
        
        response = self.client.chat.completions.create(**kwargs)
        
        return ModelResponse(
            content=response.choices[0].message.content,
            model=self.model_id,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            } if response.usage else None
        )
    
    @property
    def name(self) -> str:
        return self.model_id
    
    @property
    def provider(self) -> str:
        return "openai"
