"""Conversation settings page for PsychiaTSR."""

import streamlit as st
from typing import Optional, Dict, Any

# Import components that will be moved here
from src.ui.llm_config import display_llm_config


def display_conversation_settings():
    """Display conversation settings page with all configuration options."""

    st.title("⚙️ Ustawienia Konwersacji")
    st.markdown("Skonfiguruj modele AI, audio i parametry agentów dla sesji terapeutycznych.")

    # Create tabs for different settings categories
    tab_models, tab_audio, tab_agents = st.tabs([
        "🤖 Modele LLM",
        "🔊 Audio",
        "👥 Parametry Agentów"
    ])

    # Tab 1: LLM Models Configuration
    with tab_models:
        st.subheader("Konfiguracja Modeli AI")
        st.markdown("Wybierz i skonfiguruj modele dla terapeuty i nadzorcy.")

        # Get LLM configuration
        model_config = display_llm_config()

        # Apply model changes button
        if model_config and model_config.get('therapist_model') and model_config.get('supervisor_model'):
            if st.button("✅ Zastosuj wybrane modele", use_container_width=True, key="apply_models"):
                if _apply_model_changes(model_config):
                    st.success("✅ Modele zostały zastosowane!")
                    st.rerun()
                else:
                    st.error("❌ Błąd przy zastosowaniu modeli")

    # Tab 2: Audio Configuration
    with tab_audio:
        st.subheader("Konfiguracja Audio")
        _display_audio_settings()

    # Tab 3: Agent Parameters
    with tab_agents:
        st.subheader("Parametry Agentów")
        _display_agent_parameters()



def _display_audio_settings():
    """Display audio configuration settings."""
    try:
        from src.audio.services.audio_service import AudioService
        from src.ui.audio.audio_config_widget import AudioConfigWidget
        AUDIO_AVAILABLE = True
    except ImportError:
        AUDIO_AVAILABLE = False

    # Import logging function
    from src.ui.technical_log_display import add_technical_log

    if not AUDIO_AVAILABLE:
        st.warning("⚠️ Moduł audio nie jest dostępny. Zainstaluj wymagane zależności:")
        st.code("pip install streamlit-webrtc aiortc av numpy elevenlabs")
        return

    # Get previous audio state for logging
    previous_audio_state = st.session_state.get("audio_enabled", False)

    # Audio enable/disable toggle
    audio_enabled = st.checkbox(
        "🎵 Włącz syntezę mowy (TTS)",
        value=previous_audio_state,
        help="Włącz odtwarzanie odpowiedzi terapeuty jako mowa",
        key="audio_enabled_checkbox"  # Use different key to avoid conflicts
    )

    # Update session state manually
    st.session_state.audio_enabled = audio_enabled

    # Log audio state changes and save to session
    if audio_enabled != previous_audio_state:
        status_text = "włączone" if audio_enabled else "wyłączone"
        add_technical_log("audio_settings", f"🔊 Audio TTS {status_text}")

        # Save to app config
        from src.core.config.config_manager import ConfigManager
        config_manager = ConfigManager()
        config_manager.update_audio_config(audio_enabled, None)

    if audio_enabled:
        # Show audio configuration
        audio_service = AudioService()
        audio_config_widget = AudioConfigWidget(audio_service)

        st.success("🎵 Audio włączone")

        # Audio mode selection
        st.markdown("**Tryb audio:**")
        col1, col2 = st.columns(2)

        with col1:
            webrtc_mode = st.checkbox(
                "🌐 WebRTC (zaawansowane)",
                value=st.session_state.get("webrtc_mode", False),
                help="Streaming w czasie rzeczywistym - wymaga uprawnień do mikrofonu"
            )
            st.session_state.webrtc_mode = webrtc_mode

        with col2:
            fallback_mode = st.checkbox(
                "📱 HTML5 Audio (zalecane)",
                value=st.session_state.get("fallback_mode", True),
                help="Odtwarzanie przez przeglądarkę - działa bez mikrofonu"
            )
            st.session_state.fallback_mode = fallback_mode

        if not webrtc_mode and not fallback_mode:
            st.warning("⚠️ Wybierz przynajmniej jeden tryb audio")
        elif fallback_mode and not webrtc_mode:
            st.info("💡 **HTML5 Audio** - odtwarzanie bez mikrofonu, idealne do słuchania odpowiedzi!")

        # Render audio config section
        tts_config = audio_config_widget.render_config_section()
        if tts_config:
            audio_config_widget.save_config_to_session(tts_config)
            st.info("✅ Konfiguracja ElevenLabs została zapisana")
            # Log successful TTS config
            add_technical_log("audio_config", f"🎙️ Konfiguracja TTS zapisana (Voice ID: {tts_config.get('voice_id', 'unknown')})")

            # Save TTS config to app config
            from src.core.config.config_manager import ConfigManager
            config_manager = ConfigManager()
            config_manager.update_audio_config(audio_enabled, tts_config)
    else:
        st.info("🔇 Audio wyłączone")
        # Clean up audio resources
        if hasattr(st.session_state, 'pcm_buffer'):
            _cleanup_audio_resources()


