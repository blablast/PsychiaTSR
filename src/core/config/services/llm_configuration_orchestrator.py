"""LLM Configuration Orchestrator following SOLID principles."""

from typing import Optional, Dict, Any
from ..interfaces import (
    ICredentialsProvider,
    IProviderConfigurationBuilder,
    IProviderValidator,
    IProviderDiscovery
)
from ..domain import ProviderConfiguration, AgentProviderMapping


class LLMConfigurationOrchestrator:
    """Orchestrator that coordinates LLM configuration services."""

    def __init__(self,
                 credentials_provider: ICredentialsProvider,
                 configuration_builder: IProviderConfigurationBuilder,
                 validator: IProviderValidator,
                 discovery: IProviderDiscovery):
        """Initialize with service dependencies."""
        self._credentials = credentials_provider
        self._builder = configuration_builder
        self._validator = validator
        self._discovery = discovery

    def get_agent_configuration(self, agent_type: str) -> Optional[ProviderConfiguration]:
        """Get complete, validated configuration for an agent."""
        try:
            # Build base configuration (without credentials)
            base_config = self._builder.build_agent_configuration(agent_type)

            # Get credentials for the provider
            credentials = self._credentials.get_credentials(base_config.provider)
            if not credentials:
                return None

            # Create complete configuration
            complete_config = ProviderConfiguration(
                provider=base_config.provider,
                model=base_config.model,
                credentials=credentials,
                parameters=base_config.parameters
            )

            # Validate the configuration
            return complete_config if self._validator.validate_configuration(complete_config) else None

        except Exception:
            return None

    def get_agent_mapping(self, agent_type: str) -> Optional[AgentProviderMapping]:
        """Get validated agent to provider mapping."""
        config = self.get_agent_configuration(agent_type)
        return self._builder.build_agent_mapping(agent_type, config) if config else None


    def validate_agent_setup(self, agent_type: str) -> Dict[str, Any]:
        """Validate complete agent setup and return detailed status."""
        result = {
            "valid": False,
            "agent_type": agent_type,
            "errors": [],
            "warnings": []
        }

        try:
            config = self.get_agent_configuration(agent_type)

            if not config:
                result["errors"].append(f"Could not build configuration for agent {agent_type}")
                return result

            # Detailed validation
            validation_errors = self._validator.get_validation_errors(config)
            if validation_errors:
                result["errors"].extend(validation_errors)
                return result

            # Agent-specific validation
            if not self._validator.validate_agent_configuration(agent_type, config):
                result["warnings"].append(f"Configuration may not be optimal for agent {agent_type}")

            result["valid"] = True
            result["provider"] = config.provider.value
            result["model"] = config.model

        except Exception as e:
            result["errors"].append(f"Validation failed: {str(e)}")

        return result

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system configuration status."""
        # Get provider discovery status
        provider_status = self._discovery.get_provider_status()

        # Validate each agent type
        agent_statuses = {}
        for agent_type in ["therapist", "supervisor"]:
            agent_statuses[agent_type] = self.validate_agent_setup(agent_type)

        # Overall system health
        all_agents_valid = all(status["valid"] for status in agent_statuses.values())

        return {
            "system_healthy": all_agents_valid and provider_status["available_count"] > 0,
            "provider_status": provider_status,
            "agent_configurations": agent_statuses,
            "recommendations": self._generate_recommendations(provider_status, agent_statuses)
        }

    @staticmethod
    def _generate_recommendations(provider_status: dict, agent_statuses: dict) -> list:
        """Generate recommendations for configuration improvements."""
        recommendations = []

        # Provider recommendations
        if provider_status["availability_percentage"] < 50:
            recommendations.append("Consider configuring more LLM providers for better resilience")

        # Agent recommendations
        for agent_type, status in agent_statuses.items():
            if not status["valid"]:
                recommendations.append(f"Fix configuration issues for {agent_type} agent")
            elif status.get("warnings"):
                recommendations.append(f"Optimize configuration for {agent_type} agent")

        if not recommendations:
            recommendations.append("System configuration is optimal")

        return recommendations