"""Streamlit implementation of session context interfaces."""

from typing import Any, Dict, List, Optional
import streamlit as st

from ...core.session.interfaces.session_context_interface import ISessionContext, IUINotifier
from config import Config


class StreamlitSessionContext(ISessionContext):
    """Streamlit implementation of session context interface."""

    def get_session_value(self, key: str, default: Any = None) -> Any:
        """Get value from Streamlit session state."""
        return st.session_state.get(key, default)

    def set_session_value(self, key: str, value: Any) -> None:
        """Set value in Streamlit session state."""
        st.session_state[key] = value

    def has_session_value(self, key: str) -> bool:
        """Check if key exists in Streamlit session state."""
        return key in st.session_state

    def get_session_id(self) -> Optional[str]:
        """Get current session ID from Streamlit state."""
        return st.session_state.get("session_id")

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get conversation messages from Streamlit state."""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        return st.session_state.messages

    def add_message(self, message: Dict[str, Any]) -> None:
        """Add message to conversation in Streamlit state."""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        st.session_state.messages.append(message)

    def get_current_stage(self) -> str:
        """Get current therapy stage from Streamlit state."""
        return st.session_state.get("current_stage", "opening")

    def set_current_stage(self, stage: str) -> None:
        """Set current therapy stage in Streamlit state."""
        st.session_state["current_stage"] = stage

    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """Get agent configuration from Streamlit state with Config fallbacks."""
        config = Config.get_instance()
        agent_defaults = config.get_agent_defaults()

        # Get from session state with fallbacks to Config
        model_key = f"selected_{agent_type}_model"
        provider_key = f"selected_{agent_type}_provider"

        model = st.session_state.get(model_key, agent_defaults[agent_type]["model"])
        provider = st.session_state.get(provider_key, agent_defaults[agent_type]["provider"])

        return {
            "model": model,
            "provider": provider,
            "parameters": config.get_agent_parameters(agent_type),
        }


class StreamlitUINotifier(IUINotifier):
    """Streamlit implementation of UI notifications interface."""

    def show_success(self, message: str) -> None:
        """Show success message using Streamlit."""
        st.success(message)

    def show_error(self, message: str) -> None:
        """Show error message using Streamlit."""
        st.error(message)

    def show_info(self, message: str) -> None:
        """Show info message using Streamlit."""
        st.info(message)

    def show_warning(self, message: str) -> None:
        """Show warning message using Streamlit."""
        st.warning(message)
