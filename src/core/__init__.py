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
    WorkflowResult,
    WorkflowOrchestrator,
    WorkflowFactory,
)

# Agent Session Management (moved to UI layer)

# Conversation Management
from .conversation import ConversationManager

# Logging System
from .logging import (
    LoggerFactory,
    BaseLogger,
    ILogger,
    IFormatter,
    IStorage,
    LogEntry,
    JsonFormatter,
    TextFormatter,
    FileStorage,
    ConsoleStorage,
    MemoryStorage,
    CompositeStorage,
)

# Models
from .models import SessionInfo, Language



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


    # Prompt Management
    'SystemPromptManager',
    'StagePromptManager',
    'UnifiedPromptManager',

    # Workflow Management
    'TherapyWorkflowManager',
    'send_supervisor_request',
    'initialize_agents',
    'WorkflowResult',
    'WorkflowOrchestrator',
    'WorkflowFactory',

    # Agent Session Management (moved to UI layer)

    # Conversation Management
    'ConversationManager',

    # Logging System
    'LoggerFactory',
    'BaseLogger',
    'ILogger',
    'IFormatter',
    'IStorage',
    'LogEntry',
    'JsonFormatter',
    'TextFormatter',
    'FileStorage',
    'ConsoleStorage',
    'MemoryStorage',
    'CompositeStorage',

    # Models
    'SessionInfo',
    'Language',

]