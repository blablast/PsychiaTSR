"""Crisis handling logic separated from workflow concerns."""

from typing import Dict, Any
from ..workflow.workflow_result import WorkflowResult
from .ui_notifier import UICrisisNotifier


class CrisisHandler:
    """Handles crisis situations when safety risks are detected."""

    def __init__(self, session_manager, ui_notifier: UICrisisNotifier, logger):
        """
        Initialize crisis handler.

        Args:
            session_manager: Session manager for conversation updates
            ui_notifier: UI notification strategy
            logger: Logger for crisis events
        """
        self._session_manager = session_manager
        self._ui_notifier = ui_notifier
        self._logger = logger

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

        # Notify UI of crisis state
        self._ui_notifier.notify_crisis_detected()

        # Generate crisis response
        crisis_response = self._generate_crisis_response()

        # Update conversation with crisis response
        self._session_manager.add_user_message(user_message)
        self._session_manager.add_assistant_message(crisis_response, "crisis_protocol_v1")

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
                "current_stage": self._session_manager.get_current_stage()
            }
        )

    def _generate_crisis_response(self) -> str:
        """Generate standardized crisis response message."""
        return (
            "**⚠️ NATYCHMIASTOWA POMOC POTRZEBNA**\n\n"
            "Rozumiem, że przeżywasz bardzo trudny moment. Twoje bezpieczeństwo jest najważniejsze.\n\n"
            "**PILNE KONTAKTY:**\n"
            "• **Telefon Zaufania**: 116 123 (bezpłatny, całodobowy)\n"
            "• **Pogotowie Ratunkowe**: 112\n"
            "• **Najbliższy SOR** (Szpitalny Oddział Ratunkowy)\n\n"
            "**Nie jesteś sam/sama.** Jeśli masz myśli o skrzywdzeniu siebie, proszę natychmiast skontaktuj się "
            "z którymś z powyższych numerów lub udaj się do najbliższego szpitala.\n\n"
            "Czy możesz mi powiedzieć, czy jesteś teraz w bezpiecznym miejscu?"
        )