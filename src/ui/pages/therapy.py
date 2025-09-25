"""Main therapy page for Psychia TSR"""

import streamlit as st

from config import Config
from src.core.session import load_stages
from src.ui.chat import display_chat_interface
from src.ui.technical_log_display import display_technical_log, copy_technical_logs


def therapy_page() -> None:
    """Main therapy page with chat interface and session management."""
    # Session controls at the top
    col1, col2, col3 = st.columns([2, 1, 1])

    # with col1:
    from config import Config
    config = Config.get_instance()
    st.title(config.APP_TITLE)

    # with col2:
    #     if st.button("🆕 Nowa sesja", use_container_width=True, help="Rozpocznij nową sesję terapeutyczną"):
    #         from src.core.session import create_new_session
    #         create_new_session()
    #         st.success("🎉 Utworzono nową sesję!")
    #         st.rerun()

    # Reset button removed - sessions now persist properly

    # Session info
    # if st.session_state.get("session_id"):
    #     st.info(f"🔗 **Sesja aktywna:** {st.session_state.session_id}")
    # else:
    #     st.warning("⚠️ **Brak aktywnej sesji** - kliknij 'Nowa sesja' aby rozpocząć")

    # Agents will be initialized lazily when first message is sent
    
    # Load stages
    stages = load_stages()
    if not stages:
        st.error("Nie można wczytać etapów terapii")
        st.stop()
    
    # Crisis warning
    if st.session_state.show_crisis_message:
        st.error("⚠️ **UWAGA**: Wykryto sygnały mogące wskazywać na kryzys psychiczny. "
                "Jeśli masz myśli samobójcze lub potrzebujesz natychmiastowej pomocy, "
                "skontaktuj się z Centrum Wsparcia (116 123) lub udaj się na SOR.")
    
    # Custom CSS for full height containers
    st.markdown("""
    <style>
    .stContainer > div {
        height: calc(100vh - 200px) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Layout: chat on left, technical log on right (50/50 split)
    chat_col, log_col = st.columns([1, 1])

    with chat_col:
        st.subheader("💬 Sesja terapii")

        # Display chat interfaces (full page height)
        display_chat_interface()

        # Stage control below chat
        #from src.ui.chat import display_stage_controls
        #display_stage_controls()

    # Technical log in right column
    with log_col:
        st.subheader("🔧 Logi techniczne")

        # Create scrollable container for technical logs with auto-scroll
        with st.container(height=800):
            display_technical_log()

        # # Controls row below logs
        # col1, col2 = st.columns([1, 1])
        # with col1:
        #     if st.button("🗑️ Wyczyść logi"):
        #         st.session_state.technical_log = []
        #         st.rerun()
        # with col2:
        #     if st.button("📋 Skopiuj logi"):
        #         copy_technical_logs()
        #
        #     # Add JavaScript for auto-scroll to bottom
        #     st.markdown("""
        #     <script>
        #     // Auto-scroll to bottom of log container
        #     setTimeout(function() {
        #         var containers = document.querySelectorAll('[data-testid="stVerticalBlock"]');
        #         if (containers.length > 0) {
        #             var lastContainer = containers[containers.length - 1];
        #             lastContainer.scrollTop = lastContainer.scrollHeight;
        #         }
        #     }, 100);
        #     </script>
        #     """, unsafe_allow_html=True)


# _reset_session function removed - sessions now persist properly without reset option