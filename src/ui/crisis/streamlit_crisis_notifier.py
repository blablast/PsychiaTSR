"""Streamlit-specific crisis notification implementation."""

import streamlit as st
from ...core.crisis.interfaces import UICrisisNotifier


class StreamlitCrisisNotifier(UICrisisNotifier):
    """Streamlit-specific crisis notification implementation."""

    def notify_crisis_detected(self) -> None:
        """Set Streamlit session state to show crisis."""
        st.session_state.show_crisis_message = True

    def show_crisis_message(self, message: str) -> None:
        """Show crisis message using Streamlit error widget."""
        st.error(message)