def _display_agent_parameters():
    """Display agent parameters configuration."""
    st.markdown("Dostosuj zachowanie agentów terapeutycznych.")

    # Therapist parameters
    st.subheader("🧑‍⚕️ Parametry Terapeuty")

    col1, col2 = st.columns(2)

    with col1:
        temp = st.slider(
            "Temperatura",
            min_value=0.0,
            max_value=2.0,
            value=st.session_state.get("therapist_temperature", 0.7),
            step=0.1,
            help="Kontroluje kreatywność odpowiedzi (0.0 = konserwatywne, 2.0 = kreatywne)",
            key="therapist_temperature"
        )

        max_tokens = st.number_input(
            "Maksymalna liczba tokenów",
            min_value=100,
            max_value=4000,
            value=st.session_state.get("therapist_max_tokens", 1000),
            step=100,
            help="Maksymalna długość odpowiedzi terapeuty",
            key="therapist_max_tokens"
        )



    # Supervisor parameters
    st.subheader("👨‍💼 Parametry Nadzorcy")

    col3, col4 = st.columns(2)

    with col3:
        sup_temp = st.slider(
            "Temperatura nadzorcy",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get("supervisor_temperature", 0.3),
            step=0.1,
            help="Kontroluje konserwatyzm decyzji nadzorcy",
            key="supervisor_temperature"
        )

    with col4:
        crisis_sensitivity = st.selectbox(
            "Czułość na kryzys",
            options=["Niska", "Średnia", "Wysoka"],
            index=["Niska", "Średnia", "Wysoka"].index(
                st.session_state.get("crisis_sensitivity", "Średnia")
            ),
            help="Jak szybko nadzorca reaguje na sygnały kryzysowe",
            key="crisis_sensitivity"
        )

    # Parameters are automatically saved to session_state via widget keys
    # Show current values info
    if st.button("💾 Pokaż obecne ustawienia", key="show_current_settings"):
        st.success("**Aktualne parametry:**")
        st.json({
            "therapist_temperature": st.session_state.therapist_temperature,
            "therapist_max_tokens": st.session_state.therapist_max_tokens,
            "therapist_style": st.session_state.therapist_style,
            "therapist_memory": st.session_state.therapist_memory,
            "supervisor_temperature": st.session_state.supervisor_temperature,
            "crisis_sensitivity": st.session_state.crisis_sensitivity,
        })


def _apply_model_changes(model_config: Dict[str, Any]) -> bool:
    """Apply selected model changes."""
    try:
        therapist_info = model_config['therapist_model']
        supervisor_info = model_config['supervisor_model']

        # Import required modules
        from src.core.logging import LoggerFactory
        logger = LoggerFactory.create_streamlit_logger()

        # Try to initialize with new models
        if _initialize_agents_with_selected_models(logger):
            # Save model configuration as new defaults
            from src.core.config import ConfigManager
            config_manager = ConfigManager()
            config_manager.update_model_config(
                therapist_model=therapist_info['model_id'],
                therapist_provider=therapist_info['provider'],
                supervisor_model=supervisor_info['model_id'],
                supervisor_provider=supervisor_info['provider']
            )

            # Log model information
            logger.log_model_info(
                therapist_model=therapist_info['model_id'],
                supervisor_model=supervisor_info['model_id'],
                therapist_provider=therapist_info['provider'],
                supervisor_provider=supervisor_info['provider']
            )

            # Update session with new model information if session exists
            if st.session_state.get('session_id'):
                from src.infrastructure.storage import StorageProvider
                from config import Config
                storage = StorageProvider(Config.LOGS_DIR)
                storage.update_session_models(
                    session_id=st.session_state.session_id,
                    therapist_model=therapist_info['model_id'],
                    supervisor_model=supervisor_info['model_id'],
                    therapist_provider=therapist_info['provider'],
                    supervisor_provider=supervisor_info['provider']
                )

            return True

        return False

    except Exception as e:
        st.error(f"Błąd podczas zastosowania modeli: {str(e)}")
        return False


