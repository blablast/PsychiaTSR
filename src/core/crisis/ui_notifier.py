"""UI notification interfaces for crisis situations."""

from abc import ABC, abstractmethod


class UICrisisNotifier(ABC):
    """Abstract interface for UI crisis notifications."""

    @abstractmethod
    def notify_crisis_detected(self) -> None:
        """Notify UI that a crisis has been detected."""
        pass

    @abstractmethod
    def show_crisis_message(self, message: str) -> None:
        """Display crisis message to user."""
        pass


class StreamlitCrisisNotifier(UICrisisNotifier):
    """Streamlit-specific crisis notification implementation."""

    def notify_crisis_detected(self) -> None:
        """Set Streamlit session state to show crisis."""
        import streamlit as st
        st.session_state.show_crisis_message = True

    def show_crisis_message(self, message: str) -> None:
        """Show crisis message using Streamlit error widget."""
        import streamlit as st
        st.error(message)


class NoOpCrisisNotifier(UICrisisNotifier):
    """No-op implementation for testing or non-UI contexts."""

    def notify_crisis_detected(self) -> None:
        """Do nothing - for testing."""
        pass

    def show_crisis_message(self, message: str) -> None:
        """Do nothing - for testing."""
        pass