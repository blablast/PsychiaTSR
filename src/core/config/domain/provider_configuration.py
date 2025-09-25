"""Domain model for LLM provider configuration."""

from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum


class ProviderType(Enum):
    """Supported LLM provider types."""
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    AZURE = "azure"


@dataclass(frozen=True)
class ProviderCredentials:
    """Immutable credentials for LLM provider."""
    provider: ProviderType
    api_key: str

    def is_valid(self) -> bool:
        """Check if credentials are valid."""
        return bool(self.api_key and self.api_key.strip())


@dataclass(frozen=True)
class LLMParameters:
    """Immutable LLM generation parameters."""
    temperature: float = 0.7
    max_tokens: int = 150
    top_p: float = 0.9

    def __post_init__(self):
        """Validate parameters."""
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"Temperature must be between 0.0 and 2.0, got {self.temperature}")
        if self.max_tokens <= 0:
            raise ValueError(f"Max tokens must be positive, got {self.max_tokens}")
        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError(f"Top_p must be between 0.0 and 1.0, got {self.top_p}")


@dataclass(frozen=True)
class ProviderConfiguration:
    """Complete immutable configuration for an LLM provider."""
    provider: ProviderType
    model: str
    credentials: ProviderCredentials
    parameters: LLMParameters

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM provider APIs."""
        return {
            "api_key": self.credentials.api_key,
            "model": self.model,
            "temperature": self.parameters.temperature,
            "max_tokens": self.parameters.max_tokens,
            "top_p": self.parameters.top_p
        }


@dataclass(frozen=True)
class AgentProviderMapping:
    """Immutable mapping of agent to provider configuration."""
    agent_type: str
    provider_config: ProviderConfiguration

    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration dictionary for the agent."""
        config = self.provider_config.to_dict()
        config["agent_type"] = self.agent_type
        config["provider"] = self.provider_config.provider.value
        return config