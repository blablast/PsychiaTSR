"""Credentials service."""

from typing import Optional, Dict
from ..interfaces import ICredentialsProvider
from ..domain import ProviderType, ProviderCredentials
from ..loaders.environment_loader import EnvironmentLoader


class CredentialsService(ICredentialsProvider):
    """Service for managing LLM provider credentials."""

    def __init__(self, environment_loader: EnvironmentLoader):
        """Initialize with environment loader."""
        self._env_loader = environment_loader

    def get_credentials(self, provider: ProviderType) -> Optional[ProviderCredentials]:
        """Get credentials for specified provider."""
        api_key = self._env_loader.get_api_key(provider.value)
        return ProviderCredentials(provider=provider, api_key=api_key) if api_key else None

    def has_credentials(self, provider: ProviderType) -> bool:
        """Check if credentials exist for provider."""
        return self._env_loader.has_api_key(provider.value)

    def get_all_available_credentials(self) -> Dict[ProviderType, ProviderCredentials]:
        """Get all available credentials."""
        credentials = {}

        for provider in ProviderType:
            creds = self.get_credentials(provider)
            if creds and creds.is_valid():
                credentials[provider] = creds

        return credentials