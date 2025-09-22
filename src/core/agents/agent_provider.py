"""Provides agents from Streamlit session state."""

import streamlit as st

from .interfaces.agent_provider_interface import IAgentProvider


class StreamlitAgentProvider(IAgentProvider):
    """Provides agents from Streamlit session state."""

    def get_therapist_agent(self):
        return st.session_state.get('therapist_agent')

    def get_supervisor_agent(self):
        return st.session_state.get('supervisor_agent')

    def is_initialized(self) -> bool:
        return (self.get_therapist_agent() is not None and
                self.get_supervisor_agent() is not None)