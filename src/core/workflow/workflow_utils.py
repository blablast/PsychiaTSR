"""Workflow management for therapy sessions."""
import os
import streamlit as st
from .workflow_manager import TherapyWorkflowManager
from ...ui.session.streamlit_agent_provider import StreamlitAgentProvider
from ..conversation import ConversationManager
from ..logging import LoggerFactory
# Agents now created via ServiceFactory with dependency injection
from ...llm import OpenAIProvider, GeminiProvider
from ...core.safety import SafetyChecker
from config import Config


def _get_or_create_session_logger():
    """Get or create a single logger instance for the session to avoid duplicates."""
    # Use a session state key to store the logger instance
    logger_key = 'therapy_session_logger'

    if logger_key not in st.session_state:
        # Create logger only once per session
        log_file = os.path.join(Config.LOGS_DIR, "sessions", f"{st.session_state.get('session_id', 'unknown')}.json")
        st.session_state[logger_key] = LoggerFactory.create_multi_logger(
            file_path=log_file,
            use_console=False,
            use_streamlit=True,
            max_entries=50
        )

    return st.session_state[logger_key]



def send_supervisor_request(user_message: str):
    """Accept user message into ConversationManager and process if ready."""
    # Get or create ConversationManager from session state
    if 'conversation_manager' not in st.session_state:
        st.session_state.conversation_manager = ConversationManager()

    conversation_manager = st.session_state.conversation_manager

    # Accept user input
    if not conversation_manager.accept_user_input(user_message):
        st.warning("Czekaj na odpowiedź terapeuty...")
        return

    # If we have a complete question, process it
    if conversation_manager.has_pending_question():
        from ..prompts.unified_prompt_manager import UnifiedPromptManager

        agent_provider = StreamlitAgentProvider()
        prompt_manager = UnifiedPromptManager(Config.PROMPT_DIR)

        # Reuse logger from session state if available, otherwise create new one
        logger = _get_or_create_session_logger()

        workflow_manager = TherapyWorkflowManager(
            agent_provider, prompt_manager, conversation_manager, logger
        )

        # Initialize workflow orchestrator with session manager
        from ..session import create_streamlit_session_manager
        session_manager = create_streamlit_session_manager()
        workflow_manager.set_session_manager(session_manager)

        result = workflow_manager.process_pending_question()

        if not result.success:
            st.error(result.message)
        elif result.data:
            # Update UI state
            if result.data.get("stage_changed"):
                st.success(f"🎯 **ZMIANA ETAPU → {result.data['current_stage']}**")


def initialize_agents():
    """Initialize therapy agents with default configuration."""

    def assign_llm(provider_name, model_name, keys):
        if provider_name == 'openai':
            return OpenAIProvider(model_name, api_key=keys['openai'])
        elif provider_name == 'gemini':
            return GeminiProvider(model_name, api_key=keys['gemini'])
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

    try:
        # Initialize LLM providers based on configuration
        agent_defaults = Config.get_agent_defaults()

        # Prepare API keys
        api_keys = {
            'openai': Config.OPENAI_API_KEY,
            'gemini': Config.GOOGLE_API_KEY
        }

        # Initialize therapist LLM
        therapist_llm = assign_llm(agent_defaults['therapist']['provider'],
                                   agent_defaults['therapist']['model'],
                                   api_keys)

        # Initialize supervisor LLM
        supervisor_llm = assign_llm(agent_defaults['supervisor']['provider'],
                                      agent_defaults['supervisor']['model'],
                                     api_keys)

        # Reuse logger from session state if available, otherwise create new one
        logger = _get_or_create_session_logger()

        # Initialize agents using new ServiceFactory architecture
        from ..prompts.unified_prompt_manager import UnifiedPromptManager
        from ..services import ServiceFactory

        safety_checker = SafetyChecker()
        prompt_manager = UnifiedPromptManager(Config.PROMPT_DIR)

        # Create agents with dependency injection
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

        # Check availability in background (non-blocking)
        # If models are not available, errors will show when trying to use them
        # Note: Model info already logged during session creation

        return True

    except Exception as e:
        st.error(f"Agent initialization failed: {str(e)}")
        return False


def send_supervisor_request_stream(user_message: str):
    """Accept user message into ConversationManager and process with streaming if ready."""
    # Get or create ConversationManager from session state
    if 'conversation_manager' not in st.session_state:
        st.session_state.conversation_manager = ConversationManager()

    conversation_manager = st.session_state.conversation_manager

    # Accept user input for processing
    if not conversation_manager.accept_user_input(user_message):
        st.warning("Czekaj na odpowiedź terapeuty...")
        return

    # If we have a complete question, process it with streaming
    if conversation_manager.has_pending_question():
        from ..prompts.unified_prompt_manager import UnifiedPromptManager

        agent_provider = StreamlitAgentProvider()
        prompt_manager = UnifiedPromptManager(Config.PROMPT_DIR)

        # Reuse logger from session state if available, otherwise create new one
        logger = _get_or_create_session_logger()

        workflow_manager = TherapyWorkflowManager(
            agent_provider, prompt_manager, conversation_manager, logger
        )

        # Initialize workflow orchestrator with session manager
        from ..session import create_streamlit_session_manager
        session_manager = create_streamlit_session_manager()
        workflow_manager.set_session_manager(session_manager)

        # Process with streaming
        yield from workflow_manager.process_pending_question_stream()


__all__ = [
    'send_supervisor_request',
    'send_supervisor_request_stream',
    'initialize_agents'
]