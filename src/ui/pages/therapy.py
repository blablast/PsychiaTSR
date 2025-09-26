"""Main therapy page for Psychia TSR"""

import streamlit as st

from config import Config
from src.core.session import load_stages
from src.ui.chat import display_chat_interface
from src.ui.technical_log_display import display_technical_log, copy_technical_logs


def therapy_page() -> None:
    """Main therapy page with chat interface and session management."""
    col1, col2, col3 = st.columns([2, 1, 1])

    from config import Config

    config = Config.get_instance()
    st.title(config.APP_TITLE)
    stages = load_stages()
    if not stages:
        st.error("Nie można wczytać etapów terapii")
        st.stop()

    if st.session_state.show_crisis_message:
        st.error(
            "⚠️ **UWAGA**: Wykryto sygnały mogące wskazywać na kryzys psychiczny. "
            "Jeśli masz myśli samobójcze lub potrzebujesz natychmiastowej pomocy, "
            "skontaktuj się z Centrum Wsparcia (116 123) lub udaj się na SOR."
        )

    st.markdown(
        """
    <style>
    .stContainer > div {
        height: calc(100vh - 200px) !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    chat_col, log_col = st.columns([1, 1])

    with chat_col:
        st.subheader("💬 Sesja terapii")

        display_chat_interface()

    with log_col:
        st.subheader("🔧 Logi techniczne")

        with st.container(height=800):
            display_technical_log()
