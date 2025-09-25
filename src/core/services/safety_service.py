"""Safety checking service following Single Responsibility Principle."""

from typing import List, Dict, Any
from ...core.safety import SafetyChecker
from ...core.models.schemas import MessageData, SupervisorDecision


class SafetyService:
    """Handles all safety-related operations for agents."""

    def __init__(self, safety_checker: SafetyChecker):
        self._safety_checker = safety_checker

    def check_user_input(self, user_message: str) -> Dict[str, Any]:
        """Check user input for safety concerns."""
        return self._safety_checker.check_user_input(user_message)

    def validate_therapist_response(self, response: str) -> Dict[str, Any]:
        """Validate therapist response for safety."""
        return self._safety_checker.validate_therapist_response(response)

    def check_conversation_safety(self, conversation_history: List[MessageData]) -> Dict[str, Any]:
        """Check entire conversation for safety risks."""
        recent_messages = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history

        safety_concerns = []
        for msg in recent_messages:
            if msg.role == "user":
                safety_check = self.check_user_input(msg.text)
                if safety_check["has_risk"]:
                    concern_text = f"RYZYKO BEZPIECZEŃSTWA w wiadomości: {msg.text}..."
                    safety_concerns.append(concern_text)

        return {
            "has_risk": len(safety_concerns) > 0,
            "concerns": safety_concerns,
            "crisis_message": self._safety_checker.get_crisis_message() if safety_concerns else ""
        }

    def build_safety_context(self, conversation_history: List[MessageData]) -> str:
        """Build safety context string for prompts."""
        safety_check = self.check_conversation_safety(conversation_history)

        if safety_check["has_risk"]:
            concerns_text = "\n".join(safety_check["concerns"])
            return f"WYKRYTE ZAGROŻENIA BEZPIECZEŃSTWA:\n{concerns_text}\n\n"\
                   "Ważne: Ustaw safety_risk=true jeśli jest jakiekolwiek ryzyko."
        else:
            return "Brak wykrytych zagrożeń bezpieczeństwa w ostatnich wiadomościach."

    def apply_safety_to_decision(
            self,
            decision: SupervisorDecision,
            conversation_history: List[MessageData]) -> SupervisorDecision:
        """Apply safety checks to supervisor decision."""
        safety_check = self.check_conversation_safety(conversation_history)

        if safety_check["has_risk"]:
            decision.safety_risk = True
            decision.safety_message = safety_check["crisis_message"]

        return decision