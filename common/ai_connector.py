"""
AI Connector module for handling different AI providers (Claude, GPT)
"""

import os
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
import anthropic
import openai
from dotenv import load_dotenv

load_dotenv()


class AIProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class AIConnector(ABC):
    """Abstract base class for AI connectors"""

    @abstractmethod
    async def generate_response(self, prompt: str, system_message: str = None) -> str:
        """Generate AI response for given prompt"""
        pass

    @abstractmethod
    async def generate_structured_response(self, prompt: str, system_message: str = None) -> Dict[str, Any]:
        """Generate structured AI response"""
        pass


class AnthropicConnector(AIConnector):
    """Claude/Anthropic AI connector"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"

    async def generate_response(self, prompt: str, system_message: str = None) -> str:
        """Generate response using Claude"""
        try:
            messages = [{"role": "user", "content": prompt}]

            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 8000,
                "temperature": 0.3
            }

            if system_message:
                kwargs["system"] = system_message

            response = self.client.messages.create(**kwargs)
            return response.content[0].text

        except Exception as e:
            raise Exception(f"Error generating Anthropic response: {str(e)}")

    async def generate_structured_response(self, prompt: str, system_message: str = None) -> Dict[str, Any]:
        """Generate structured response with JSON parsing"""
        response_text = await self.generate_response(prompt, system_message)

        # Try to extract JSON from response
        try:
            import json
            # Find JSON block in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return {"response": response_text}

        except json.JSONDecodeError:
            return {"response": response_text}


class OpenAIConnector(AIConnector):
    """OpenAI GPT connector (stub for future implementation)"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        # Initialize client but don't use it yet
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = "gpt-4"

    async def generate_response(self, prompt: str, system_message: str = None) -> str:
        """Stub implementation - will be implemented later"""
        return "OpenAI connector not implemented yet. Using placeholder response."

    async def generate_structured_response(self, prompt: str, system_message: str = None) -> Dict[str, Any]:
        """Stub implementation"""
        return {"response": "OpenAI connector not implemented yet"}


class AIConnectorFactory:
    """Factory for creating AI connectors"""

    @staticmethod
    def create_connector(provider: AIProvider = None) -> AIConnector:
        """Create AI connector based on provider"""
        if provider is None:
            provider_str = os.getenv("DEFAULT_AI_PROVIDER", "anthropic")
            provider = AIProvider(provider_str)

        if provider == AIProvider.ANTHROPIC:
            return AnthropicConnector()
        elif provider == AIProvider.OPENAI:
            return OpenAIConnector()
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")


# Convenience function for quick access
async def get_ai_response(prompt: str, system_message: str = None, provider: AIProvider = None) -> str:
    """Quick function to get AI response"""
    connector = AIConnectorFactory.create_connector(provider)
    return await connector.generate_response(prompt, system_message)