"""Google Gemini model adapter."""

import os
from typing import Optional

import google.generativeai as genai

from .base import BaseModel, Message, ModelResponse


# Model ID mappings for convenience
GEMINI_MODELS = {
    "gemini-2.5-pro": "gemini-2.5-pro-preview-06-05",
    "gemini-2.0-flash": "gemini-2.0-flash",
    "gemini-1.5-pro": "gemini-1.5-pro",
}


class GeminiModel(BaseModel):
    """Google Gemini model adapter."""
    
    def __init__(
        self, 
        model_id: str = "gemini-2.5-pro",
        max_tokens: int = 8192,
        temperature: Optional[float] = None
    ):
        """
        Initialize Gemini adapter.
        
        Args:
            model_id: Model identifier (e.g., "gemini-2.5-pro")
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (None = default)
        """
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        
        # Map short names to full IDs
        resolved_id = GEMINI_MODELS.get(model_id, model_id)
        self.model = genai.GenerativeModel(resolved_id)
        self.model_id = resolved_id
        self._name = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    def complete(self, messages: list[Message]) -> ModelResponse:
        """Send messages and get completion from Gemini."""
        
        # Build conversation history for Gemini
        # Gemini uses a different format - combine into a chat
        history = []
        system_instruction = None
        current_content = None
        
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                history.append({
                    "role": "user",
                    "parts": [msg.content]
                })
            elif msg.role == "assistant":
                history.append({
                    "role": "model",
                    "parts": [msg.content]
                })
        
        # Create chat with history (excluding last user message)
        if history and history[-1]["role"] == "user":
            current_content = history[-1]["parts"][0]
            history = history[:-1]
        
        # Build generation config
        generation_config = {
            "max_output_tokens": self.max_tokens,
        }
        if self.temperature is not None:
            generation_config["temperature"] = self.temperature
        
        # Create model with system instruction if present
        if system_instruction:
            model = genai.GenerativeModel(
                self.model_id,
                system_instruction=system_instruction
            )
        else:
            model = self.model
        
        chat = model.start_chat(history=history)
        response = chat.send_message(
            current_content or "",
            generation_config=generation_config
        )
        
        return ModelResponse(
            content=response.text,
            model=self.model_id,
            usage=None  # Gemini usage tracking is different
        )
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def provider(self) -> str:
        return "google"
