"""Sidebar functionality for Psychia TSR"""

import streamlit as st
from src.core.session import create_new_session
from src.ui.llm_config import display_llm_config


def display_sidebar():
    """Display sidebar with session controls and basic info"""
    with st.sidebar:
        st.title("🧠 Psychia TSR")

        # Session controls
        st.subheader("Sesja")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🆕 Nowa", use_container_width=True):
                create_new_session()
                st.rerun()

        with col2:
            if st.button("🔄 Reset", use_container_width=True):
                # Reset session state
                for key in ["messages", "session_id", "current_stage", "show_crisis_message"]:
                    if key in st.session_state:
                        if key == "current_stage":
                            from src.core.stages import StageManager
                            from config import Config
                            stage_manager = StageManager(Config.STAGES_DIR)
                            first_stage = stage_manager.get_first_stage()
                            st.session_state[key] = first_stage.stage_id if first_stage else "opening"
                        elif key == "show_crisis_message":
                            st.session_state[key] = False
                        else:
                            st.session_state[key] = [] if key == "messages" else None
                st.success("Sesja zresetowana")
                st.rerun()

        # Current session info
        if st.session_state.session_id:
            st.info(f"**ID:** {st.session_state.session_id}")


        # LLM Configuration
        st.divider()
        model_config = display_llm_config()


        # Apply model changes button
        if model_config and model_config.get('therapist_model') and model_config.get('supervisor_model'):
            if st.button("✅ Zastosuj wybrane modele", use_container_width=True):
                therapist_info = model_config['therapist_model']
                supervisor_info = model_config['supervisor_model']

                # Store selected models in session state
                st.session_state.selected_therapist_provider = therapist_info['provider']
                st.session_state.selected_therapist_model = therapist_info['model_id']
                st.session_state.selected_supervisor_provider = supervisor_info['provider']
                st.session_state.selected_supervisor_model = supervisor_info['model_id']

                # Clear existing agents to force reinitialization
                st.session_state.therapist_agent = None
                st.session_state.supervisor_agent = None

                # Create logger for agents and model info
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
                        from src.utils.storage import StorageProvider
                        from config import Config
                        storage = StorageProvider(Config.DATA_DIR)
                        storage.update_session_models(
                            session_id=st.session_state.session_id,
                            therapist_model=therapist_info['model_id'],
                            supervisor_model=supervisor_info['model_id'],
                            therapist_provider=therapist_info['provider'],
                            supervisor_provider=supervisor_info['provider']
                        )

                    st.success(f"✅ Modele zastosowane i zapisane jako domyślne!\n\n**Terapeuta:** {therapist_info['name']}\n**Nadzorca:** {supervisor_info['name']}")
                    st.rerun()
                else:
                    st.error("❌ Błąd inicjalizacji wybranych modeli")


def _initialize_agents_with_selected_models(logger=None):
    """Initialize agents with user-selected models and providers."""
    try:
        from src.llm import OpenAIProvider, GeminiProvider
        from src.agents import TherapistAgent, SupervisorAgent
        from src.utils.safety import SafetyChecker
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