def _initialize_agents_with_selected_models(logger=None):
    """Initialize agents with user-selected models and providers."""
    try:
        from src.llm import OpenAIProvider, GeminiProvider
        from src.agents import TherapistAgent, SupervisorAgent
        from src.core.safety import SafetyChecker
        from config import Config
        import os

        # Get selected models from session state with new defaults
        agent_defaults = Config.get_agent_defaults()
        therapist_provider = st.session_state.get('selected_therapist_provider', agent_defaults['therapist']['provider'])
        therapist_model = st.session_state.get('selected_therapist_model', agent_defaults['therapist']['model'])
        supervisor_provider = st.session_state.get('selected_supervisor_provider', agent_defaults['supervisor']['provider'])
        supervisor_model = st.session_state.get('selected_supervisor_model', agent_defaults['supervisor']['model'])

        # Initialize therapist LLM
        if therapist_provider == 'openai':
            api_key = st.session_state.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
            if not api_key:
                st.error("Brak klucza API OpenAI")
                return False
            therapist_llm = OpenAIProvider(therapist_model, api_key=api_key)
        elif therapist_provider == 'gemini':
            api_key = st.session_state.get('google_api_key') or os.getenv('GOOGLE_API_KEY')
            if not api_key:
                st.error("Brak klucza API Google")
                return False
            therapist_llm = GeminiProvider(therapist_model, api_key=api_key)
        else:
            st.error(f"Nieznany provider: {therapist_provider}")
            return False

        # Initialize supervisor LLM
        if supervisor_provider == 'openai':
            api_key = st.session_state.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
            if not api_key:
                st.error("Brak klucza API OpenAI")
                return False
            supervisor_llm = OpenAIProvider(supervisor_model, api_key=api_key)
        elif supervisor_provider == 'gemini':
            api_key = st.session_state.get('google_api_key') or os.getenv('GOOGLE_API_KEY')
            if not api_key:
                st.error("Brak klucza API Google")
                return False
            supervisor_llm = GeminiProvider(supervisor_model, api_key=api_key)
        else:
            st.error(f"Nieznany provider: {supervisor_provider}")
            return False

        # Test availability
        if not therapist_llm.is_available():
            st.error(f"Model terapeuty {therapist_model} nie jest dostępny")
            return False

        if not supervisor_llm.is_available():
            st.error(f"Model nadzorcy {supervisor_model} nie jest dostępny")
            return False

        # Create logger if not provided
        if not logger:
            from src.core.logging import LoggerFactory
            logger = LoggerFactory.create_streamlit_logger()

        # Initialize agents with logger using ServiceFactory
        from src.core.prompts import UnifiedPromptManager
        from src.core.services import ServiceFactory

        safety_checker = SafetyChecker()
        prompt_manager = UnifiedPromptManager(Config.PROMPT_DIR)

        st.session_state.therapist_agent = ServiceFactory.create_therapist_agent(
            llm_provider=therapist_llm,
            prompt_manager=prompt_manager,
            safety_checker=safety_checker,
            logger=logger
        )
        st.session_state.supervisor_agent = ServiceFactory.create_supervisor_agent(
            llm_provider=supervisor_llm,
            prompt_manager=prompt_manager,
            safety_checker=safety_checker,
            logger=logger
        )

        return True

    except Exception as e:
        st.error(f"Błąd inicjalizacji agentów: {str(e)}")
        return False


def _cleanup_audio_resources():
    """Clean up audio resources when audio is disabled."""
    try:
        # Close PCM buffer
        if "pcm_buffer" in st.session_state:
            pcm_buffer = st.session_state.pcm_buffer
            if hasattr(pcm_buffer, 'close'):
                pcm_buffer.close()
            del st.session_state.pcm_buffer

        # Clear TTS config
        if "_tts_cfg" in st.session_state:
            del st.session_state._tts_cfg

    except Exception as e:
        print(f"Error cleaning up audio resources: {e}")