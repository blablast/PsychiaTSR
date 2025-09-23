"""Refactored TherapistAgent following Single Responsibility Principle and Dependency Injection."""

from typing import List, Dict, Any
from ..llm.base import LLMProvider
from ..core.services import PromptService, SafetyService, MemoryService
from ..utils.schemas import MessageData


class TherapistAgent:
    """
    TherapistAgent focused ONLY on therapeutic response generation business logic.

    Uses dependency injection for all infrastructure concerns:
    - PromptService: prompt management
    - SafetyService: safety checking
    - MemoryService: LLM memory management
    """

    def __init__(self,
                 llm_provider: LLMProvider,
                 prompt_service: PromptService,
                 safety_service: SafetyService,
                 memory_service: MemoryService,
                 logger=None):
        self._llm_provider = llm_provider
        self._prompt_service = prompt_service
        self._safety_service = safety_service
        self._memory_service = memory_service
        self._logger = logger

        # Agent state
        self._current_stage = None
        self._system_prompt_set = False
        self._stage_prompt_set = False

    def generate_response(self,
                         user_message: str,
                         stage_prompt: str,
                         conversation_history: List[MessageData],
                         stage_id: str = None) -> Dict[str, Any]:
        """
        CORE BUSINESS LOGIC: Generate therapeutic response.

        This is the ONLY responsibility of TherapistAgent.
        All infrastructure is delegated to injected services.
        """
        import time
        start_time = time.time()

        try:
            # Check user input for safety (delegated to SafetyService)
            safety_check = self._safety_service.check_user_input(user_message)

            # Ensure system and stage prompts are configured
            self._ensure_prompts_configured(stage_id, stage_prompt)

            # Build conversation context (delegated to MemoryService)
            conversation_context = self._memory_service.build_conversation_context(conversation_history)

            # Build therapist prompt (delegated to PromptService)
            therapist_prompt = self._prompt_service.build_therapist_prompt(user_message, conversation_context)

            # Log therapist request
            if self._logger:
                stage_prompt_text = self._prompt_service.get_stage_prompt(stage_id, "therapist")
                system_prompt_text = self._prompt_service.get_system_prompt("therapist")
                prompt_data = {
                    "id": f"therapist_{stage_id}",
                    "prompt_text": f"{system_prompt_text}\n\n{stage_prompt_text}"
                }
                self._logger.log_therapist_request(prompt_data)

            # Generate LLM response
            if self._memory_service.supports_memory(self._llm_provider):
                # Memory-optimized: system prompt already set, just send user prompt
                response = self._llm_provider.generate_sync(prompt=therapist_prompt)
            else:
                # Traditional: send complete prompt with system context
                system_prompt = self._prompt_service.get_system_prompt("therapist")
                response = self._llm_provider.generate_sync(
                    prompt=therapist_prompt,
                    system_prompt=system_prompt
                )

            # Validate response for safety (delegated to SafetyService)
            validation = self._safety_service.validate_therapist_response(response)

            # Clean response
            clean_response = response.replace('\\n', '\n')

            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            # Log therapist response
            if self._logger:
                self._logger.log_therapist_response(clean_response, response_time_ms)

            return {
                "response": clean_response,
                "original_response": response,
                "safety_check": safety_check,
                "validation": validation,
                "success": True,
                "error": None
            }

        except Exception as e:
            # Handle error with safety check already performed
            if self._logger:
                self._logger.log_error(f"Therapist response generation failed: {str(e)}")

            return {
                "response": "",
                "original_response": "",
                "safety_check": safety_check if 'safety_check' in locals() else {"has_risk": False},
                "validation": {"is_valid": False, "issues": [str(e)]},
                "success": False,
                "error": str(e)
            }

    def generate_response_stream(self,
                               user_message: str,
                               stage_prompt: str,
                               conversation_history: List[MessageData],
                               stage_id: str = None):
        """
        CORE BUSINESS LOGIC: Generate therapeutic response with streaming.

        Yields response chunks as they arrive from the LLM.
        """
        import time
        start_time = time.time()

        try:
            # Check user input for safety (delegated to SafetyService)
            safety_check = self._safety_service.check_user_input(user_message)

            # Ensure system and stage prompts are configured
            self._ensure_prompts_configured(stage_id, stage_prompt)

            # Build conversation context (delegated to MemoryService)
            conversation_context = self._memory_service.build_conversation_context(conversation_history)

            # Build therapist prompt (delegated to PromptService)
            therapist_prompt = self._prompt_service.build_therapist_prompt(user_message, conversation_context)

            # Log therapist request
            if self._logger:
                stage_prompt_text = self._prompt_service.get_stage_prompt(stage_id, "therapist")
                system_prompt_text = self._prompt_service.get_system_prompt("therapist")
                prompt_data = {
                    "id": f"therapist_{stage_id}",
                    "prompt_text": f"{system_prompt_text}\n\n{stage_prompt_text}"
                }
                self._logger.log_therapist_request(prompt_data)

            # Generate streaming LLM response
            full_response = ""
            if self._memory_service.supports_memory(self._llm_provider):
                # Memory-optimized: system prompt already set, just send user prompt
                stream = self._llm_provider.generate_stream(prompt=therapist_prompt)
            else:
                # Traditional: send complete prompt with system context
                system_prompt = self._prompt_service.get_system_prompt("therapist")
                stream = self._llm_provider.generate_stream(
                    prompt=therapist_prompt,
                    system_prompt=system_prompt
                )

            # Stream response chunks
            for chunk in stream:
                full_response += chunk
                yield chunk

            # Validate complete response for safety (delegated to SafetyService)
            validation = self._safety_service.validate_therapist_response(full_response)

            # Clean response
            clean_response = full_response.replace('\\n', '\n')

            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            # Log therapist response
            if self._logger:
                self._logger.log_therapist_response(clean_response, response_time_ms)

            # Yield final metadata so adapter can catch it
            yield {
                "response": clean_response,
                "original_response": full_response,
                "safety_check": safety_check,
                "validation": validation,
                "success": True,
                "error": None,
                "response_time_ms": response_time_ms
            }

        except Exception as e:
            # Handle error with safety check already performed
            if self._logger:
                self._logger.log_error(f"Therapist streaming response failed: {str(e)}")

            # Yield error message so UI can display it
            yield f"[Błąd generowania odpowiedzi: {str(e)}]"

            # Yield error metadata
            yield {
                "response": "",
                "original_response": "",
                "safety_check": safety_check if 'safety_check' in locals() else {"has_risk": False},
                "validation": {"is_valid": False, "issues": [str(e)]},
                "success": False,
                "error": str(e)
            }

    def _ensure_prompts_configured(self, stage_id: str, stage_prompt: str) -> None:
        """Ensure system and stage prompts are configured."""
        # Set system prompt once
        if not self._system_prompt_set:
            system_prompt = self._prompt_service.get_system_prompt("therapist")
            if system_prompt:
                self._memory_service.setup_system_prompt(self._llm_provider, system_prompt, "therapist")
                self._system_prompt_set = True

        # Set stage prompt if entering new stage
        if self._current_stage != stage_id:
            self._current_stage = stage_id
            self._stage_prompt_set = False
            # Note: Only supervisor logs stage transitions, therapist just follows

        if not self._stage_prompt_set and stage_prompt:
            self._memory_service.setup_stage_prompt(self._llm_provider, stage_prompt, stage_id, "therapist")
            self._stage_prompt_set = True

    # Compatibility methods for existing workflow
    def set_system_prompt(self, system_prompt: str) -> None:
        """Compatibility method for existing workflow."""
        if not self._system_prompt_set:
            self._memory_service.setup_system_prompt(self._llm_provider, system_prompt, "therapist")
            self._system_prompt_set = True

    def get_last_used_prompt_info(self) -> dict:
        """Compatibility method for existing workflow."""
        return {"full_prompt": "Therapist prompt info not tracked in new architecture"}

    @property
    def _system_prompt(self) -> str:
        """Compatibility property for existing workflow."""
        return self._prompt_service.get_system_prompt("therapist") if self._system_prompt_set else None