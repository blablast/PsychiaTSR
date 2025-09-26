"""Provides therapy agents from Streamlit session state."""

import streamlit as st

from ...core.session.interfaces.session_provider_interface import ISessionAgentProvider


class StreamlitAgentProvider(ISessionAgentProvider):
    """Provides therapy agents from Streamlit session state storage."""

    def get_therapist_agent(self):
        """
        Get the therapist agent instance from Streamlit session state.

        Returns:
            TherapistAgent instance or None if not initialized
        """
        return st.session_state.get("therapist_agent")

    def get_supervisor_agent(self):
        """
        Get the supervisor agent instance from Streamlit session state.

        Returns:
            SupervisorAgent instance or None if not initialized
        """
        return st.session_state.get("supervisor_agent")

    def is_initialized(self) -> bool:
        """
        Check if both therapy agents are properly initialized in session state.

        Returns:
            True if both therapist and supervisor agents are available
        """
        return self.get_therapist_agent() is not None and self.get_supervisor_agent() is not None
