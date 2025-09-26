"""LLM Provider Package for PsychiaTSR.

This package provides abstraction layer for Large Language Model providers,
supporting multiple AI providers with unified interfaces for the therapy system.

Providers:
    OpenAIProvider: OpenAI GPT models (GPT-4o, GPT-4o-mini, GPT-3.5-turbo)
    GeminiProvider: Google Gemini models (gemini-1.5-pro, gemini-1.5-flash)

Architecture:
    - LLMProvider: Abstract base class defining the provider interface
    - ModelDiscovery: Dynamic model discovery and validation
    - Streaming support for real-time therapy conversations
    - Structured output support for supervisor agent decisions

Usage:
    ```python
    from src.llm import OpenAIProvider, GeminiProvider

    # Create provider instance
    provider = OpenAIProvider(
        api_key="your-key",
        model="gpt-4o-mini",
        temperature=0.7
    )

    # Generate response
    response = provider.generate_response(
        prompt="How can I help you today?",
        max_tokens=200
    )
    ```

Integration:
    Providers integrate with the dual-agent system through dependency injection,
    supporting both therapist conversation and supervisor stage evaluation.
"""

from .base import LLMProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .model_discovery import ModelDiscovery

__all__ = ["LLMProvider", "OpenAIProvider", "GeminiProvider", "ModelDiscovery"]
