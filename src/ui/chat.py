"""Chat display functionality for Psychia TSR"""

import streamlit as st

from src.core.session import format_timestamp, load_stages
from src.core.workflow import send_supervisor_request
from src.ui.technical_log_display import add_technical_log

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
        # Chat messages display
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

        # Auto-scroll to bottom by adding empty space at the end
        if st.session_state.messages:
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

        # Show detailed processing steps
        with st.spinner("🔍 Konsultuję z supervisorem → 💬 Generuję odpowiedź terapeuty..."):
            # Process with supervisor and therapist
            send_supervisor_request(prompt)

        # Rerun to show response
        st.rerun()

    # Chat input - always at the bottom
    if prompt := st.chat_input('Napisz swoją wiadomość...'):
        # Create new session if none exists
        if not st.session_state.session_id:
            from src.core.session import create_new_session
            create_new_session()
            add_technical_log("info", f"🆕 Nowa sesja utworzona automatycznie: {st.session_state.session_id}")

        # Add user message immediately to session state for instant display
        from datetime import datetime
        user_message = {
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.messages.append(user_message)

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