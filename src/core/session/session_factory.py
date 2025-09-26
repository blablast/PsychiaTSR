"""Factory function for creating session manager with Streamlit."""

from typing import Optional

from .session_manager import SessionManager
from .session_state import StreamlitSessionState
from .stages.stage_manager import StageManager
from ...infrastructure.storage import StorageProvider


def create_streamlit_session_manager(
    storage_provider: Optional[StorageProvider] = None,
) -> SessionManager:
    """Create a SessionManager configured for Streamlit."""
    from config import Config

    config = Config.get_instance()
    session_state = StreamlitSessionState()
    stage_manager = StageManager(config.STAGES_DIR)

    return SessionManager(session_state, stage_manager, storage_provider)
