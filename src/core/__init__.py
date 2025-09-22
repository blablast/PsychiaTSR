"""Core business logic package following SOLID principles."""

# Configuration
from .config import ConfigManager

# Session Management
from .session import (
    SessionManager,
    create_streamlit_session_manager,
    StreamlitSessionState,
    load_stages,
    create_new_session,
    get_configured_models,
    ISessionState,
)

# Stage Management
from .stages import StageManager, StageInfo

# Prompt Management
from .prompts import (
    SystemPromptManager,
    StagePromptManager,
    UnifiedPromptManager,
)

# Workflow Management
from .workflow import (
    TherapyWorkflowManager,
    send_supervisor_request,
    initialize_agents,
    SupervisorEvaluator,
    TherapistResponder,
    WorkflowResult,
)

# Agent Management
from .agents import StreamlitAgentProvider, IAgentProvider

# Logging System
from .logging import (
    LoggerFactory,
    TechnicalLogger,
    LogEntry,
    ITechnicalLogger,
    ILogStorage,
    InMemoryLogStorage,
    StreamlitLogStorage,
    FileLogStorage,
    DualLogStorage,
)

# Models
from .models import SessionInfo, Language

# Exceptions
from .exceptions import SessionManagerError, TherapyWorkflowError


__all__ = [
    # Configuration
    'ConfigManager',

    # Session Management
    'SessionManager',
    'create_streamlit_session_manager',
    'StreamlitSessionState',
    'load_stages',
    'create_new_session',
    'get_configured_models',
    'ISessionState',

    # Stage Management
    'StageManager',
    'StageInfo',

    # Prompt Management
    'SystemPromptManager',
    'StagePromptManager',
    'UnifiedPromptManager',

    # Workflow Management
    'TherapyWorkflowManager',
    'send_supervisor_request',
    'initialize_agents',
    'SupervisorEvaluator',
    'TherapistResponder',
    'WorkflowResult',

    # Agent Management
    'StreamlitAgentProvider',
    'IAgentProvider',

    # Logging System
    'LoggerFactory',
    'TechnicalLogger',
    'LogEntry',
    'ITechnicalLogger',
    'ILogStorage',
    'InMemoryLogStorage',
    'StreamlitLogStorage',
    'FileLogStorage',
    'DualLogStorage',

    # Models
    'SessionInfo',
    'Language',

    # Exceptions
    'SessionManagerError',
    'TherapyWorkflowError',
]