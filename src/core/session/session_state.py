"""Streamlit-based session state implementation."""

import streamlit as st
from typing import List, Dict, Any, Optional

from .interfaces.session_state_interface import ISessionState


class StreamlitSessionState(ISessionState):
    """Streamlit-based session state implementation."""

    def get_session_id(self) -> Optional[str]:
        return st.session_state.get('session_id')

    def set_session_id(self, session_id: str) -> None:
        st.session_state.session_id = session_id

    def get_current_stage(self) -> str:
        current_stage = st.session_state.get('current_stage')
        if not current_stage:
            # Get first stage dynamically
            from .stages.stage_manager import StageManager
            from config import Config
            config = Config.get_instance()
            stage_manager = StageManager(config.STAGES_DIR)
            first_stage = stage_manager.get_first_stage()
            current_stage = first_stage.stage_id if first_stage else "opening"
            # Cache it
            st.session_state.current_stage = current_stage
        return current_stage

    def set_current_stage(self, stage: str) -> None:
        st.session_state.current_stage = stage

    def get_messages(self) -> List[Dict[str, Any]]:
        return st.session_state.get('messages', [])

    def add_message(self, message: Dict[str, Any]) -> None:
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        st.session_state.messages.append(message)

    def clear_messages(self) -> None:
        st.session_state.messages = []