"""Factory for creating workflow strategies."""

from .workflow_strategy import WorkflowStrategy
from .conversation_workflow_strategy import ConversationWorkflowStrategy
from .workflow_request import WorkflowType
from .agent_adapters import SupervisorAdapter, TherapistAdapter


class WorkflowStrategyFactory:
    """Factory for creating appropriate workflow strategies."""

    def __init__(self, agent_provider, prompt_manager, session_manager, conversation_manager, logger):
        """
        Initialize strategy factory with dependencies.

        Args:
            agent_provider: Agent provider interfaces
            prompt_manager: Prompt management service
            session_manager: Session state manager
            conversation_manager: Conversation state manager
            logger: Logger for workflow events
        """
        self._agent_provider = agent_provider
        self._prompt_manager = prompt_manager
        self._session_manager = session_manager
        self._conversation_manager = conversation_manager
        self._logger = logger

        # Create adapters for agents
        self._supervisor_adapter = SupervisorAdapter(agent_provider, prompt_manager, logger)
        self._therapist_adapter = TherapistAdapter(agent_provider, prompt_manager, logger)

    def create_strategy(self, workflow_type: WorkflowType) -> WorkflowStrategy:
        """
        Create appropriate workflow strategy.

        Args:
            workflow_type: Type of workflow strategy to create

        Returns:
            WorkflowStrategy instance

        Raises:
            ValueError: If workflow_type is not supported
        """
        if workflow_type == WorkflowType.CONVERSATION:
            return ConversationWorkflowStrategy(
                supervisor_evaluator=self._supervisor_adapter,
                therapist_responder=self._therapist_adapter,
                conversation_manager=self._conversation_manager,
                logger=self._logger
            )
        else:
            raise ValueError(f"Unsupported workflow type: {workflow_type}")