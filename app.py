"""Main Streamlit application for Psychia TSR - Modularized version"""

import streamlit as st

from src.core.application.environment_setup import EnvironmentSetup
from src.ui.application.page_configurator import PageConfigurator
from src.core.application.user_config_loader import UserConfigLoader
from src.ui.session.session_state_initializer import SessionStateInitializer
from src.ui.application.page_router import PageRouter
from src.ui.sidebar import display_sidebar

# Initialize environment
EnvironmentSetup.initialize()

# Configure page
PageConfigurator.configure()

# Load user configuration
UserConfigLoader().load_and_apply_config()

# Initialize session state
SessionStateInitializer.initialize()


def main():
    """Main Streamlit application with navigation"""

    # Display sidebar navigation
    display_sidebar()

    # Get current page from session state
    current_page = st.session_state.get("current_page", "conversation")

    # Route to appropriate page
    if current_page == "conversation":
        from src.ui.pages.therapy import therapy_page

        therapy_page()
    elif current_page == "prompts":
        from src.ui.pages.prompts_unified import prompts_unified_page

        prompts_unified_page()
    elif current_page == "settings":
        from src.ui.pages.conversation_settings import display_conversation_settings

        display_conversation_settings()
    elif current_page == "reports":
        _display_reports_page()
    elif current_page == "tests":
        _display_tests_page()
    else:
        # Default to conversation
        from src.ui.pages.therapy import therapy_page

        therapy_page()


def _display_reports_page():
    """Display reports and analytics page."""
    import streamlit as st

    st.title("📊 Raporty i Statystyki")
    st.info("🚧 Ta strona jest w trakcie rozwoju...")
    st.markdown(
        """
    ### Planowane funkcje:
    - 📈 Statystyki sesji terapeutycznych
    - 📋 Raporty z użycia modeli AI
    - 🔍 Analiza skuteczności terapii
    - 📊 Wykresy postępu pacjentów
    """
    )


def _display_tests_page():
    """Display testing and development page."""
    import streamlit as st

    st.title("🔬 Testy i Rozwój")

    # Test page selection
    test_option = st.selectbox(
        "Wybierz moduł testowy:", ["Testy Modeli", "Testy Promptów", "Eksport Danych", "Inne Testy"]
    )

    if test_option == "Testy Modeli":
        from src.ui.pages.model_test import model_test_page

        model_test_page()
    elif test_option == "Testy Promptów":
        from src.ui.pages.prompts_new import prompts_management_page

        prompts_management_page()
    elif test_option == "Eksport Danych":
        from src.ui.pages.export import export_page

        export_page()
    else:
        from src.ui.pages.testing import testing_page

        testing_page()


if __name__ == "__main__":
    main()
