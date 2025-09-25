"""Factory for creating complete workflow orchestration system."""

from ..crisis.crisis_handler import CrisisHandler
from ..crisis import NoOpCrisisNotifier
from ...ui.crisis import StreamlitCrisisNotifier
from ..session.session_orchestrator import SessionOrchestrator
from ..session.stage_progression_handler import StageProgressionHandler
from .workflow_orchestrator import WorkflowOrchestrator
from .strategies.strategy_factory import WorkflowStrategyFactory


class WorkflowFactory:
    """Factory for creating complete workflow orchestration system."""

    @staticmethod
    def create_streamlit_orchestrator(agent_provider, prompt_manager, session_manager, conversation_manager, logger):
        """
        Create workflow orchestrator with Streamlit UI dependencies.

        Args:
            agent_provider: Agent provider interfaces
            prompt_manager: Prompt management service
            session_manager: Session state manager
            conversation_manager: Conversation state manager
            logger: Logger for workflow events

        Returns:
            WorkflowOrchestrator: Fully configured orchestrator
        """
        # Create UI notifier for Streamlit
        ui_notifier = StreamlitCrisisNotifier()

        # Create crisis handler
        crisis_handler = CrisisHandler(
            session_manager=session_manager,
            ui_notifier=ui_notifier,
            logger=logger
        )

        # Create session orchestration components
        stage_progression_handler = StageProgressionHandler(
            session_manager=session_manager,
            logger=logger
        )

        session_orchestrator = SessionOrchestrator(
            session_manager=session_manager,
            stage_progression_handler=stage_progression_handler,
            logger=logger
        )

        # Create strategy factory with direct parameters
        strategy_factory = WorkflowStrategyFactory(
            agent_provider=agent_provider,
            prompt_manager=prompt_manager,
            session_manager=session_manager,
            conversation_manager=conversation_manager,
            logger=logger
        )

        # Create main orchestrator
        return WorkflowOrchestrator(
            strategy_factory=strategy_factory,
            crisis_handler=crisis_handler,
            session_orchestrator=session_orchestrator,
            logger=logger
        )

    @staticmethod
    def create_test_orchestrator(agent_provider, prompt_manager, session_manager, conversation_manager, logger):
        """
        Create workflow orchestrator for testing (no UI dependencies).

        Args:
            agent_provider: Agent provider interfaces
            prompt_manager: Prompt management service
            session_manager: Session state manager
            conversation_manager: Conversation state manager
            logger: Logger for workflow events

        Returns:
            WorkflowOrchestrator: Fully configured orchestrator for testing
        """
        # Create no-op UI notifier for testing
        ui_notifier = NoOpCrisisNotifier()

        # Create crisis handler
        crisis_handler = CrisisHandler(
            session_manager=session_manager,
            ui_notifier=ui_notifier,
            logger=logger
        )

        # Create session orchestration components
        stage_progression_handler = StageProgressionHandler(
            session_manager=session_manager,
            logger=logger
        )

        session_orchestrator = SessionOrchestrator(
            session_manager=session_manager,
            stage_progression_handler=stage_progression_handler,
            logger=logger
        )

        # Create strategy factory with direct parameters
        strategy_factory = WorkflowStrategyFactory(
            agent_provider=agent_provider,
            prompt_manager=prompt_manager,
            session_manager=session_manager,
            conversation_manager=conversation_manager,
            logger=logger
        )

        # Create main orchestrator
        return WorkflowOrchestrator(
            strategy_factory=strategy_factory,
            crisis_handler=crisis_handler,
            session_orchestrator=session_orchestrator,
            logger=logger
        )