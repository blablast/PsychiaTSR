from typing import Dict, Any, List
from .base import BaseAgent
from ..llm.base import LLMProvider
from ..utils.safety import SafetyChecker
from ..utils.schemas import MessageData


class TherapistAgent(BaseAgent):
    """Therapeutic agent for conversations with memory optimization."""

    ADDITIONAL_GUIDELINES_HEADER = "DODATKOWE WYTYCZNE"
    USER_PROMPT_TEMPLATE = """KONTEKST ROZMOWY:
{context}

AKTUALNA WIADOMOŚĆ UŻYTKOWNIKA:
{user_message}

Odpowiedz zgodnie z zasadami TSR."""

    def __init__(self, llm_provider: LLMProvider, safety_checker: SafetyChecker):
        super().__init__(llm_provider, safety_checker)
        self._current_stage = None
        self._stage_prompt_set = False


    def set_stage_prompt(self, stage_id: str, stage_prompt: str):
        """Set stage prompt once when entering new stage"""
        if self._current_stage != stage_id:
            self._current_stage = stage_id
            self._stage_prompt_set = False

        if not self._stage_prompt_set:
            # Send stage prompt only once per stage
            if hasattr(self.llm_provider, 'conversation_messages') or hasattr(self.llm_provider, 'chat_session'):
                # For memory-optimized providers, send stage prompt as system message
                stage_instruction = f"NOWY ETAP TERAPII:\n{stage_prompt}\n\nOd teraz prowadź rozmowę zgodnie z wytycznymi tego etapu."

                # Send stage instruction
                if hasattr(self.llm_provider, 'add_user_message') and hasattr(self.llm_provider, 'add_assistant_message'):
                    self.llm_provider.add_user_message(stage_instruction)
                    self.llm_provider.add_assistant_message("Rozumiem. Prowadzę rozmowę zgodnie z wytycznymi tego etapu.")

                self._stage_prompt_set = True

    def generate_response(
        self,
        user_message: str,
        stage_prompt: str,
        conversation_history: List[MessageData],
        stage_id: str = None
    ) -> Dict[str, Any]:
        """Generate therapeutic response"""

        # Check user input for safety
        safety_check = self.safety_checker.check_user_input(user_message)

        # Set stage prompt if provided and if entering new stage
        if stage_id and stage_prompt:
            self.set_stage_prompt(stage_id, stage_prompt)

        # Build context from conversation history
        context = self._build_conversation_context(conversation_history)

        # Validate system prompt is set
        self._validate_required_prompt()

        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            context=context,
            user_message=user_message
        )

        try:
            # Prepare final prompt with stage context if needed
            if self._stage_prompt_set:
                # Ultra-optimized: stage prompt already sent via set_stage_prompt
                final_prompt = user_prompt
                self._prepare_prompt_info(
                    prompt_id="ultra_optimized",
                    prompt_type="ultra_optimized",
                    prompt_content=final_prompt,
                    review=f"Ultra-optimized approach - stage prompt sent once for stage {stage_id}"
                )
            else:
                # Include stage prompt if not set yet
                final_prompt = f"{stage_prompt}\n\n{user_prompt}" if stage_prompt else user_prompt
                prompt_type = "memory_optimized" if stage_prompt else "standard"
                self._prepare_prompt_info(
                    prompt_id=prompt_type,
                    prompt_type=prompt_type,
                    prompt_content=final_prompt,
                    review=f"Using {prompt_type} approach - stage prompt {'included' if stage_prompt else 'not provided'}"
                )

            # Generate response using base class method
            response = self._generate_with_memory_optimization(
                prompt=final_prompt,
                temperature=0.7,
                max_tokens=150
            )

            validation = self.safety_checker.validate_therapist_response(response)

            return {
                "response": response,
                "safety_check": safety_check,
                "validation": validation,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            error_result = self._handle_llm_error(e, "generating therapeutic response")
            error_result.update({
                "response": "",
                "safety_check": safety_check,
                "validation": {"is_valid": False, "issues": [str(e)]}
            })
            return error_result