"""Session state initialization for Streamlit application."""

import streamlit as st
from ...core.services.simple_service_factory import SimpleServiceFactory


class SessionStateInitializer:
    """Handles initialization of default session state values."""

    @staticmethod
    def initialize():
        """Initialize all required session state variables with default values."""
        # Session management
        if "session_id" not in st.session_state:
            st.session_state.session_id = None


        # Current therapy stage
        if "current_stage" not in st.session_state:
            # Get first stage dynamically using SimpleServiceFactory
            stage_manager = SimpleServiceFactory.create_stage_manager()
            first_stage = stage_manager.get_first_stage()
            st.session_state.current_stage = first_stage.stage_id if first_stage else "opening"

        # Core services - resolved through SimpleServiceFactory
        if "storage" not in st.session_state:
            st.session_state.storage = SimpleServiceFactory.create_storage_provider()

        if "safety_checker" not in st.session_state:
            st.session_state.safety_checker = SimpleServiceFactory.create_safety_checker()

        # Agent instances
        if "therapist_agent" not in st.session_state:
            st.session_state.therapist_agent = None

        if "supervisor_agent" not in st.session_state:
            st.session_state.supervisor_agent = None

        # UI state
        if "show_crisis_message" not in st.session_state:
            st.session_state.show_crisis_message = False

        # Technical logging
        if "technical_log" not in st.session_state:
            st.session_state.technical_log = []

        # Message processing state
        if "pending_user_message" not in st.session_state:
            st.session_state.pending_user_message = None

        # Audio configuration - initialize with defaults first
        if "audio_enabled" not in st.session_state:
            st.session_state.audio_enabled = False

        if "_tts_cfg" not in st.session_state:
            st.session_state._tts_cfg = None

        # Load audio config from app config
        SessionStateInitializer._load_audio_config_from_session()

    @staticmethod
    def _load_audio_config_from_session():
        """Load audio configuration from app config."""
        try:
            from ...core.config.config_manager import ConfigManager
            config_manager = ConfigManager()
            audio_config = config_manager.get_audio_config()

            if audio_config.get("enabled", False):
                st.session_state.audio_enabled = True

                # Load TTS config if available
                tts_config = audio_config.get("tts_config", {})
                if tts_config.get("voice_id"):
                    # Add API key from environment if available
                    import os
                    api_key = os.getenv('ELEVENLABS_API_KEY')
                    if api_key:
                        tts_config = tts_config.copy()
                        tts_config['api_key'] = api_key

                    st.session_state._tts_cfg = tts_config
        except Exception:
            # Fail silently - don't break app if audio config loading fails
            pass