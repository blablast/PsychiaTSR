"""Navigation sidebar for Psychia TSR"""

import streamlit as st
from src.ui.technical_log_display import add_technical_log


def display_sidebar():
    """Display simplified navigation sidebar."""
    with st.sidebar:
        st.title("🧠 Psychia TSR")

        # Navigation menu
        st.subheader("📋 Menu")

        # Navigation options
        page = st.radio(
            "Wybierz stronę:",
            options=["💬 Konwersacja", "📝 Prompty"], #"⚙️ Ustawienia", "📊 Raporty", "🔬 Testy"],
            index=0,  # Default to conversation
            key="navigation_page"
        )

        # Map page names to internal identifiers
        page_mapping = {
            "💬 Konwersacja": "conversation",
            "📝 Prompty": "prompts",
            #"⚙️ Ustawienia": "settings",
            #"📊 Raporty": "reports",
            #"🔬 Testy": "tests"
        }

        # Set current page in session state
        st.session_state["current_page"] = page_mapping[page]

        st.divider()

        # Current session info (if exists)
        if not st.session_state.get("session_id"):
            st.warning("**Brak aktywnej sesji**")

        # Quick stats
        if st.session_state.get("conversation_manager"):
            conv = st.session_state.conversation_manager.get_full_conversation_for_display()
            if conv:
                st.metric("Wiadomości", len(conv))

        # Enhanced audio status indicator
        _display_audio_status_sidebar()

        st.divider()
        st.markdown("**Psychia TSR v1.0**")
        # st.markdown("*System wsparcia terapeutycznego*")


def _display_audio_status_sidebar():
    """Display detailed audio status information in sidebar."""
    try:
        from src.audio.services.audio_service import AudioService
        AUDIO_AVAILABLE = True
    except ImportError:
        AUDIO_AVAILABLE = False

    audio_enabled = st.session_state.get("audio_enabled", False)
    tts_configured = bool(st.session_state.get("_tts_cfg"))

    if not AUDIO_AVAILABLE:
        st.warning("🔧 Moduł audio niedostępny")
        return

    if not audio_enabled:
        st.info("🔇 Audio wyłączone")
        return

    if not tts_configured:
        st.warning("🔧 Audio włączone (brak konfiguracji)")
        st.caption("Przejdź do Ustawień → Audio")
        return

    # Audio is enabled and configured
    tts_config = st.session_state.get("_tts_cfg", {})
    voice_id = tts_config.get("voice_id", "unknown")

    # Check audio modes
    webrtc_mode = st.session_state.get("webrtc_mode", False)
    fallback_mode = st.session_state.get("fallback_mode", True)

    if fallback_mode and not webrtc_mode:
        st.success("🎵 HTML5 Audio aktywne")
        st.caption(f"Voice: {voice_id}")
        st.caption("🎧 Tylko słuchanie (bez mikrofonu)")
    elif webrtc_mode and not fallback_mode:
        st.success("🎵 WebRTC Audio aktywne")
        st.caption(f"Voice: {voice_id}")
        st.caption("🎙️ Wymaga mikrofonu")
    elif webrtc_mode and fallback_mode:
        st.success("🎵 Audio aktywne (oba tryby)")
        st.caption(f"Voice: {voice_id}")
        st.caption("WebRTC + HTML5 fallback")
    else:
        st.warning("⚠️ Audio skonfigurowane ale tryby wyłączone")
        st.caption("Wybierz tryb w Ustawieniach")