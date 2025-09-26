"""Provider validation service."""

from ..interfaces import IProviderValidator
from ..domain import ProviderCredentials, ProviderConfiguration


class ProviderValidator(IProviderValidator):
    """Service for validating provider configurations."""

    def validate_credentials(self, credentials: ProviderCredentials) -> bool:
        """Validate provider credentials."""
        if not credentials:
            return False

        return credentials.is_valid()

    def validate_configuration(self, config: ProviderConfiguration) -> bool:
        """Validate complete provider configuration."""
        if not config:
            return False

        if not self.validate_credentials(config.credentials):
            return False

        if not config.model or not config.model.strip():
            return False

        if not config.parameters:
            return False

        return True

    def get_validation_errors(self, config: ProviderConfiguration) -> list:
        """Get detailed validation errors for configuration."""
        errors = []

        if not config:
            errors.append("Configuration is None")
            return errors

        if not config.credentials:
            errors.append("Credentials are missing")
        elif not self.validate_credentials(config.credentials):
            errors.append(f"Invalid credentials for provider {config.provider.value}")

        if not config.model or not config.model.strip():
            errors.append("Model name is missing or empty")

        if not config.parameters:
            errors.append("LLM parameters are missing")

        return errors

    def validate_agent_configuration(self, agent_type: str, config: ProviderConfiguration) -> bool:
        """Validate configuration for specific agent type."""
        if not agent_type or not agent_type.strip():
            return False

        if not self.validate_configuration(config):
            return False

        if agent_type == "supervisor":
            if config.parameters.temperature > 0.5:
                return False

        return True
