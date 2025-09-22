"""Workflow management for therapy sessions."""
import os
import streamlit as st
from .workflow_manager import TherapyWorkflowManager
from ..agents.agent_provider import StreamlitAgentProvider
from ..session.session_factory import create_streamlit_session_manager
from ..logging.logger_factory import LoggerFactory
from ...agents import TherapistAgent, SupervisorAgent
from ...llm import OpenAIProvider, GeminiProvider
from ...utils.safety import SafetyChecker
from config import Config



def send_supervisor_request(user_message: str):
    """Send supervisor request and process user message through therapy workflow."""
    from ..prompts.unified_prompt_manager import UnifiedPromptManager

    agent_provider = StreamlitAgentProvider()
    prompt_manager = UnifiedPromptManager(Config.PROMPT_DIR)
    session_manager = create_streamlit_session_manager()

    # Create dual logger that saves to both UI and file
    log_file = os.path.join(Config.DATA_DIR, "therapy_logs", f"session_{st.session_state.get('session_id', 'unknown')}.json")
    logger = LoggerFactory.create_dual_logger(log_file)

    workflow_manager = TherapyWorkflowManager(
        agent_provider, prompt_manager, session_manager, logger
    )

    result = workflow_manager.process_user_message(user_message)

    if not result.success:
        st.error(result.message)
    elif result.data:
        # Update UI state
        if result.data.get("stage_changed"):
            # Just show success message (stage transition message is added by workflow manager)
            from ..session import load_stages
            stages = load_stages()
            current_stage_info = next((stage for stage in stages if stage["id"] == result.data['current_stage']), None)

            if current_stage_info:
                stage_name = current_stage_info['name']
                stage_order = current_stage_info['order']
                st.success(f"🎯 **ZMIANA ETAPU → Etap {stage_order}: {stage_name}**")
            else:
                st.success(f"🎯 **ZMIANA ETAPU → {result.data['current_stage']}**")


def initialize_agents():
    """Initialize therapy agents with default configuration."""

    def assign_llm(provider_name, model_name, api_keys):
        if provider_name == 'openai':
            return OpenAIProvider(model_name, api_key=api_keys['openai'])
        elif provider_name == 'gemini':
            return GeminiProvider(model_name, api_key=api_keys['gemini'])
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

        # Initialize agents
        safety_checker = SafetyChecker()
        st.session_state.therapist_agent = TherapistAgent(therapist_llm, safety_checker)
        st.session_state.supervisor_agent = SupervisorAgent(supervisor_llm, safety_checker)

        # Check availability in background (non-blocking)
        # If models are not available, errors will show when trying to use them

        # Log model information
        log_file = os.path.join(Config.DATA_DIR, "therapy_logs", f"session_{st.session_state.get('session_id', 'unknown')}.json")
        logger = LoggerFactory.create_dual_logger(log_file)
        agent_defaults = Config.get_agent_defaults()
        logger.log_model_info(
            therapist_model=agent_defaults['therapist']['model'],
            supervisor_model=agent_defaults['supervisor']['model'],
            therapist_provider=agent_defaults['therapist']['provider'],
            supervisor_provider=agent_defaults['supervisor']['provider']
        )

        return True

    except Exception as e:
        st.error(f"Agent initialization failed: {str(e)}")
        return False


__all__ = [
    'send_supervisor_request',
    'initialize_agents'
]