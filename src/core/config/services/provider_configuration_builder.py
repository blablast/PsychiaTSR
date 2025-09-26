"""Provider configuration builder."""

from ..interfaces import IProviderConfigurationBuilder
from ..domain import (
    ProviderType,
    ProviderCredentials,
    LLMParameters,
    ProviderConfiguration,
    AgentProviderMapping,
)
from ..loaders.agent_loader import AgentLoader


class ProviderConfigurationBuilder(IProviderConfigurationBuilder):
    """Service for building provider configurations."""

    def __init__(self, agent_loader: AgentLoader):
        """Initialize with agent loader."""
        self._agent_loader = agent_loader

    def build_configuration(
        self, provider: ProviderType, model: str, credentials: ProviderCredentials
    ) -> ProviderConfiguration:
        """Build complete provider configuration."""
        parameters = LLMParameters()

        return ProviderConfiguration(
            provider=provider, model=model, credentials=credentials, parameters=parameters
        )

    def build_agent_configuration(self, agent_type: str) -> ProviderConfiguration:
        """Build configuration for specific agent type."""
        provider_name = self._agent_loader.get_agent_provider(agent_type)
        model = self._agent_loader.get_agent_model(agent_type)
        agent_params = self._agent_loader.get_agent_parameters(agent_type)

        provider = ProviderType(provider_name)
        parameters = LLMParameters(
            temperature=agent_params.get("temperature", 0.7),
            max_tokens=agent_params.get("max_tokens", 150),
            top_p=agent_params.get("top_p", 0.9),
        )

        # Create placeholder credentials that will be replaced by orchestrator
        placeholder_credentials = ProviderCredentials(provider=provider, api_key="")

        return ProviderConfiguration(
            provider=provider,
            model=model,
            credentials=placeholder_credentials,
            parameters=parameters,
        )

    def build_agent_mapping(
        self, agent_type: str, provider_config: ProviderConfiguration
    ) -> AgentProviderMapping:
        """Build agent to provider mapping."""
        return AgentProviderMapping(agent_type=agent_type, provider_config=provider_config)

    def build_configuration_with_agent_params(
        self, provider: ProviderType, model: str, credentials: ProviderCredentials, agent_type: str
    ) -> ProviderConfiguration:
        """Build configuration with agent-specific parameters."""
        agent_params = self._agent_loader.get_agent_parameters(agent_type)

        parameters = LLMParameters(
            temperature=agent_params.get("temperature", 0.7),
            max_tokens=agent_params.get("max_tokens", 150),
            top_p=agent_params.get("top_p", 0.9),
        )

        return ProviderConfiguration(
            provider=provider, model=model, credentials=credentials, parameters=parameters
        )
