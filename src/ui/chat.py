"""Chat display functionality for Psychia TSR"""

import streamlit as st

from src.core.session import format_timestamp, load_stages
from src.core.workflow import send_supervisor_request, send_supervisor_request_stream
from src.ui.technical_log_display import add_technical_log
from typing import Optional, Dict

def display_chat_interface():
    """Display main chat interface"""

    # Crisis message display
    if st.session_state.show_crisis_message:
        st.error("⚠️ **UWAGA**: Wykryto sygnały mogące wskazywać na kryzys psychiczny. "
                "Jeśli masz myśli samobójcze lub potrzebujesz natychmiastowej pomocy, "
                "skontaktuj się z Centrum Wsparcia (116 123) lub udaj się na SOR.")

    # Create a scrollable container for messages (reduced height for stage info)
    messages_container = st.container(height=750)

    with messages_container:
        # Get conversation from ConversationManager if available
        if 'conversation_manager' in st.session_state:
            conversation = st.session_state.conversation_manager.get_full_conversation_for_display()

            for message in conversation:
                # Check if this is a pending message
                is_pending = getattr(message, 'is_pending', False)

                with st.chat_message(message.role):
                    content = message.text
                    if is_pending:
                        content += " ⏳"  # Add pending indicator
                    st.write(content)

                    # Show timestamp and response times for therapist messages
                    if hasattr(message, 'timestamp'):
                        caption_parts = [f"🕒 {format_timestamp(message.timestamp)}"]

                        # Add response times for therapist messages
                        if message.role == "therapist":
                            response_times = _get_latest_response_times()
                            if response_times:
                                sup_time = response_times.get('supervisor_time_ms', 0)
                                ther_time = response_times.get('therapist_time_ms', 0)
                                if sup_time > 0 or ther_time > 0:
                                    time_str = f"(SUP: {sup_time/1000:.2f}s, THE: {ther_time/1000:.2f}s)"
                                    caption_parts.append(time_str)

                        st.caption(" ".join(caption_parts))
        else:
            # Fallback to old session_state.messages
            for message in st.session_state.messages:
                # Special rendering for stage transition messages
                if message.get("is_stage_transition", False):
                    st.info(message["content"])
                else:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])

                        # Show timestamp if available
                        if "timestamp" in message:
                            st.caption(f"🕒 {format_timestamp(message['timestamp'])}")

        # Show streaming response if there's a pending message
        if hasattr(st.session_state, 'processing_message') and st.session_state.processing_message:
            with st.chat_message("assistant"):
                # Collect streamed content
                full_response = ""
                response_placeholder = st.empty()

                for chunk in st.session_state.stream_generator:
                    full_response += chunk
                    response_placeholder.write(full_response)

                # Store the final response in session state for persistence
                st.session_state.last_streamed_response = full_response

                # Clear the processing state after streaming
                del st.session_state.processing_message
                del st.session_state.stream_generator

        # Auto-scroll to bottom by adding empty space at the end
        st.empty()

    # Check if we need to process a pending message
    if hasattr(st.session_state, 'pending_user_message') and st.session_state.pending_user_message:
        prompt = st.session_state.pending_user_message
        st.session_state.pending_user_message = None

        # Initialize agents if needed (lazy loading)
        if st.session_state.therapist_agent is None:
            with st.spinner("🤖 Inicjalizuję agentów terapii..."):
                from src.core.workflow import initialize_agents
                if not initialize_agents():
                    st.error("Nie można zainicjować agentów terapii")
                    return

        # Set up streaming
        with st.spinner("🔍 Konsultuję z supervisorem..."):
            st.session_state.processing_message = True
            st.session_state.stream_generator = send_supervisor_request_stream(prompt)

        # Rerun to show streaming
        st.rerun()

    # Chat input - always at the bottom
    if prompt := st.chat_input('Napisz swoją wiadomość...'):
        # Create new session if none exists
        if not st.session_state.session_id:
            from src.core.session import create_new_session
            create_new_session()
            add_technical_log("info", f"🆕 Nowa sesja utworzona automatycznie: {st.session_state.session_id}")

        # Initialize ConversationManager if needed
        if 'conversation_manager' not in st.session_state:
            from src.core.conversation import ConversationManager
            st.session_state.conversation_manager = ConversationManager()

        # Log user message immediately
        add_technical_log("info", f"👤 Użytkownik: {prompt}")

        # Set pending message for processing on next rerun
        st.session_state.pending_user_message = prompt

        # Force immediate refresh to show user message
        st.rerun()

    st.divider()


def display_stage_controls():
    """Display stage navigation controls below chat"""
    from src.core.session import advance_stage

    st.subheader("🎯 Kontrola etapu terapii")


    # Stage navigation buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("⬅️ Poprzedni etap", use_container_width=True):
            if advance_stage("previous"):
                # Force agents reinitialization with new stage prompts
                _reinitialize_agents_for_new_stage()
            st.rerun()

    with col2:
        if st.button("➡️ Następny etap", use_container_width=True):
            if advance_stage("next"):
                # Force agents reinitialization with new stage prompts
                _reinitialize_agents_for_new_stage()
            st.rerun()

    with col3:
        st.caption("Zmiana etapu automatycznie odnowi prompty systemowe")


def _reinitialize_agents_for_new_stage():
    """Reinitialize agents to load new stage prompts"""
    # Clear existing agents to force reinitialization with new prompts
    st.session_state.therapist_agent = None
    st.session_state.supervisor_agent = None

    # Log stage change
    add_technical_log("stage_transition", f"🔄 Agents reinitialized for stage: {st.session_state.current_stage}")


def display_crisis_warning():
    """Display crisis warning if needed"""
    if st.session_state.show_crisis_message:
        st.error("⚠️ **UWAGA**: Wykryto sygnały mogące wskazywać na kryzys psychiczny. "
                "Jeśli masz myśli samobójcze lub potrzebujesz natychmiastowej pomocy, "
                "skontaktuj się z Centrum Wsparcia (116 123) lub udaj się na SOR.")


def _get_latest_response_times() -> Optional[Dict[str, int]]:
    """Get the latest supervisor and therapist response times from technical logs."""
    try:
        # Try to get from session_data first
        if hasattr(st.session_state, 'session_data') and st.session_state.session_data:
            technical_logs = st.session_state.session_data.get('technical_logs', [])
        # Fallback to logger in session state
        elif hasattr(st.session_state, 'therapy_session_logger'):
            logger = st.session_state.therapy_session_logger
            if hasattr(logger, 'get_logs'):
                log_entries = logger.get_logs()
                technical_logs = [entry.__dict__ if hasattr(entry, '__dict__') else entry for entry in log_entries]
            else:
                return None
        else:
            return None

        # Find the most recent supervisor and therapist response times
        supervisor_time = None
        therapist_time = None

        # Reverse iterate to find most recent times
        for log_entry in reversed(technical_logs):
            if supervisor_time is None and log_entry.get('event_type') == 'supervisor_response':
                supervisor_time = log_entry.get('response_time_ms')

            if therapist_time is None and log_entry.get('event_type') == 'therapist_response':
                therapist_time = log_entry.get('response_time_ms')

            # Stop when we have both times
            if supervisor_time is not None and therapist_time is not None:
                break

        if supervisor_time is not None or therapist_time is not None:
            return {
                'supervisor_time_ms': supervisor_time or 0,
                'therapist_time_ms': therapist_time or 0
            }

        return None

    except Exception:
        # Silently fail if we can't get response times
        return None