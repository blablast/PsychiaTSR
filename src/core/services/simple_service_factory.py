"""Simple service factory - replaces over-engineered DI container."""

from typing import Dict, Any, Optional, TypeVar, Type
from functools import lru_cache
from pathlib import Path

# NOTE: Config import removed to avoid circular dependency

# Import services that need to be created
from ..logging.interfaces.logger_interface import ILogger
from ..logging.logger_factory import LoggerFactory
from ...infrastructure.storage.storage import StorageProvider
from ..safety.safety import SafetyChecker
from ..session.stages.stage_manager import StageManager
from ..session.session_state import StreamlitSessionState

T = TypeVar("T")


class SimpleServiceFactory:
    """
    Simple service factory using factory pattern instead of complex DI.

    Eliminates over-engineering by:
    - Single responsibility: just create services
    - No complex lifetimes, scopes, or hierarchies
    - Direct method calls instead of reflection
    - Singletons via @lru_cache where needed
    - Easy to test and understand
    """

    # =====================================================================================
    # CONFIGURATION SERVICES
    # =====================================================================================

    @staticmethod
    def get_config():
        """Get Config instance - import here to avoid circular dependency."""
        from config import Config

        return Config.get_instance()

    # =====================================================================================
    # CORE SERVICES
    # =====================================================================================

    @staticmethod
    @lru_cache(maxsize=1)
    def create_logger() -> ILogger:
        """Create default logger (singleton)."""
        return LoggerFactory.create_default()

    @staticmethod
    @lru_cache(maxsize=1)
    def create_storage_provider() -> StorageProvider:
        """Create storage provider (singleton)."""
        config = SimpleServiceFactory.get_config()
        return StorageProvider(config.LOGS_DIR)

    @staticmethod
    @lru_cache(maxsize=1)
    def create_safety_checker() -> SafetyChecker:
        """Create safety checker (singleton)."""
        return SafetyChecker()

    @staticmethod
    @lru_cache(maxsize=1)
    def create_stage_manager() -> StageManager:
        """Create stage manager (singleton)."""
        config = SimpleServiceFactory.get_config()
        return StageManager(config.STAGES_DIR)

    @staticmethod
    def create_session_state() -> StreamlitSessionState:
        """Create session state (transient - new instance each time)."""
        return StreamlitSessionState()

    # =====================================================================================
    # PROMPT MANAGEMENT SERVICES
    # =====================================================================================

    @staticmethod
    @lru_cache(maxsize=1)
    def create_prompt_management_service():
        """Create prompt management service (singleton)."""
        from ..prompts.prompt_management_service import PromptManagementService

        config = SimpleServiceFactory.get_config()
        logger = SimpleServiceFactory.create_logger()
        return PromptManagementService(config.PROMPT_DIR, logger)

    # =====================================================================================
    # AGENT SERVICES (transient - new instance each time for session isolation)
    # =====================================================================================

    @staticmethod
    def create_prompt_service():
        """Create prompt service (transient)."""
        from ..services.prompt_service import PromptService
        from ..prompts.unified_prompt_manager import UnifiedPromptManager

        config = SimpleServiceFactory.get_config()
        prompt_manager = UnifiedPromptManager(config.PROMPT_DIR)
        return PromptService(prompt_manager)

    @staticmethod
    def create_parsing_service():
        """Create parsing service (transient)."""
        from ..services.parsing_service import ParsingService

        logger = SimpleServiceFactory.create_logger()
        return ParsingService(logger)

    @staticmethod
    def create_safety_service():
        """Create safety service (transient)."""
        from ..services.safety_service import SafetyService

        safety_checker = SimpleServiceFactory.create_safety_checker()
        return SafetyService(safety_checker)

    @staticmethod
    def create_memory_service():
        """Create memory service (transient)."""
        from ..services.memory_service import MemoryService

        logger = SimpleServiceFactory.create_logger()
        return MemoryService(logger)

    # =====================================================================================
    # SESSION MANAGEMENT SERVICES
    # =====================================================================================

    @staticmethod
    def create_session_manager():
        """Create session manager (transient - per session)."""
        from ..session.session_manager import SessionManager

        storage = SimpleServiceFactory.create_storage_provider()
        logger = SimpleServiceFactory.create_logger()
        return SessionManager(storage, logger)

    @staticmethod
    def create_conversation_manager():
        """Create conversation manager (transient - per session)."""
        from ..conversation.conversation_manager import ConversationManager

        logger = SimpleServiceFactory.create_logger()
        return ConversationManager(logger)

    # =====================================================================================
    # WORKFLOW SERVICES
    # =====================================================================================

    @staticmethod
    def create_workflow_manager():
        """Create workflow manager (transient - per session)."""
        from ..workflow.workflow_manager import WorkflowManager

        logger = SimpleServiceFactory.create_logger()
        return WorkflowManager(logger)

    @staticmethod
    def create_async_workflow_manager():
        """Create async workflow manager (transient - per session)."""
        from ..workflow.async_workflow_manager import AsyncWorkflowManager
        from ...ui.session.streamlit_agent_provider import StreamlitAgentProvider

        agent_provider = StreamlitAgentProvider()
        prompt_manager = SimpleServiceFactory.create_prompt_management_service()
        conversation_manager = SimpleServiceFactory.create_conversation_manager()
        logger = SimpleServiceFactory.create_logger()

        return AsyncWorkflowManager(agent_provider, prompt_manager, conversation_manager, logger)

    # =====================================================================================
    # AUDIO SERVICES (optional)
    # =====================================================================================

    @staticmethod
    @lru_cache(maxsize=1)
    def create_audio_service():
        """Create audio service (singleton)."""
        try:
            from ...audio.services.audio_service import AudioService

            return AudioService()
        except ImportError:
            return None

    @staticmethod
    def create_elevenlabs_provider():
        """Create ElevenLabs TTS provider (transient)."""
        try:
            from ...audio.providers.elevenlabs_provider import ElevenLabsTTSProvider

            return ElevenLabsTTSProvider()
        except ImportError:
            return None

    @staticmethod
    @lru_cache(maxsize=1)
    def create_audio_streaming_manager():
        """Create audio streaming manager (singleton)."""
        try:
            from ...audio.webrtc.streaming_manager import AudioStreamingManager

            return AudioStreamingManager()
        except ImportError:
            return None

    # =====================================================================================
    # UTILITY METHODS
    # =====================================================================================

    @staticmethod
    def create_agent_services() -> Dict[str, Any]:
        """Create a complete set of agent services for a session."""
        return {
            "prompt_service": SimpleServiceFactory.create_prompt_service(),
            "parsing_service": SimpleServiceFactory.create_parsing_service(),
            "safety_service": SimpleServiceFactory.create_safety_service(),
            "memory_service": SimpleServiceFactory.create_memory_service(),
            "logger": SimpleServiceFactory.create_logger(),
        }

    @staticmethod
    def create_session_services() -> Dict[str, Any]:
        """Create a complete set of session services."""
        return {
            "session_manager": SimpleServiceFactory.create_session_manager(),
            "conversation_manager": SimpleServiceFactory.create_conversation_manager(),
            "workflow_manager": SimpleServiceFactory.create_workflow_manager(),
            "storage": SimpleServiceFactory.create_storage_provider(),
            "safety_checker": SimpleServiceFactory.create_safety_checker(),
            "stage_manager": SimpleServiceFactory.create_stage_manager(),
            "logger": SimpleServiceFactory.create_logger(),
        }

    @staticmethod
    def clear_cache() -> None:
        """Clear cached singleton instances (useful for testing)."""
        SimpleServiceFactory.get_config.cache_clear()
        SimpleServiceFactory.create_logger.cache_clear()
        SimpleServiceFactory.create_storage_provider.cache_clear()
        SimpleServiceFactory.create_safety_checker.cache_clear()
        SimpleServiceFactory.create_stage_manager.cache_clear()
        SimpleServiceFactory.create_prompt_management_service.cache_clear()

        # Clear audio services cache if they exist
        if hasattr(SimpleServiceFactory.create_audio_service, "cache_clear"):
            SimpleServiceFactory.create_audio_service.cache_clear()
        if hasattr(SimpleServiceFactory.create_audio_streaming_manager, "cache_clear"):
            SimpleServiceFactory.create_audio_streaming_manager.cache_clear()

    @staticmethod
    def validate_services() -> Dict[str, bool]:
        """Validate that all core services can be created."""
        validation_results = {}

        core_services = [
            "config",
            "logger",
            "storage_provider",
            "safety_checker",
            "stage_manager",
            "prompt_management_service",
        ]

        for service_name in core_services:
            try:
                method_name = f"create_{service_name}" if service_name != "config" else "get_config"
                method = getattr(SimpleServiceFactory, method_name)
                instance = method()
                validation_results[service_name] = instance is not None
            except Exception as e:
                validation_results[service_name] = False

        return validation_results


