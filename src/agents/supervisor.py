"""
SupervisorAgent - Business logic for therapy stage evaluation and progression decisions.

This agent analyzes conversation history and determines whether the current therapy stage
is complete and should advance to the next stage. It follows Solution-Focused Brief Therapy
(SFBT) principles and ensures safe progression through the 5-stage therapy workflow.

Key responsibilities:
- Evaluate stage completion based on conversation context
- Make stage advancement decisions (stay/advance)
- Apply safety checks to all decisions
- Provide structured reasoning for decisions
"""
import time
from typing import List, Dict, Any
from ..llm.base import LLMProvider
from ..core.services import PromptService, ParsingService, SafetyService, MemoryService
from ..core.models.schemas import MessageData, SupervisorDecision
from .interfaces.async_agent_interface import IAsyncSupervisorAgent
from .base_agent import AgentBase


class SupervisorAgent(AgentBase, IAsyncSupervisorAgent):
    """
    SupervisorAgent for therapy stage evaluation and progression decisions.

    This agent uses dependency injection to handle all infrastructure concerns
    while focusing solely on the business logic of stage evaluation. Inherits
    shared infrastructure from AgentBase.
    """

    # =====================================================================================
    # AGENT CONFIGURATION (IMPLEMENTATION OF ABSTRACT METHODS)
    # =====================================================================================

    def __init__(self,
                 llm_provider: LLMProvider,
                 prompt_service: PromptService,
                 parsing_service: ParsingService,
                 safety_service: SafetyService,
                 memory_service: MemoryService,
                 logger=None):
        """
        Initialize SupervisorAgent with injected dependencies.

        Args:
            llm_provider: LLM provider for generating responses (OpenAI/Gemini)
            prompt_service: Service for managing and building prompts
            parsing_service: Service for parsing and validating LLM responses
            safety_service: Service for applying safety checks and validations
            memory_service: Service for managing LLM memory and context optimization
            logger: Optional logger for tracking agent operations
        """
        # Store parsing service for supervisor-specific functionality
        self._parsing_service = parsing_service

        # Initialize base agent with shared infrastructure
        super().__init__(llm_provider, prompt_service, safety_service, memory_service, logger, "supervisor")

    def _get_default_agent_type(self) -> str:
        """Get the default agent type identifier for supervisor."""
        return "supervisor"

    def _configure_agent_specific_features(self) -> None:
        """
        Configure supervisor-specific features during initialization.

        Supervisor configures structured output for consistent decision objects,
        enabling reliable JSON parsing of evaluation decisions.
        """
        provider_class = self._llm_provider.__class__.__name__

        if provider_class == 'OpenAIProvider':
            # Configure OpenAI structured output if supported
            if hasattr(self._llm_provider, 'set_default_response_format'):
                from ..core.models.schemas import SupervisorDecision
                response_format = SupervisorDecision.get_openai_response_format()
                self._llm_provider.set_default_response_format(response_format)
                if self._logger:
                    self._logger.log_info("OpenAI structured output configured", {
                        "provider": "OpenAI",
                        "feature": "structured_output",
                        "agent_type": "supervisor"
                    })

        elif provider_class == 'GeminiProvider':
            # Configure Gemini structured output if supported
            if hasattr(self._llm_provider, 'set_default_response_schema'):
                from ..core.models.schemas import SupervisorDecision
                response_schema = SupervisorDecision.get_gemini_response_schema()
                self._llm_provider.set_default_response_schema(response_schema)
                if self._logger:
                    self._logger.log_info("Gemini structured output configured", {
                        "provider": "Gemini",
                        "feature": "structured_output",
                        "agent_type": "supervisor"
                    })

    def _should_log_stage_transitions(self) -> bool:
        """Supervisor logs stage transitions as the authority on stage progression."""
        return True

    def _log_agent_request(self, prompt_data: Dict[str, Any]) -> None:
        """Log supervisor-specific request data."""
        self._logger.log_supervisor_request(prompt_data)

    def _log_full_prompt_request(self, stage: str, full_prompt: str, history: List[MessageData]) -> None:
        """Log complete prompt content sent to LLM for debugging."""
        if self._logger:
            # Create summary of conversation history for context
            history_summary = f"{len(history)} messages" if history else "no history"
            last_message = history[-1].text if history else "none"

            prompt_data = {
                "id": f"supervisor_{stage}",
                "stage": stage,
                "history_summary": history_summary,
                "last_user_message": last_message,
                "full_prompt": full_prompt,
                "prompt_length": len(full_prompt)
            }
            self._logger.log_supervisor_request(prompt_data)

    # =====================================================================================
    # PUBLIC API - MAIN BUSINESS METHODS
    # =====================================================================================

    def evaluate_stage_completion(
            self,
            stage: str,
            history: List[MessageData],
            stage_prompt: str ) -> SupervisorDecision:
        """
        Evaluate whether the current therapy stage is complete and should advance.

        This is the main business method that orchestrates the entire evaluation process:
        1. Configure prompts for the current stage
        2. Build supervisor prompt with conversation context
        3. Generate LLM evaluation
        4. Process and validate the decision
        5. Apply safety checks

        Args:
            stage: Current therapy stage ID (e.g., 'opening', 'resources', 'scaling')
            history: List of conversation messages for context analysis
            stage_prompt: Stage-specific prompt defining evaluation criteria

        Returns:
            SupervisorDecision with evaluation results and advancement recommendation
        """
        start_time = time.time()

        try:
            # Step 1: Ensure prompts are properly configured for this stage
            self._ensure_prompts_configured(stage, stage_prompt)

            # Step 2: Build comprehensive supervisor prompt with conversation context
            supervisor_prompt = self._build_supervisor_prompt(stage, history)

            # Step 3: Log the evaluation request with FULL PROMPT CONTENT for debugging
            self._log_full_prompt_request(stage, supervisor_prompt, history)

            # Step 4: Generate LLM evaluation (synchronous)
            response = self._llm_provider.generate_sync(prompt=supervisor_prompt)

            # Step 5: Process response into structured decision with safety validation
            final_decision = self._process_supervisor_response(response, history)

            # Step 6: Log the completed evaluation with timing
            response_time_ms = self._calculate_response_time(start_time)
            self._log_supervisor_response(final_decision, response_time_ms)

            return final_decision

        except Exception as e:
            # Handle any errors with safe fallback decision
            return self._handle_evaluation_error(e)

    async def evaluate_stage_completion_async(self,
                                             stage: str,
                                             history: List[MessageData],
                                             stage_prompt: str) -> SupervisorDecision:
        """
        Asynchronous version of stage completion evaluation.

        Identical business logic to evaluate_stage_completion() but uses async LLM calls
        for better performance in concurrent scenarios.

        Args:
            stage: Current therapy stage ID
            history: Conversation message history
            stage_prompt: Stage-specific evaluation prompt

        Returns:
            SupervisorDecision with evaluation results
        """
        start_time = time.time()

        try:
            self._ensure_prompts_configured(stage, stage_prompt)
            supervisor_prompt = self._build_supervisor_prompt(stage, history)
            self._log_full_prompt_request(stage, supervisor_prompt, history)

            # Async LLM call - main difference from sync version
            response = await self._llm_provider.generate(prompt=supervisor_prompt)
            final_decision = self._process_supervisor_response(response, history)

            response_time_ms = self._calculate_response_time(start_time)
            self._log_supervisor_response(final_decision, response_time_ms)

            return final_decision

        except Exception as e:
            return self._handle_evaluation_error(e)

    async def generate_response_async(self,
                                     user_message: str,
                                     stage_prompt: str,
                                     conversation_history: List[MessageData],
                                     stage_id: str = None) -> Dict[str, Any]:
        """
        Generate general supervisor response asynchronously.

        This method provides a more general response generation capability,
        similar to TherapistAgent, for cases where a text response is needed
        rather than a structured decision.

        Args:
            user_message: The user's message to respond to
            stage_prompt: Stage-specific prompt for context
            conversation_history: Full conversation context
            stage_id: Optional stage identifier (defaults to current stage)

        Returns:
            Dict containing response text, success status, and metadata
        """
        start_time = time.time()

        try:
            self._ensure_prompts_configured(stage_id, stage_prompt)
            supervisor_prompt = self._build_supervisor_prompt(stage_id, conversation_history)
            self._log_request(stage_id)

            response = await self._llm_provider.generate(prompt=supervisor_prompt)
            return self._build_response_result(response, start_time)

        except Exception as e:
            return self._handle_response_error(e)

    # =====================================================================================
    # PRIVATE HELPER METHODS - SUPERVISOR-SPECIFIC BUSINESS LOGIC
    # =====================================================================================

    def _build_supervisor_prompt(self, stage: str, history: List[MessageData]) -> str:
        """
        Build comprehensive supervisor prompt from conversation context and safety considerations.

        This method combines multiple context sources to create a rich prompt:
        - Conversation history (limited to recent messages for token efficiency)
        - Safety context (crisis indicators, risk factors)
        - Stage-specific evaluation criteria

        Args:
            stage: Current therapy stage ID
            history: List of conversation messages

        Returns:
            Complete supervisor prompt ready for LLM
        """
        # Build conversation context with configurable token limit for performance optimization
        from config import Config
        config = Config.get_instance()
        conversation_context = self._build_conversation_context(history, max_messages=config.MAX_SUPERVISOR_CONTEXT_MESSAGES)

        # Build safety context to identify potential risks or crisis indicators
        safety_context = self._build_safety_context(history)

        # Combine all contexts into final supervisor prompt
        return self._prompt_service.build_supervisor_prompt(stage, conversation_context, safety_context)

    def _process_supervisor_response(self, response: str, history: List[MessageData]) -> SupervisorDecision:
        """
        Process raw LLM response into validated SupervisorDecision object.

        This method handles the complete response processing pipeline:
        1. Parse JSON response into structured data
        2. Create SupervisorDecision object with validation
        3. Apply safety checks and risk assessment
        4. Return final validated decision

        Args:
            response: Raw LLM response text (should be JSON)
            history: Conversation history for safety validation context

        Returns:
            Validated SupervisorDecision object ready for use
        """
        # Parse JSON response into structured data
        parsed_data = self._parsing_service.parse_supervisor_response(response)

        # Create initial decision object (with validation)
        decision = self._parsing_service.create_supervisor_decision(parsed_data)

        # Apply safety checks and return final decision (may override decision if risks detected)
        return self._safety_service.apply_safety_to_decision(decision, history)

    def _build_response_result(self, response: str, start_time: float) -> Dict[str, Any]:
        """
        Build successful response result dictionary for async response generation.

        Args:
            response: LLM response text
            start_time: Request start time for calculating response duration

        Returns:
            Formatted response dictionary with metadata
        """
        response_time_ms = self._calculate_response_time(start_time)
        # Clean escaped newlines for proper display
        clean_response = self._clean_response_text(response)

        return {
            "response": clean_response,
            "original_response": response,
            "success": True,
            "error": None,
            "response_time_ms": response_time_ms
        }

    def _log_supervisor_response(self, decision: SupervisorDecision, response_time_ms: int) -> None:
        """
        Log supervisor decision with performance metrics.

        Args:
            decision: The supervisor decision to log
            response_time_ms: Response generation time in milliseconds
        """
        if self._logger:
            self._logger.log_supervisor_response(decision, response_time_ms)

    def _handle_evaluation_error(self, error: Exception) -> SupervisorDecision:
        """
        Handle evaluation errors and return safe fallback decision.

        When evaluation fails, we must return a safe decision that:
        - Keeps the user in the current stage (no advancement)
        - Provides clear error messaging
        - Maintains formal addressing
        - Includes error details for debugging

        Args:
            error: The exception that occurred during evaluation

        Returns:
            Safe fallback SupervisorDecision
        """
        self._log_operation_error("evaluation", error)

        # Return safe fallback - always "stay" to prevent incorrect stage advancement
        return SupervisorDecision(
            decision="stay",  # Safe choice - don't advance on errors
            summary=f"Błąd w ocenie nadzorcy: {str(error)}",
            addressing="formal",  # Maintain formal tone during errors
            reason=f"Błąd w ocenie nadzorcy: {str(error)}",
            handoff={"error": str(error), "error_type": type(error).__name__},  # Debug info
            safety_risk=False,  # Error handling doesn't indicate safety risk
            safety_message=""
        )

    def _handle_response_error(self, error: Exception) -> Dict[str, Any]:
        """
        Handle response generation errors for async response method.

        Args:
            error: The exception that occurred during response generation

        Returns:
            Error response dictionary
        """
        self._log_operation_error("response generation", error)

        return {
            "response": f"[Błąd generowania odpowiedzi supervisora: {str(error)}]",
            "original_response": "",
            "success": False,
            "error": str(error)
        }