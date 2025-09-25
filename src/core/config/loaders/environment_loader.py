"""Environment variable configuration loader."""

import os
from typing import Dict

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


class EnvironmentLoader:
    """Handles environment variable configuration."""

    def __init__(self):
        """Initialize environment configuration."""
        self._api_keys = self._load_api_keys()

    @staticmethod
    def _load_api_keys() -> Dict[str, str]:
        """Load API keys from environment variables or Streamlit secrets."""
        def get_key(key_name: str) -> str:
            """Get API key from environment variables or Streamlit secrets."""
            # First try environment variables
            env_value = os.getenv(key_name, "")
            if env_value:
                return env_value

            # If running in Streamlit Cloud, try st.secrets
            if STREAMLIT_AVAILABLE:
                try:
                    # Check if we're actually running in Streamlit context
                    if hasattr(st, 'secrets') and hasattr(st.secrets, '_file_path'):
                        return st.secrets.get(key_name, "")
                except (AttributeError, KeyError, Exception):
                    # Silently fail if secrets are not available
                    pass

            return ""

        return {
            "openai": get_key("OPENAI_API_KEY"),
            "google": get_key("GOOGLE_API_KEY"),
            "anthropic": get_key("ANTHROPIC_API_KEY"),
            "azure": get_key("AZURE_API_KEY"),
            "elevenlabs": get_key("ELEVENLABS_API_KEY")
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