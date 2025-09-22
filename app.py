"""Main Streamlit application for Psychia TSR - Modularized version"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Optimize GPU memory allocation for HuggingFace models
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
from config import Config
from src.utils.storage import StorageProvider
from src.utils.safety import SafetyChecker
from src.ui.sidebar import display_sidebar
from src.ui.pages.therapy import therapy_page
from src.ui.pages.prompts import prompts_management_page
from src.ui.pages.export import export_project_page
from src.ui.pages.testing import testing_page
from src.ui.pages.model_test import model_test_page

# Page configuration
st.set_page_config(
    page_title=Config.APP_TITLE,
    page_icon=Config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for sidebar styling
st.markdown("""
<style>
    .sidebar-divider {
        border-top: 2px solid #f0f2f6;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Load user configuration
from src.core.config import ConfigManager
from src.core.models import Language
if "config_loaded" not in st.session_state:
    config_manager = ConfigManager()
    user_config = config_manager.load_config()

    # Apply configuration to session state using Config defaults
    agent_defaults = Config.get_agent_defaults()
    st.session_state.selected_therapist_model = user_config.get('providers', {}).get('therapist', {}).get('model', agent_defaults['therapist']['model'])
    st.session_state.selected_therapist_provider = user_config.get('providers', {}).get('therapist', {}).get('provider', agent_defaults['therapist']['provider'])
    st.session_state.selected_supervisor_model = user_config.get('providers', {}).get('supervisor', {}).get('model', agent_defaults['supervisor']['model'])
    st.session_state.selected_supervisor_provider = user_config.get('providers', {}).get('supervisor', {}).get('provider', agent_defaults['supervisor']['provider'])


    # Prompting strategy
    st.session_state.use_system_prompt = user_config.get('use_system_prompt', True)


    # Convert language string to Language enum
    language_code = user_config.get('language', 'pl')
    if language_code == 'pl':
        st.session_state.language = Language.POLISH
    elif language_code == 'en':
        st.session_state.language = Language.ENGLISH
    else:
        st.session_state.language = Language.POLISH  # Default fallback

    st.session_state.config_loaded = True

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_stage" not in st.session_state:
    # Get first stage dynamically from configuration
    from src.core.stages import StageManager
    from config import Config
    stage_manager = StageManager(Config.STAGES_DIR)
    first_stage = stage_manager.get_first_stage()
    st.session_state.current_stage = first_stage.stage_id if first_stage else "opening"
if "storage" not in st.session_state:
    st.session_state.storage = StorageProvider(Config.DATA_DIR)
if "safety_checker" not in st.session_state:
    st.session_state.safety_checker = SafetyChecker()
if "therapist_agent" not in st.session_state:
    st.session_state.therapist_agent = None
if "supervisor_agent" not in st.session_state:
    st.session_state.supervisor_agent = None
if "show_crisis_message" not in st.session_state:
    st.session_state.show_crisis_message = False
if "technical_log" not in st.session_state:
    st.session_state.technical_log = []
if "pending_user_message" not in st.session_state:
    st.session_state.pending_user_message = None


def main():
    """Main Streamlit application"""
    
    # Display sidebar
    display_sidebar()
    
    # Page selection
    page = st.sidebar.selectbox(
        "🔄 Wybierz stronę:",
        ["🏠 Terapia", "📝 Prompty", "🧪 Testowanie", "🤖 Test Modeli", "📦 Eksport Projektu"],
        key="page_selector"
    )

    # Route to appropriate page
    if page == "📦 Eksport Projektu":
        export_project_page()
    elif page == "📝 Prompty":
        prompts_management_page()
    elif page == "🧪 Testowanie":
        testing_page()
    elif page == "🤖 Test Modeli":
        model_test_page()
    else:  # Default to therapy page
        therapy_page()


if __name__ == "__main__":
    main()