"""Provider discovery service."""

from typing import List
from ..interfaces import IProviderDiscovery, ICredentialsProvider
from ..domain import ProviderType


class ProviderDiscovery(IProviderDiscovery):
    """Service for discovering available providers."""

    def __init__(self, credentials_provider: ICredentialsProvider):
        """Initialize with credentials provider."""
        self._credentials_provider = credentials_provider

    def get_available_providers(self) -> List[ProviderType]:
        """Get list of available providers with valid credentials."""
        available = []

        for provider in ProviderType:
            if self._credentials_provider.has_credentials(provider):
                available.append(provider)

        return available

    def get_supported_providers(self) -> List[ProviderType]:
        """Get list of all supported provider types."""
        return list(ProviderType)

    def is_provider_available(self, provider: ProviderType) -> bool:
        """Check if specific provider is available."""
        return self._credentials_provider.has_credentials(provider)

    def get_unavailable_providers(self) -> List[ProviderType]:
        """Get list of providers without valid credentials."""
        unavailable = []

        for provider in ProviderType:
            if not self._credentials_provider.has_credentials(provider):
                unavailable.append(provider)

        return unavailable

    def get_provider_status(self) -> dict:
        """Get comprehensive status of all providers."""
        available = self.get_available_providers()
        unavailable = self.get_unavailable_providers()

        return {
            "total_supported": len(ProviderType),
            "available_count": len(available),
            "unavailable_count": len(unavailable),
            "available_providers": [p.value for p in available],
            "unavailable_providers": [p.value for p in unavailable],
            "availability_percentage": (len(available) / len(ProviderType)) * 100
        }