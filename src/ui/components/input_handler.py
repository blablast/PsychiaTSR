"""Input handling component for chat interface."""

import streamlit as st
from src.core.workflow import send_supervisor_request_stream
from src.ui.technical_log_display import add_technical_log


class InputHandler:
    """Component responsible for handling user input and message processing."""

    @staticmethod
    def handle_pending_messages() -> None:
        """Process any pending user messages."""
        if not InputHandler._has_pending_message():
            return

        prompt = st.session_state.pending_user_message
        st.session_state.pending_user_message = None

        InputHandler._add_user_message(prompt)
        InputHandler._trigger_response_generation(prompt)


    @staticmethod
    def handle_post_streaming_refresh() -> bool:
        """Handle refresh after streaming completes.

        Returns:
            True if rerun was triggered, False otherwise
        """
        if st.session_state.pop('stream_refresh_pending', False):
            st.rerun()
            return True
        return False

    @staticmethod
    def setup_user_input() -> None:
        """Set up user input interface."""
        # Add user input at the bottom
        st.divider()

        # User input
        if prompt := st.chat_input("Jak się dziś czujesz?"):
            InputHandler._initialize_session_if_needed()
            InputHandler._initialize_conversation_manager_if_needed()
            InputHandler._queue_user_message(prompt)

        st.divider()

    @staticmethod
    def _has_pending_message() -> bool:
        """Check if there's a pending user message to process."""
        return (
            hasattr(st.session_state, 'pending_user_message') and
            st.session_state.pending_user_message
        )

    @staticmethod
    def _add_user_message(prompt: str) -> None:
        """Add user message to conversation manager."""
        if 'conversation_manager' in st.session_state:
            st.session_state.conversation_manager.accept_user_input(prompt)

    @staticmethod
    def _trigger_response_generation(prompt: str) -> None:
        """Trigger therapist response generation."""
        try:

            if st.session_state.get('therapist_agent') is None:
                with st.spinner("🤖 Inicjalizuję agentów terapii..."):
                    from src.core.workflow import initialize_agents
                    init_result = initialize_agents()
                    if not init_result:
                        add_technical_log("error", "❌ Nie można zainicjować agentów terapii")
                        return

            # Mark that we're processing a message
            st.session_state.processing_message = True

            # Set up streaming generator - function handles orchestration internally
            with st.spinner("🔍 Konsultuję z supervisorem..."):
                generator = send_supervisor_request_stream(prompt)
                if generator is None:
                    add_technical_log("workflow_error", "❌ Generator workflow jest None")
                    st.session_state.processing_message = False
                    return

                st.session_state.stream_generator = generator

        except Exception as e:
            add_technical_log("error", f"❌ Błąd podczas generowania odpowiedzi: {str(e)}")
            st.session_state.processing_message = False

    @staticmethod
    def _initialize_session_if_needed() -> None:
        """Initialize session if none exists."""
        if not st.session_state.get('session_id'):
            from src.core.session import create_new_session
            create_new_session()
            add_technical_log("info", f"🆕 Nowa sesja utworzona automatycznie: {st.session_state.session_id}")

    @staticmethod
    def _initialize_conversation_manager_if_needed() -> None:
        """Initialize ConversationManager if needed."""
        if 'conversation_manager' not in st.session_state:
            from src.core.conversation import ConversationManager
            st.session_state.conversation_manager = ConversationManager()

    @staticmethod
    def _queue_user_message(prompt: str) -> None:
        """Queue user message for processing on next rerun."""
        # Log user message immediately
        add_technical_log("info", f"👤 Użytkownik: {prompt}")
        st.session_state.pending_user_message = prompt
        st.rerun()

    @staticmethod
    def cleanup_streaming_state() -> None:
        """Clean up streaming-related state after completion."""
        st.session_state.pop('processing_message', None)
        st.session_state.pop('stream_generator', None)