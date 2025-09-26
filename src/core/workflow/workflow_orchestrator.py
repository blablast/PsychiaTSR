"""Main workflow orchestrator for therapy sessions."""

from .strategies.strategy_factory import WorkflowStrategyFactory
from .strategies.workflow_context import WorkflowContext
from .strategies.workflow_request import WorkflowRequest
from .workflow_result import WorkflowResult
from ..crisis.crisis_handler import CrisisHandler
from ..session.session_orchestrator import SessionOrchestrator


class WorkflowOrchestrator:
    """
    Simplified workflow orchestrator for therapy sessions.

    Orchestrates the workflow steps while delegating
    specific concerns to specialized services.
    """

    def __init__(
        self,
        strategy_factory: WorkflowStrategyFactory,
        crisis_handler: CrisisHandler,
        session_orchestrator: SessionOrchestrator,
        logger,
    ):
        """
        Initialize workflow orchestrator with injected dependencies.

        Args:
            strategy_factory: Factory for creating workflow strategies
            crisis_handler: Handler for crisis situations
            session_orchestrator: Handler for session-related operations
            logger: Logger for orchestration events
        """
        self._strategy_factory = strategy_factory
        self._crisis_handler = crisis_handler
        self._session_orchestrator = session_orchestrator
        self._logger = logger

    def process_request(self, request: WorkflowRequest) -> WorkflowResult:
        """
        Main orchestration method for processing workflow requests.

        Args:
            request: WorkflowRequest containing type and context

        Returns:
            WorkflowResult with execution results
        """
        try:
            self._logger.log_info(f"🔄 Starting {request.type.value} workflow")

            result = self._execute_strategy(request)
            if not result.success:
                return result

            result = self._handle_crisis_check(result, request)
            if not result.success:
                return result

            self._finalize_session(result, request)
            self._logger.log_info(f"✅ {request.type.value} workflow completed successfully")
            return result

        except Exception as e:
            self._logger.log_error(f"Workflow orchestration failed: {str(e)}")
            return WorkflowResult(
                success=False, message="Workflow orchestration failed", error=str(e)
            )

    def _execute_strategy(self, request: WorkflowRequest) -> WorkflowResult:
        """
        Execute the appropriate workflow strategy.

        Args:
            request: WorkflowRequest containing type and context

        Returns:
            WorkflowResult from strategy execution
        """
        strategy = self._strategy_factory.create_strategy(request.type)
        return strategy.execute(request.context)

    def _handle_crisis_check(
        self, result: WorkflowResult, request: WorkflowRequest
    ) -> WorkflowResult:
        """
        Check for and handle crisis situations.

        Args:
            result: WorkflowResult from strategy execution
            request: Original workflow request

        Returns:
            WorkflowResult - original result or crisis handling result
        """
        supervisor_decision = result.data.get("supervisor_decision")
        if supervisor_decision and supervisor_decision.safety_risk:
            self._logger.log_error("🚨 KRYZYS: Wykryto zagrożenie bezpieczeństwa!")
            return self._crisis_handler.handle_crisis(
                request.context.user_message, supervisor_decision
            )
        return result

    def _finalize_session(self, result: WorkflowResult, request: WorkflowRequest) -> None:
        """
        Finalize session state after successful processing.

        Args:
            result: WorkflowResult from successful execution
            request: Original workflow request
        """
        self._session_orchestrator.finalize_exchange(result, request.context.user_message)

    def process_conversation_message(
        self, user_message: str, current_stage: str, conversation_history, session_id: str
    ) -> WorkflowResult:
        """
        Convenience method for conversation workflow processing.

        Args:
            user_message: User's message
            current_stage: Current therapy stage
            conversation_history: Conversation history
            session_id: Session identifier

        Returns:
            WorkflowResult with execution results
        """
        request = WorkflowRequest.conversation(
            user_message=user_message,
            current_stage=current_stage,
            conversation_history=conversation_history,
            session_id=session_id,
        )
        return self.process_request(request)

    def process_conversation_message_stream(
        self, user_message: str, current_stage: str, conversation_history, session_id: str
    ):
        """
        Stream conversation workflow processing.

        Yields therapist response chunks while processing supervisor normally.
        """

        request = WorkflowRequest.conversation(
            user_message=user_message,
            current_stage=current_stage,
            conversation_history=conversation_history,
            session_id=session_id,
        )

        # Process request with streaming
        context = WorkflowContext.from_request(request)

        strategy = self._strategy_factory.create_strategy(request.type)

        # Check if strategy supports streaming
        if hasattr(strategy, "execute_stream"):
            yield from strategy.execute_stream(context)
        else:
            # Fallback to non-streaming
            result = strategy.execute(context)
            if result.success and result.data and result.data.get("therapist_response"):
                yield result.data["therapist_response"]
            else:
                yield f"[Błąd: {result.message}]"
