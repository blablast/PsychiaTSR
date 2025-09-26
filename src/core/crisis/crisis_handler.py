"""Crisis handling logic separated from workflow concerns."""

from ..workflow.workflow_result import WorkflowResult
from .interfaces import ICrisisHandler, ICrisisSessionManager, UICrisisNotifier
from .crisis_config import CrisisConfig


class CrisisHandler(ICrisisHandler):
    """Handles crisis situations when safety risks are detected."""

    def __init__(
        self, session_manager: ICrisisSessionManager, ui_notifier: UICrisisNotifier, logger
    ):
        """
        Initialize crisis handler.

        Args:
            session_manager: Session manager for conversation updates (interface)
            ui_notifier: UI notification strategy
            logger: Logger for crisis events
        """
        self._session_manager = session_manager
        self._ui_notifier = ui_notifier
        self._logger = logger
        self._crisis_active = False

    def handle_crisis(self, user_message: str, supervisor_decision) -> WorkflowResult:
        """
        Handle crisis situation when safety_risk is detected.

        Args:
            user_message: User's message that triggered crisis
            supervisor_decision: Supervisor decision with safety_risk=True

        Returns:
            WorkflowResult with crisis response
        """
        # Log crisis activation
        self._logger.log_error("🚨 PROTOKÓŁ KRYZYSOWY AKTYWOWANY")
        self._crisis_active = True

        # Notify UI of crisis state
        self._ui_notifier.notify_crisis_detected()

        # Generate crisis response from config
        crisis_response = CrisisConfig.get_crisis_response()
        protocols = CrisisConfig.get_crisis_protocols()

        # Update conversation with crisis response
        self._session_manager.add_user_message(user_message)
        self._session_manager.add_assistant_message(
            crisis_response, protocols["immediate_response"]
        )

        # Log crisis response sent
        self._logger.log_info("🚨 Wysłano odpowiedź kryzysową")

        return WorkflowResult(
            success=True,
            message="Crisis protocol activated",
            data={
                "crisis_mode": True,
                "supervisor_decision": supervisor_decision,
                "therapist_response": crisis_response,
                "stage_changed": False,
                "current_stage": self._session_manager.get_current_stage(),
            },
        )

    def is_crisis_active(self) -> bool:
        """Check if crisis mode is currently active."""
        return self._crisis_active

    def get_crisis_contacts(self) -> dict:
        """Get emergency contact information."""
        return CrisisConfig.get_crisis_contacts()

    def deactivate_crisis(self) -> None:
        """Deactivate crisis mode (for testing/admin purposes)."""
        self._crisis_active = False
        self._logger.log_info("🚨 Protokół kryzysowy dezaktywowany")
