"""Service registration for dependency injection container."""

from config import Config
from .container import DependencyContainer, ServiceLifetime
from ..config.config_manager import ConfigManager
from ...infrastructure.storage import StorageProvider
from ...core.safety import SafetyChecker
from ..session.stages.stage_manager import StageManager
from ..session.session_state import StreamlitSessionState


class ServiceRegistry:
    """Handles registration of all application services."""

    @staticmethod
    def register_core_services(container: DependencyContainer) -> None:
        """Register core application services."""

        # Configuration services
        from config import Config
        config = Config.get_instance()
        container.register_instance(Config, config)
        container.register(ConfigManager, ConfigManager, ServiceLifetime.SINGLETON)

        # Specialized config classes (updated paths)
        from ..config.loaders.base_loader import BaseLoader
        from ..config.loaders.environment_loader import EnvironmentLoader
        from ..config.loaders.agent_loader import AgentLoader
        from ..config.loaders.app_loader import AppLoader
        from ..config.loaders.directory_loader import DirectoryLoader

        container.register(BaseLoader, BaseLoader, ServiceLifetime.SINGLETON)
        container.register(EnvironmentLoader, EnvironmentLoader, ServiceLifetime.SINGLETON)

        # Config classes that need config data
        def create_agent_loader():
            base_loader = container.resolve(BaseLoader)
            return AgentLoader(base_loader.get_config_data())

        def create_app_loader():
            base_loader = container.resolve(BaseLoader)
            return AppLoader(base_loader.get_config_data())

        def create_directory_loader():
            base_loader = container.resolve(BaseLoader)
            return DirectoryLoader(base_loader.get_config_data())

        container.register_factory(AgentLoader, create_agent_loader, ServiceLifetime.SINGLETON)
        container.register_factory(AppLoader, create_app_loader, ServiceLifetime.SINGLETON)
        container.register_factory(DirectoryLoader, create_directory_loader, ServiceLifetime.SINGLETON)

        # Logging services
        from ..logging.interfaces.logger_interface import ILogger
        from ..logging.logger_factory import LoggerFactory

        container.register_factory(
            ILogger,
            lambda: LoggerFactory.create_default(),
            ServiceLifetime.SINGLETON
        )

        # Storage and safety services
        container.register_factory(
            StorageProvider,
            lambda: StorageProvider(Config.get_instance().LOGS_DIR),
            ServiceLifetime.SINGLETON
        )
        container.register(SafetyChecker, SafetyChecker, ServiceLifetime.SINGLETON)

        # Stage management
        container.register_factory(
            StageManager,
            lambda: StageManager(Config.get_instance().STAGES_DIR),
            ServiceLifetime.SINGLETON
        )

        # Session state (Streamlit specific)
        container.register(StreamlitSessionState, StreamlitSessionState, ServiceLifetime.SINGLETON)

    @staticmethod
    def register_agent_services(container: DependencyContainer) -> None:
        """Register agent-related services."""
        from ..prompts.unified_prompt_manager import UnifiedPromptManager
        from ..services.prompt_service import PromptService
        from ..services.parsing_service import ParsingService
        from ..services.safety_service import SafetyService
        from ..services.memory_service import MemoryService

        # Prompt management - use factory to provide the directory parameter
        container.register_factory(
            UnifiedPromptManager,
            lambda: UnifiedPromptManager(Config.get_instance().PROMPT_DIR),
            ServiceLifetime.SINGLETON
        )

        # Agent services - these will automatically resolve ILogger through DI
        container.register(PromptService, PromptService, ServiceLifetime.TRANSIENT)
        container.register(ParsingService, ParsingService, ServiceLifetime.TRANSIENT)
        container.register(SafetyService, SafetyService, ServiceLifetime.TRANSIENT)
        container.register(MemoryService, MemoryService, ServiceLifetime.TRANSIENT)

    @staticmethod
    def register_session_services(container: DependencyContainer) -> None:
        """Register session management services."""
        from ..session.session_manager import SessionManager
        from ..conversation.conversation_manager import ConversationManager

        # Session and conversation management
        container.register(SessionManager, SessionManager, ServiceLifetime.SCOPED)
        container.register(ConversationManager, ConversationManager, ServiceLifetime.SCOPED)

        # Async workflow services
        from ..workflow.async_workflow_manager import AsyncWorkflowManager

        def create_async_workflow_manager():
            from ...ui.session.streamlit_agent_provider import StreamlitAgentProvider  # Use proper agent provider
            from ..prompts.unified_prompt_manager import UnifiedPromptManager
            from ..logging.interfaces.logger_interface import ILogger

            agent_provider = StreamlitAgentProvider()  # Use proper agent provider
            prompt_manager = container.resolve(UnifiedPromptManager)
            conversation_manager = container.resolve(ConversationManager)
            logger = container.resolve(ILogger)
            return AsyncWorkflowManager(agent_provider, prompt_manager, conversation_manager, logger)

        container.register_factory(
            AsyncWorkflowManager,
            create_async_workflow_manager,
            ServiceLifetime.SCOPED
        )

    @staticmethod
    def register_audio_services(container: DependencyContainer) -> None:
        """Register audio services."""
        try:
            from ...audio.services.audio_service import AudioService
            from ...audio.providers.elevenlabs_provider import ElevenLabsTTSProvider
            from ...audio.webrtc.streaming_manager import AudioStreamingManager

            # Register audio services
            container.register(AudioService, AudioService, ServiceLifetime.SINGLETON)
            container.register(ElevenLabsTTSProvider, ElevenLabsTTSProvider, ServiceLifetime.TRANSIENT)
            container.register(AudioStreamingManager, AudioStreamingManager, ServiceLifetime.SINGLETON)

        except ImportError:
            # Audio dependencies not available - skip registration
            pass

    @staticmethod
    def register_all_services(container: DependencyContainer) -> None:
        """Register all application services in the container."""
        ServiceRegistry.register_core_services(container)
        ServiceRegistry.register_agent_services(container)
        ServiceRegistry.register_session_services(container)
        ServiceRegistry.register_audio_services(container)

    @staticmethod
    def create_configured_container() -> DependencyContainer:
        """Create and configure a new dependency container with all services."""
        container = DependencyContainer()
        ServiceRegistry.register_all_services(container)
        return container