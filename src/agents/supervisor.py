import json
from typing import Dict, Any, List
from .base import BaseAgent
from ..llm.base import LLMProvider
from ..utils.safety import SafetyChecker
from ..utils.schemas import MessageData, SupervisorDecision


class SupervisorAgent(BaseAgent):
    """Supervisor agent for evaluating stage progression with memory optimization."""

    def __init__(self, llm_provider: LLMProvider, safety_checker: SafetyChecker):
        super().__init__(llm_provider, safety_checker)
        self._current_stage_id = None
        self._stage_prompt_set = False

    def set_stage_prompt(self, stage_id: str, stage_prompt: str):
        """Set stage prompt once when entering new stage"""
        if self._current_stage_id != stage_id:
            self._current_stage_id = stage_id
            self._stage_prompt_set = False

        if not self._stage_prompt_set:
            # Send stage prompt only once per stage for memory-optimized providers
            if hasattr(self.llm_provider, 'conversation_messages') or hasattr(self.llm_provider, 'chat_session'):
                stage_instruction = f"NOWY ETAP OCENY SUPERVISORA:\n{stage_prompt}\n\nOd teraz oceniaj postęp zgodnie z wytycznymi tego etapu."

                # Send stage instruction
                if hasattr(self.llm_provider, 'add_user_message') and hasattr(self.llm_provider, 'add_assistant_message'):
                    self.llm_provider.add_user_message(stage_instruction)
                    self.llm_provider.add_assistant_message("Rozumiem. Oceniam postęp zgodnie z wytycznymi tego etapu.")

                self._stage_prompt_set = True

    def generate_response(self, stage: str, history: List[MessageData], stage_prompt: str) -> Dict[str, Any]:
        """Generate supervisor evaluation response (implements BaseAgent.generate_response)."""
        try:
            result = self.evaluate_stage_completion(stage, history, stage_prompt)
            return {
                "success": True,
                "response": result,
                "supervisor_decision": result  # For backward compatibility
            }
        except Exception as e:
            return self._handle_llm_error(e, "evaluating stage completion")

    def evaluate_stage_completion(self, stage: str, history: List[MessageData], stage_prompt: str) -> SupervisorDecision:
        """Evaluate if current stage is complete and should advance"""

        try:
            # Validate system prompt is set
            self._validate_required_prompt()

            # Set stage prompt if provided and if entering new stage
            if stage and stage_prompt:
                self.set_stage_prompt(stage, stage_prompt)

            # Build conversation context using base class method
            conversation = self._build_conversation_context(history, max_messages=10)

            # Add safety context
            safety_context = self._build_safety_context(history)

            # Prepare evaluation prompt with smart stage prompt handling
            if self._stage_prompt_set:
                # Ultra-optimized: stage prompt already sent via set_stage_prompt
                evaluation_prompt = f"OSTATNIE WIADOMOŚCI:\n{conversation}\n\n{safety_context}"
                self._prepare_prompt_info(
                    prompt_id="ultra_optimized",
                    prompt_type="supervisor_ultra_optimized",
                    prompt_content=evaluation_prompt,
                    review=f"Ultra-optimized supervisor evaluation - stage prompt sent once for stage {stage}"
                )
            else:
                # Include stage prompt if not set yet
                evaluation_prompt = f"{stage_prompt}\n\nOSTATNIE WIADOMOŚCI:\n{conversation}\n\n{safety_context}"
                self._prepare_prompt_info(
                    prompt_id="memory_optimized",
                    prompt_type="supervisor_memory_optimized",
                    prompt_content=evaluation_prompt,
                    review=f"Memory-optimized supervisor evaluation - stage prompt included for stage {stage}"
                )

            # Generate response using base class method
            response = self._generate_with_memory_optimization(
                prompt=evaluation_prompt,
                temperature=0.3,
                max_tokens=300
            )

            decision_data = self._parse_supervisor_response(response)
            
            safety_risk = self._check_conversation_safety(history)
            if safety_risk["has_risk"]:
                decision_data["safety_risk"] = True
                decision_data["safety_message"] = self.safety_checker.get_crisis_message()
            
            return SupervisorDecision(
                decision=decision_data.get("decision", "stay"),
                reason=decision_data.get("reason", ""),
                handoff=decision_data.get("handoff", {}),
                safety_risk=decision_data.get("safety_risk", False),
                safety_message=decision_data.get("safety_message", "")
            )
            
        except Exception as e:
            # Return error decision with consistent structure
            return SupervisorDecision(
                decision="stay",
                reason=f"Błąd w ocenie nadzorcy: {str(e)}",
                handoff={"error": str(e), "error_type": type(e).__name__},
                safety_risk=False,
                safety_message=""
            )
    

    def _parse_supervisor_response(self, response: str) -> Dict[str, Any]:
        try:
            response = response.strip()

            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")

            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)

            # Convert string booleans to actual booleans
            if "safety_risk" in data:
                if isinstance(data["safety_risk"], str):
                    data["safety_risk"] = data["safety_risk"].lower() in ["true", "1", "yes"]

            return data

        except (json.JSONDecodeError, ValueError):
            return self._fallback_parse(response)
    
    @staticmethod
    def _fallback_parse(response: str) -> Dict[str, Any]:
        import re

        decision = "stay"
        reason = "Nie udało się sparsować odpowiedzi nadzorcy"

        decision_match = re.search(r'"decision":\s*"(stay|advance)"', response)
        if decision_match:
            decision = decision_match.group(1)

        reason_match = re.search(r'"reason":\s*"([^"]+)"', response)
        if reason_match:
            reason = reason_match.group(1)

        return {
            "decision": decision,
            "reason": reason,
            "handoff": {"parsing_error": True},
            "safety_risk": False,
            "safety_message": ""
        }
    
    def _build_safety_context(self, conversation_history: List[MessageData]) -> str:
        recent_messages = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history

        safety_concerns = []
        for msg in recent_messages:
            if msg.role == "user":
                safety_check = self.safety_checker.check_user_input(msg.text)
                if safety_check["has_risk"]:
                    concern_text = self._get_safety_concern_text(msg.text[:100])
                    safety_concerns.append(concern_text)

        if safety_concerns:
            return self._get_safety_context_with_risks(safety_concerns)
        else:
            return self._get_no_safety_risks_text()

    @staticmethod
    def _get_safety_concern_text(message_excerpt: str) -> str:
        return f"RYZYKO BEZPIECZEŃSTWA w wiadomości: {message_excerpt}..."

    @staticmethod
    def _get_safety_context_with_risks(safety_concerns: List[str]) -> str:
        return f"""
WAŻNE - WYKRYTE RYZYKO BEZPIECZEŃSTWA:
{chr(10).join(safety_concerns)}

Jeśli wykryjesz ryzyko bezpieczeństwa, ustaw safety_risk na true i podaj odpowiednią wiadomość.
"""

    @staticmethod
    def _get_no_safety_risks_text() -> str:
        return "Brak wykrytych zagrożeń bezpieczeństwa w ostatnich wiadomościach."
    
    def _check_conversation_safety(self, conversation_history: List[MessageData]) -> Dict[str, Any]:
        all_user_messages = [msg.text for msg in conversation_history if msg.role == "user"]

        total_safety = {
            "has_risk": False,
            "risk_count": 0,
            "high_risk_messages": []
        }

        for i, message in enumerate(all_user_messages):
            safety_check = self.safety_checker.check_user_input(message)
            if safety_check["has_risk"]:
                total_safety["has_risk"] = True
                total_safety["risk_count"] += 1

                if safety_check["risk_level"] == "high":
                    total_safety["high_risk_messages"].append({
                        "index": i,
                        "message": message[:100],
                        "keywords": safety_check["matched_keywords"]
                    })

        return total_safety
