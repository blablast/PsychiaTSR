"""JSON parsing and validation service following Single Responsibility Principle."""

import json
from typing import Dict, Any, Optional
from ...core.models.schemas import SupervisorDecision
from ..logging.interfaces.logger_interface import ILogger


class ParsingService:
    """Handles JSON parsing and validation for agent responses."""

    def __init__(self, logger: Optional[ILogger] = None):
        self._logger = logger

    def parse_supervisor_response(self, response: str) -> Dict[str, Any]:
        """Parse supervisor response into structured data."""
        try:
            response = response.strip()
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                if self._logger:
                    self._logger.log_error("No JSON structure detected in supervisor response", {
                        "response_preview": response
                    })
                raise ValueError("No JSON found in response")

            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)

            # Convert string booleans to actual booleans
            if "safety_risk" in data:
                if isinstance(data["safety_risk"], str):
                    data["safety_risk"] = data["safety_risk"].lower() in ["true", "1", "yes"]

            # Single consolidated parsing log
            if self._logger:
                self._logger.log_info("Supervisor JSON parsed successfully", {
                    "response_length": len(response),
                    "json_length": len(json_str),
                    "field_count": len(data),
                    "fields": list(data.keys())
                })

            return data

        except (json.JSONDecodeError, ValueError) as e:
            if self._logger:
                self._logger.log_error(f"JSON parsing failed: {str(e)}", {
                    "fallback": "regex parsing",
                    "error_type": type(e).__name__
                })
            return self._fallback_parse(response)

    @staticmethod
    def create_supervisor_decision(parsed_data: Dict[str, Any]) -> SupervisorDecision:
        """Create SupervisorDecision object from parsed data."""
        return SupervisorDecision(
            decision=parsed_data.get("decision", "stay"),
            summary=parsed_data.get("summary", "Podsumowanie etapu"),
            addressing=parsed_data.get("addressing", "formal"),
            reason=parsed_data.get("reason", ""),
            handoff=parsed_data.get("handoff", {}),
            safety_risk=parsed_data.get("safety_risk", False),
            safety_message=parsed_data.get("safety_message", "")
        )

    @staticmethod
    def _fallback_parse(response: str) -> Dict[str, Any]:
        """Fallback regex parsing when JSON parsing fails."""
        import re

        decision = "stay"
        summary = "Podsumowanie etapu - błąd parsowania odpowiedzi"
        addressing = "formal"
        reason = "Nie udało się sparsować odpowiedzi nadzorcy"

        # Try to extract decision
        decision_match = re.search(r'"decision":\s*"(stay|advance)"', response)
        if decision_match:
            decision = decision_match.group(1)

        # Try to extract summary
        summary_match = re.search(r'"summary":\s*"([^"]+)"', response)
        if summary_match:
            summary = summary_match.group(1)

        # Try to extract addressing
        addressing_match = re.search(r'"addressing":\s*"(formal|informal)"', response)
        if addressing_match:
            addressing = addressing_match.group(1)

        # Try to extract reason
        reason_match = re.search(r'"reason":\s*"([^"]+)"', response)
        if reason_match:
            reason = reason_match.group(1)

        return {
            "decision": decision,
            "summary": summary,
            "addressing": addressing,
            "reason": reason,
            "handoff": {"parsing_error": True, "original_response": response},
            "safety_risk": False,
            "safety_message": ""
        }