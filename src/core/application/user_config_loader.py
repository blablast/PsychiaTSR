"""User configuration loading and application."""

import streamlit as st
from config import Config, get_agent_defaults
from ..di.service_locator import ServiceLocator
from ..config.config_manager import ConfigManager
from ..models import Language


class UserConfigLoader:
    """Handles loading and applying user configuration to session state."""

    def __init__(self):
        self._config_manager = ServiceLocator.resolve(ConfigManager)

    def load_and_apply_config(self, force_reload: bool = False):
        """Load user configuration and apply it to session state."""
        if "config_loaded" in st.session_state and not force_reload:
            return  # Already loaded

        user_config = self._config_manager.load_config()
        agent_defaults = get_agent_defaults()

        # Apply model configurations
        self._apply_model_config(user_config, agent_defaults)

        # Apply prompting strategy
        self._apply_prompting_config(user_config)

        # Apply language configuration
        self._apply_language_config(user_config)

        st.session_state.config_loaded = True

    @staticmethod
    def reload_config():
        """Force reload configuration from file."""
        if "config_loaded" in st.session_state:
            del st.session_state["config_loaded"]

        # Clear cached config in Config singleton
        from config import Config

        Config._instance = None

        # Reload config
        loader = UserConfigLoader()
        loader.load_and_apply_config(force_reload=True)

    @staticmethod
    def _apply_model_config(user_config: dict, agent_defaults: dict):
        """
        Apply model and provider configuration for therapist and supervisor.
        Args:
            user_config: Loaded user configuration dictionary
            agent_defaults: Default agent configurations
        """

        # Use the 'agents' key which contains therapist/supervisor configs
        agents_config = user_config.get("agents", {})
        therapist_config = agents_config.get("therapist", {})
        supervisor_config = agents_config.get("supervisor", {})

        st.session_state.selected_therapist_model = therapist_config.get(
            "model", agent_defaults["therapist"]["model"]
        )
        st.session_state.selected_therapist_provider = therapist_config.get(
            "provider", agent_defaults["therapist"]["provider"]
        )
        st.session_state.selected_supervisor_model = supervisor_config.get(
            "model", agent_defaults["supervisor"]["model"]
        )
        st.session_state.selected_supervisor_provider = supervisor_config.get(
            "provider", agent_defaults["supervisor"]["provider"]
        )

    @staticmethod
    def _apply_prompting_config(user_config: dict):
        """Apply prompting strategy configuration."""
        st.session_state.use_system_prompt = user_config.get("use_system_prompt", True)

    @staticmethod
    def _apply_language_config(user_config: dict):
        """Apply language configuration."""
        language_code = user_config.get("language", "pl")

        if language_code == "pl":
            st.session_state.language = Language.POLISH
        elif language_code == "en":
            st.session_state.language = Language.ENGLISH
        else:
            st.session_state.language = Language.POLISH  # Default fallback