# =====================================================================================
# BACKWARDS COMPATIBILITY - ServiceLocator-like interface
# =====================================================================================


class ServiceLocator:
    """
    Backwards compatibility facade for existing ServiceLocator usage.

    Delegates to SimpleServiceFactory for actual service creation.
    """

    # Mapping from type/class to factory method
    _service_map = {
        "Config": "get_config",
        "ILogger": "create_logger",
        "StorageProvider": "create_storage_provider",
        "SafetyChecker": "create_safety_checker",
        "StageManager": "create_stage_manager",
        "StreamlitSessionState": "create_session_state",
        "PromptService": "create_prompt_service",
        "ParsingService": "create_parsing_service",
        "SafetyService": "create_safety_service",
        "MemoryService": "create_memory_service",
        "SessionManager": "create_session_manager",
        "ConversationManager": "create_conversation_manager",
        "WorkflowManager": "create_workflow_manager",
        "AsyncWorkflowManager": "create_async_workflow_manager",
    }

    @classmethod
    def resolve(cls, service_type: Type[T]) -> T:
        """Resolve service by type (backwards compatibility)."""
        service_name = service_type.__name__

        if service_name in cls._service_map:
            method_name = cls._service_map[service_name]
            method = getattr(SimpleServiceFactory, method_name)
            return method()

        raise ValueError(f"Service {service_name} is not registered in SimpleServiceFactory")

    @classmethod
    def initialize(cls) -> None:
        """Initialize services (backwards compatibility - does nothing)."""
        pass

    @classmethod
    def create_scope(cls):
        """Create scope (backwards compatibility - returns self)."""
        return cls
