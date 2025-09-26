"""Agent configuration loader."""

from typing import Dict, Any


class AgentLoader:
    """Handles agent-specific configuration (therapist, supervisor)."""

    def __init__(self, config_data: Dict[str, Any]):
        """Initialize with configuration data."""
        self._agents_config = config_data.get("agents", {})

    def get_agent_provider(self, agent_type: str) -> str:
        """Get provider for specified agent."""
        agent_config = self._agents_config.get(agent_type, {})
        return agent_config.get("provider", self._get_default_provider(agent_type))

    def get_agent_model(self, agent_type: str) -> str:
        """Get model for specified agent."""
        agent_config = self._agents_config.get(agent_type, {})
        return agent_config.get("model", self._get_default_model(agent_type))

    def get_agent_parameters(self, agent_type: str) -> Dict[str, Any]:
        """Get parameters for specified agent."""
        agent_config = self._agents_config.get(agent_type, {})
        agent_params = agent_config.get("parameters", {})

        # Default parameters
        defaults = {"temperature": 0.7, "max_tokens": 150, "top_p": 0.9}

        # Merge with agent-specific overrides
        return {**defaults, **agent_params}

    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """Get complete configuration for specified agent."""
        return {
            "provider": self.get_agent_provider(agent_type),
            "model": self.get_agent_model(agent_type),
            "parameters": self.get_agent_parameters(agent_type),
        }

    def get_all_agents_config(self) -> Dict[str, Dict[str, Any]]:
        """Get configuration for all agents."""
        return {
            "therapist": self.get_agent_config("therapist"),
            "supervisor": self.get_agent_config("supervisor"),
        }

    @staticmethod
    def _get_default_provider(agent_type: str) -> str:
        """Get default provider for agent type from template file."""
        import json
        from pathlib import Path

        try:
            template_path = Path("config/templates/defaults/agents_config_default.json")
            if template_path.exists():
                with open(template_path, "r", encoding="utf-8") as f:
                    defaults = json.load(f)
                    return defaults.get("agents", {}).get(agent_type, {}).get("provider", "openai")
        except Exception:
            pass

        # Fallback defaults
        defaults = {"therapist": "openai", "supervisor": "gemini"}
        return defaults.get(agent_type, "openai")

    @staticmethod
    def _get_default_model(agent_type: str) -> str:
        """Get default model for agent type from template file."""
        import json
        from pathlib import Path

        try:
            template_path = Path("config/templates/defaults/agents_config_default.json")
            if template_path.exists():
                with open(template_path, "r", encoding="utf-8") as f:
                    defaults = json.load(f)
                    return (
                        defaults.get("agents", {}).get(agent_type, {}).get("model", "gpt-4o-mini")
                    )
        except Exception:
            pass

        # Fallback defaults
        defaults = {"therapist": "gpt-4o-mini", "supervisor": "gemini-2.5-flash"}
        return defaults.get(agent_type, "gpt-4o-mini")
