"""Conversation display component for chat interface."""

import streamlit as st
from typing import Optional
from .message_renderer import MessageRenderer

# Audio services have been removed
AUDIO_AVAILABLE = False


class ConversationDisplay:
    """Component responsible for displaying conversation history."""

    @staticmethod
    def display_conversation_history() -> None:
        """Display the complete conversation history."""
        if "conversation_manager" not in st.session_state:
            return

        conversation = st.session_state.conversation_manager.get_full_conversation_for_display()

        for i, message in enumerate(conversation):
            MessageRenderer.render_message(message)

    @staticmethod
    def create_messages_container(height: int = 750) -> tuple:
        """Create containers for messages display.

        Args:
            height: Height of the scrollable messages container

        Returns:
            Tuple of (conversation_container, streaming_container)
        """
        messages_container = st.container(height=height)

        with messages_container:
            conversation_container = st.container()
            streaming_container = st.container()

        return conversation_container, streaming_container
