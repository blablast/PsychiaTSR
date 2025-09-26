"""Dedicated stage progression handling logic."""

from dataclasses import dataclass


@dataclass
class StageProgressionResult:
    """Result of stage progression operation."""

    success: bool
    old_stage: str
    new_stage: str
    message: str
    error: str = None


class StageProgressionHandler:
    """Handles stage progression logic separately from workflow concerns."""

    def __init__(self, session_manager, logger):
        """
        Initialize stage progression handler.

        Args:
            session_manager: Session manager for stage operations
            logger: Logger for progression events
        """
        self._session_manager = session_manager
        self._logger = logger

    @staticmethod
    def should_advance_stage(supervisor_decision) -> bool:
        """
        Determine if stage should advance based on supervisor decision.

        Args:
            supervisor_decision: SupervisorDecision object

        Returns:
            bool: True if stage should advance
        """
        return supervisor_decision.decision == "advance"

    def advance_stage(self) -> StageProgressionResult:
        """
        Execute stage advancement.

        Returns:
            StageProgressionResult with advancement details
        """
        try:
            old_stage = self._session_manager.get_current_stage()

            progression_result = self._session_manager.advance_to_next_stage()

            if not progression_result.success:
                return StageProgressionResult(
                    success=False,
                    old_stage=old_stage,
                    new_stage=old_stage,
                    message="Stage progression failed",
                    error=progression_result.error,
                )

            new_stage = self._session_manager.get_current_stage()

            # Log stage progression
            self._logger.log_info("=" * 60)
            self._logger.log_info(f"🎯 ZMIANA ETAPU TERAPII: '{old_stage}' → '{new_stage}'")
            self._logger.log_info("Nowe prompty systemowe zostaną ustawione dla agentów")
            self._logger.log_info("=" * 60)

            return StageProgressionResult(
                success=True,
                old_stage=old_stage,
                new_stage=new_stage,
                message=f"Stage advanced from {old_stage} to {new_stage}",
            )

        except Exception as e:
            self._logger.log_error(f"Stage progression failed: {str(e)}")
            return StageProgressionResult(
                success=False,
                old_stage=self._session_manager.get_current_stage(),
                new_stage=self._session_manager.get_current_stage(),
                message="Stage progression failed due to exception",
                error=str(e),
            )

    def add_stage_transition_message(self, current_stage: str) -> None:
        """
        Add stage transition message to conversation.

        Args:
            current_stage: Current stage name
        """
        try:
            stage_transition_message = f"[Etap terapii: {current_stage}]"
            self._session_manager.add_stage_transition_message(stage_transition_message)
        except Exception as e:
            self._logger.log_error(f"Failed to add stage transition message: {str(e)}")
