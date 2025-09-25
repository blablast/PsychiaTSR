"""Environment variable configuration loader."""

import os
from typing import Dict


class EnvironmentLoader:
    """Handles environment variable configuration."""

    def __init__(self):
        """Initialize environment configuration."""
        self._api_keys = self._load_api_keys()

    @staticmethod
    def _load_api_keys() -> Dict[str, str]:
        """Load API keys from environment variables."""
        return {
            "openai": os.getenv("OPENAI_API_KEY", ""),
            "google": os.getenv("GOOGLE_API_KEY", ""),
            "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
            "azure": os.getenv("AZURE_API_KEY", "")
        }

    def get_api_key(self, provider: str) -> str:
        """Get API key for specified provider."""
        provider_key = provider.lower()
        if provider_key == "gemini":
            provider_key = "google"

        return self._api_keys.get(provider_key, "")

    def get_all_api_keys(self) -> Dict[str, str]:
        """Get all available API keys."""
        return self._api_keys.copy()

    def has_api_key(self, provider: str) -> bool:
        """Check if API key exists for provider."""
        return bool(self.get_api_key(provider))

    def get_configured_providers(self) -> list:
        """Get list of providers with configured API keys."""
        return [provider for provider, key in self._api_keys.items() if key]

    def refresh(self) -> None:
        """Refresh API keys from environment."""
        self._api_keys = self._load_api_keys()