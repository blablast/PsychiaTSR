"""
Refactored workflow manager using new SOLID architecture.
"""

from ..agents.interfaces.agent_provider_interface import IAgentProvider
from ..prompts.unified_prompt_manager import UnifiedPromptManager
from ..conversation.conversation_manager import ConversationManager
from .workflow_result import WorkflowResult


class TherapyWorkflowManager:
    """
    Refactored workflow manager using new SOLID architecture.

    Acts as a facade over the new WorkflowOrchestrator.
    """

    def __init__(self,
                 agent_provider: IAgentProvider,
                 prompt_manager: UnifiedPromptManager,
                 conversation_manager: ConversationManager,
                 logger):
        self._conversation_manager = conversation_manager

        # New architecture components
        from .workflow_factory import WorkflowFactory
        self._session_manager = None
        self._orchestrator = None
        self._factory_args = {
            'agent_provider': agent_provider,
            'prompt_manager': prompt_manager,
            'conversation_manager': conversation_manager,
            'logger': logger
        }


    def set_session_manager(self, session_manager):
        """Set session manager and initialize orchestrator."""
        self._session_manager = session_manager
        if self._orchestrator is None:
            from .workflow_factory import WorkflowFactory
            self._orchestrator = WorkflowFactory.create_streamlit_orchestrator(
                session_manager=session_manager,
                **self._factory_args
            )

    def process_user_message(self, user_message: str) -> WorkflowResult:
        """
        Process user message through complete therapy workflow.

        Args:
            user_message: User's message to process

        Returns:
            WorkflowResult containing complete workflow results
        """
        if not self._orchestrator:
            return WorkflowResult(
                success=False,
                message="Workflow orchestrator not initialized",
                error="ORCHESTRATOR_NOT_INITIALIZED"
            )

        return self._orchestrator.process_legacy_message(
            user_message=user_message,
            current_stage=self._session_manager.get_current_stage(),
            conversation_history=self._session_manager.get_conversation_history(exclude_stage_transitions=True),
            session_id=self._session_manager.get_session_id()
        )


    def process_pending_question(self) -> WorkflowResult:
        """
        Process pending question from ConversationManager.

        Returns:
            WorkflowResult containing complete workflow results
        """
        if not self._orchestrator:
            return WorkflowResult(
                success=False,
                message="Workflow orchestrator not initialized",
                error="ORCHESTRATOR_NOT_INITIALIZED"
            )

        if not self._conversation_manager.has_pending_question():
            return WorkflowResult(
                success=False,
                message="No pending question to process",
                error="NO_PENDING_QUESTION"
            )

        _, current_question = self._conversation_manager.start_processing()
        return self._orchestrator.process_conversation_message(
            user_message=current_question,
            current_stage=self._session_manager.get_current_stage(),
            conversation_history=self._conversation_manager.get_committed_context(),
            session_id=self._session_manager.get_session_id()
        )

    def process_pending_question_stream(self):
        """
        Process pending question from ConversationManager with streaming.

        Yields therapist response chunks.
        """
        if not self._orchestrator:
            yield f"[Błąd: Workflow orchestrator nie został zainicjalizowany]"
            return

        if not self._conversation_manager.has_pending_question():
            yield f"[Błąd: Brak pytania do przetworzenia]"
            return

        _, current_question = self._conversation_manager.start_processing()

        yield from self._orchestrator.process_conversation_message_stream(
            user_message=current_question,
            current_stage=self._session_manager.get_current_stage(),
            conversation_history=self._conversation_manager.get_committed_context(),
            session_id=self._session_manager.get_session_id()
        )


