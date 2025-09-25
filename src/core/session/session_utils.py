"""Session management for therapy sessions."""

import streamlit as st
from datetime import datetime
from .stages.stage_manager import StageManager
from .session_factory import create_streamlit_session_manager
from ..logging import LoggerFactory
from config import Config


def load_stages():
    """Load therapy stages from configuration."""
    stage_manager = StageManager(Config.STAGES_DIR)
    stages = stage_manager.get_all_stages()

    return [
        {
            "id": stage.stage_id,
            "name": stage.name,
            "order": stage.order,
            "description": stage.description or ""
        }
        for stage in stages
    ]


def create_new_session():
    """Create new therapy session with current models."""
    # Clear technical logs for new session
    _clear_technical_logs()

    session_manager = create_streamlit_session_manager()
    try:
        from src.infrastructure.storage import StorageProvider
        storage = StorageProvider(Config.LOGS_DIR)
        session_manager._storage_provider = storage
        session_id = session_manager.create_new_session()

        # Log current model configuration to logs directory
        import os
        logs_dir = os.path.join("logs", session_id)
        os.makedirs(logs_dir, exist_ok=True)
        log_file = os.path.join(logs_dir, "session.json")

        logger = LoggerFactory.create_multi_logger(
            file_path=log_file,
            use_console=False,
            use_streamlit=True,
            max_entries=50
        )

        # Get current models from session state or defaults
        agent_defaults = Config.get_agent_defaults()
        therapist_model = st.session_state.get('selected_therapist_model', agent_defaults['therapist']['model'])
        supervisor_model = st.session_state.get('selected_supervisor_model', agent_defaults['supervisor']['model'])
        therapist_provider = st.session_state.get('selected_therapist_provider', agent_defaults['therapist']['provider'])
        supervisor_provider = st.session_state.get('selected_supervisor_provider', agent_defaults['supervisor']['provider'])

        logger.log_model_info(
            therapist_model=therapist_model,
            supervisor_model=supervisor_model,
            therapist_provider=therapist_provider,
            supervisor_provider=supervisor_provider
        )

        # Save model information to session metadata
        storage.update_session_models(
            session_id=session_id,
            therapist_model=therapist_model,
            supervisor_model=supervisor_model,
            therapist_provider=therapist_provider,
            supervisor_provider=supervisor_provider
        )

        # Save current audio configuration to session
        _save_current_audio_config_to_session(session_id, storage)

        # Add initial stage message as first chat message
        _add_initial_stage_message()

        # Also save session data to logs directory
        session_data = storage.load_session(session_id)
        if session_data:
            storage.save_session_log(session_id, session_data)

        st.success(f"Nowa sesja utworzona: {session_id}")
        return session_id
    except Exception as e:
        st.error(f"Błąd tworzenia sesji: {str(e)}")
        return None


def advance_stage(direction="next"):
    """Advance therapy stage in given direction."""
    session_manager = create_streamlit_session_manager()

    if direction == "next":
        result = session_manager.advance_to_next_stage()
    else:
        result = session_manager.retreat_to_previous_stage()

    if result.success:
        st.success(result.message)
    else:
        st.error(result.message)

    return result.success


def format_timestamp(timestamp):
    """Format timestamp for display."""
    if not timestamp:
        return ""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp


def get_configured_models():
    """Get configured models from config."""
    agent_defaults = Config.get_agent_defaults()
    return {
        'therapist_model': agent_defaults['therapist']['model'],
        'therapist_provider': agent_defaults['therapist']['provider'],
        'supervisor_model': agent_defaults['supervisor']['model'],
        'supervisor_provider': agent_defaults['supervisor']['provider']
    }


def _add_initial_stage_message():
    """Add initial stage welcome message to chat."""
    stages = load_stages()
    current_stage_info = next((stage for stage in stages if stage["id"] == st.session_state.current_stage), None)

    if current_stage_info:
        stage_name = current_stage_info['name']
        stage_order = current_stage_info['order']

        welcome_message = f"🎯 **Witaj w terapii TSR (Terapia Skoncentrowana na Rozwiązaniach)**\n\n**Rozpoczynamy od Etapu {stage_order}: {stage_name}**\n\nJestem Twoim terapeutą i będę prowadził z Tobą sesję używając technik specyficznych dla tego etapu. Możesz śmiało dzielić się swoimi myślami i uczuciami."

        # Initialize messages if not exists
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Add as first message
        st.session_state.messages.insert(0, {
            "role": "assistant",
            "content": welcome_message,
            "timestamp": "",
            "is_stage_transition": True
        })


def load_audio_config_from_session():
    """Load audio configuration from current session."""
    # NOTE: This function is now deprecated - audio config is loaded from app config in SessionStateInitializer
    pass


def save_audio_config_to_session():
    """Save current audio configuration to session."""
    # NOTE: This function is now deprecated - audio config is saved to app config in conversation_settings
    pass


def _save_current_audio_config_to_session(session_id: str, storage):
    """Save current session state audio config to session file."""
    audio_enabled = st.session_state.get('audio_enabled', False)
    tts_config = st.session_state.get('_tts_cfg')

    if audio_enabled or tts_config:
        storage.update_audio_config(
            session_id=session_id,
            audio_enabled=audio_enabled,
            tts_config=tts_config
        )


def _clear_technical_logs():
    """Clear technical logs from session state when creating new session."""
    import streamlit as st

    # Clear the technical log session state
    if "technical_log" in st.session_state:
        st.session_state["technical_log"] = []

    # Log that logs were cleared
    from src.ui.technical_log_display import add_technical_log
    add_technical_log("session_start", "🆕 Nowa sesja - logi wyczyszczone")


__all__ = [
    'load_stages',
    'create_new_session',
    'advance_stage',
    'format_timestamp',
    'get_configured_models',
    'load_audio_config_from_session',
    'save_audio_config_to_session'
]