"""Refactored SupervisorAgent following Single Responsibility Principle and Dependency Injection."""

from typing import List
from ..llm.base import LLMProvider
from ..core.services import PromptService, ParsingService, SafetyService, MemoryService
from ..utils.schemas import MessageData, SupervisorDecision


class SupervisorAgent:
    """
    SupervisorAgent focused ONLY on stage evaluation business logic.

    Uses dependency injection for all infrastructure concerns:
    - PromptService: prompt management
    - ParsingService: JSON parsing and validation
    - SafetyService: safety checking
    - MemoryService: LLM memory management
    """

    def __init__(self,
                 llm_provider: LLMProvider,
                 prompt_service: PromptService,
                 parsing_service: ParsingService,
                 safety_service: SafetyService,
                 memory_service: MemoryService,
                 logger=None):
        self._llm_provider = llm_provider
        self._prompt_service = prompt_service
        self._parsing_service = parsing_service
        self._safety_service = safety_service
        self._memory_service = memory_service
        self._logger = logger

        # Agent state
        self._current_stage_id = None
        self._system_prompt_set = False
        self._stage_prompt_set = False

        # Configure structured output if supported
        self._configure_structured_output()

    def evaluate_stage_completion(self, stage: str, history: List[MessageData], stage_prompt: str) -> SupervisorDecision:
        """
        CORE BUSINESS LOGIC: Evaluate if current stage is complete and should advance.

        This is the ONLY responsibility of SupervisorAgent.
        All infrastructure is delegated to injected services.
        """
        import time
        start_time = time.time()

        try:
            # Ensure system and stage prompts are set
            self._ensure_prompts_configured(stage, stage_prompt)

            # Build conversation context (delegated to MemoryService)
            conversation_context = self._memory_service.build_conversation_context(history, max_messages=10)

            # Build safety context (delegated to SafetyService)
            safety_context = self._safety_service.build_safety_context(history)

            # Build supervisor prompt (delegated to PromptService)
            supervisor_prompt = self._prompt_service.build_supervisor_prompt(stage, conversation_context, safety_context)

            # Log supervisor request
            if self._logger:
                stage_prompt_text = self._prompt_service.get_stage_prompt(stage, "supervisor")
                system_prompt_text = self._prompt_service.get_system_prompt("supervisor")
                prompt_data = {
                    "id": f"supervisor_{stage}",
                    "prompt_text": f"{system_prompt_text}\n\n{stage_prompt_text}"
                }
                self._logger.log_supervisor_request(prompt_data)

            # Generate LLM response
            response = self._llm_provider.generate_sync(prompt=supervisor_prompt)

            # Parse response (delegated to ParsingService)
            parsed_data = self._parsing_service.parse_supervisor_response(response)

            # Create supervisor decision (delegated to ParsingService)
            decision = self._parsing_service.create_supervisor_decision(parsed_data)

            # Apply safety checks (delegated to SafetyService)
            final_decision = self._safety_service.apply_safety_to_decision(decision, history)

            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            # Log supervisor response
            if self._logger:
                self._logger.log_supervisor_response(final_decision, response_time_ms)

            return final_decision

        except Exception as e:
            # Return safe fallback decision
            if self._logger:
                self._logger.log_error(f"Supervisor evaluation failed: {str(e)}")

            return SupervisorDecision(
                decision="stay",
                summary=f"Błąd w ocenie nadzorcy: {str(e)}",
                addressing="formal",
                reason=f"Błąd w ocenie nadzorcy: {str(e)}",
                handoff={"error": str(e), "error_type": type(e).__name__},
                safety_risk=False,
                safety_message=""
            )

    def _ensure_prompts_configured(self, stage_id: str, stage_prompt: str) -> None:
        """Ensure system and stage prompts are configured."""
        # Set system prompt once
        if not self._system_prompt_set:
            system_prompt = self._prompt_service.get_system_prompt("supervisor")
            if system_prompt:
                self._memory_service.setup_system_prompt(self._llm_provider, system_prompt, "supervisor")
                self._system_prompt_set = True

        # Set stage prompt if entering new stage
        if self._current_stage_id != stage_id:
            # Log stage transition before updating (only supervisor logs this)
            if self._logger:
                self._logger.log_stage_transition(self._current_stage_id or "none", stage_id)

            self._current_stage_id = stage_id
            self._stage_prompt_set = False

        if not self._stage_prompt_set and stage_prompt:
            self._memory_service.setup_stage_prompt(self._llm_provider, stage_prompt, stage_id, "supervisor")
            self._stage_prompt_set = True

    def _configure_structured_output(self) -> None:
        """Configure structured output format for the LLM provider."""
        provider_class = self._llm_provider.__class__.__name__

        if provider_class == 'OpenAIProvider':
            if hasattr(self._llm_provider, 'set_default_response_format'):
                from ..utils.schemas import SupervisorDecision
                response_format = SupervisorDecision.get_openai_response_format()
                self._llm_provider.set_default_response_format(response_format)
                if self._logger:
                    self._logger.log_info("OpenAI structured output configured for session", {
                        "provider": "OpenAI",
                        "feature": "structured_output",
                        "agent_type": "supervisor"
                    })
        elif provider_class == 'GeminiProvider':
            if hasattr(self._llm_provider, 'set_default_response_schema'):
                from ..utils.schemas import SupervisorDecision
                response_schema = SupervisorDecision.get_gemini_response_schema()
                self._llm_provider.set_default_response_schema(response_schema)
                if self._logger:
                    self._logger.log_info("Gemini structured output configured for session", {
                        "provider": "Gemini",
                        "feature": "structured_output",
                        "agent_type": "supervisor"
                    })

    # Compatibility methods for existing workflow
    def set_system_prompt(self, system_prompt: str) -> None:
        """Compatibility method for existing workflow."""
        if not self._system_prompt_set:
            self._memory_service.setup_system_prompt(self._llm_provider, system_prompt, "supervisor")
            self._system_prompt_set = True

    def get_last_used_prompt_info(self) -> dict:
        """Compatibility method for existing workflow."""
        return {"full_prompt": "Supervisor prompt info not tracked in new architecture"}

    @property
    def _system_prompt(self) -> str:
        """Compatibility property for existing workflow."""
        return self._prompt_service.get_system_prompt("supervisor") if self._system_prompt_set else None