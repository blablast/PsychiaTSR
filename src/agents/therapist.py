"""
TherapistAgent - Core business logic for generating therapeutic responses.

This agent generates empathetic, therapeutic responses following Solution-Focused Brief Therapy
(SFBT) principles. It handles the conversation flow within therapy sessions, ensuring responses
are contextually appropriate, safe, and therapeutic.

Key responsibilities:
- Generate therapeutic responses based on user input and conversation history
- Apply safety checks to user input and generated responses
- Support both synchronous and asynchronous response generation
- Provide streaming capabilities for real-time response delivery
- Maintain conversation context and stage-specific therapeutic approaches

The agent operates in 5 therapy stages:
1. Opening - Rapport building and goal setting
2. Resources - Identifying strengths and exceptions
3. Scaling - Using 1-10 scales to measure progress
4. Small Steps - Planning concrete actions
5. Summary - Reinforcement and closure
"""
import time
from typing import List, Dict, Any, AsyncGenerator
from ..core.models.schemas import MessageData
from .interfaces.async_agent_interface import IAsyncTherapistAgent
from .base_agent import AgentBase


class TherapistAgent(AgentBase, IAsyncTherapistAgent):
    """
    TherapistAgent for generating therapeutic responses using dependency injection.

    This agent focuses solely on the business logic of therapeutic response generation,
    inheriting shared infrastructure from AgentBase and implementing therapeutic-specific
    business methods.

    Example:
        >>> from src.core.services import ServiceFactory
        >>> therapist = ServiceFactory.create_therapist_agent(
        ...     llm_provider=openai_provider,
        ...     prompt_manager=prompt_manager,
        ...     safety_checker=safety_checker,
        ...     logger=logger
        ... )
        >>> result = therapist.generate_response(
        ...     user_message="Czuję się przygnębiony",
        ...     stage_prompt="Etap otwarcia...",
        ...     conversation_history=[],
        ...     stage_id="opening"
        ... )
    """

    # =====================================================================================
    # AGENT CONFIGURATION (IMPLEMENTATION OF ABSTRACT METHODS)
    # =====================================================================================

    def _get_default_agent_type(self) -> str:
        """Get the default agent type identifier for therapist."""
        return "therapist"

    def _configure_agent_specific_features(self) -> None:
        """Configure therapist-specific features during initialization."""
        # Therapist doesn't need special provider configuration like supervisor
        # (supervisor configures structured output for decision objects)
        pass

    def _should_log_stage_transitions(self) -> bool:
        """Therapist does not log stage transitions to avoid duplication."""
        return False

    def _log_agent_request(self, prompt_data: Dict[str, Any]) -> None:
        """Log therapist-specific request data."""
        self._logger.log_therapist_request(prompt_data)

    def _log_full_prompt_request(self, stage_id: str, full_prompt: str, user_message: str) -> None:
        """Log complete prompt content sent to LLM for debugging."""
        if self._logger:
            prompt_data = {
                "id": f"therapist_{stage_id}",
                "stage": stage_id,
                "user_message": user_message,
                "full_prompt": full_prompt,
                "prompt_length": len(full_prompt)
            }
            self._logger.log_therapist_request(prompt_data)

    # =====================================================================================
    # PUBLIC API - MAIN BUSINESS METHODS
    # =====================================================================================

    def generate_response(self,
                         user_message: str,
                         stage_prompt: str,
                         conversation_history: List[MessageData],
                         stage_id: str = None) -> Dict[str, Any]:
        """
        Generate therapeutic response synchronously.

        This is the primary method for generating therapeutic responses in a blocking manner.
        Suitable for scenarios where immediate response is needed and async is not required.

        Args:
            user_message: The user's message requiring a therapeutic response
            stage_prompt: Stage-specific prompt defining therapeutic approach
            conversation_history: Previous conversation messages for context
            stage_id: Current therapy stage identifier (e.g., 'opening', 'scaling')

        Returns:
            Dict containing response text, validation results, safety checks, and metadata
        """
        start_time = time.time()

        try:
            # Step 1: Safety validation of user input (critical for therapy safety)
            safety_check = self._safety_service.check_user_input(user_message)

            # Step 2: Configure prompts for current stage (memory optimization)
            self._ensure_prompts_configured(stage_id, stage_prompt)

            # Step 3: Build comprehensive therapeutic prompt with context
            therapist_prompt = self._build_therapist_prompt(user_message, conversation_history)

            # Step 4: Log request with FULL PROMPT CONTENT for debugging
            self._log_full_prompt_request(stage_id, therapist_prompt, user_message)

            # Step 5: Generate LLM response (synchronous)
            response = self._llm_provider.generate_sync(prompt=therapist_prompt)

            # Step 6: Process and validate the complete response
            return self._build_success_response(response, safety_check, start_time)

        except Exception as e:
            # Handle errors with safe fallback response
            return self._handle_response_error(e, locals().get('safety_check'))

    def generate_response_stream(self,
                               user_message: str,
                               stage_prompt: str,
                               conversation_history: List[MessageData],
                               stage_id: str = None) -> Any:
        """
        Generate therapeutic response with real-time streaming.

        This method streams response chunks as they are generated, providing immediate
        feedback to users. Essential for responsive UX in therapy applications.

        Args:
            user_message: The user's message requiring a therapeutic response
            stage_prompt: Stage-specific prompt defining therapeutic approach
            conversation_history: Previous conversation messages for context
            stage_id: Current therapy stage identifier

        Yields:
            Response chunks as strings, followed by final metadata dictionary
        """
        start_time = time.time()

        try:
            safety_check = self._safety_service.check_user_input(user_message)
            self._ensure_prompts_configured(stage_id, stage_prompt)
            therapist_prompt = self._build_therapist_prompt(user_message, conversation_history)
            self._log_full_prompt_request(stage_id, therapist_prompt, user_message)

            # Stream response chunks in real-time
            full_response = ""
            stream = self._llm_provider.generate_stream(prompt=therapist_prompt)
            first_chunk_time = None

            for chunk in stream:
                # Record first chunk timing
                if first_chunk_time is None:
                    first_chunk_time = self._calculate_response_time(start_time)

                full_response += chunk
                yield chunk  # Real-time chunk delivery

            # Yield final metadata for completion handling
            metadata = self._build_streaming_metadata(full_response, safety_check, start_time, first_chunk_time)
            yield metadata

        except Exception as e:
            # Yield error chunks for UI display
            yield from self._handle_streaming_error(e, locals().get('safety_check'))

    async def generate_response_async(self,
                                     user_message: str,
                                     stage_prompt: str,
                                     conversation_history: List[MessageData],
                                     stage_id: str = None) -> Dict[str, Any]:
        """
        Generate therapeutic response asynchronously.

        Identical business logic to generate_response() but uses async LLM calls
        for better performance in concurrent scenarios and async frameworks.

        Args:
            user_message: The user's message requiring a therapeutic response
            stage_prompt: Stage-specific prompt defining therapeutic approach
            conversation_history: Previous conversation messages for context
            stage_id: Current therapy stage identifier

        Returns:
            Dict containing response text, validation results, safety checks, and metadata
        """
        start_time = time.time()

        try:
            safety_check = self._safety_service.check_user_input(user_message)
            self._ensure_prompts_configured(stage_id, stage_prompt)
            therapist_prompt = self._build_therapist_prompt(user_message, conversation_history)
            self._log_full_prompt_request(stage_id, therapist_prompt, user_message)

            # Async LLM call - main difference from sync version
            response = await self._llm_provider.generate(prompt=therapist_prompt)
            return self._build_success_response(response, safety_check, start_time)

        except Exception as e:
            return self._handle_response_error(e, locals().get('safety_check'))

    async def generate_streaming_response_async(self,
                                               user_message: str,
                                               stage_prompt: str,
                                               conversation_history: List[MessageData],
                                               stage_id: str = None) -> AsyncGenerator[Any, None]:
        """
        Generate streaming therapeutic response asynchronously.

        Combines the benefits of async execution with real-time streaming.
        Ideal for async web frameworks like FastAPI or async Streamlit components.

        Args:
            user_message: The user's message requiring a therapeutic response
            stage_prompt: Stage-specific prompt defining therapeutic approach
            conversation_history: Previous conversation messages for context
            stage_id: Current therapy stage identifier

        Yields:
            Response chunks as strings, followed by final metadata dictionary
        """
        start_time = time.time()

        try:
            safety_check = self._safety_service.check_user_input(user_message)
            self._ensure_prompts_configured(stage_id, stage_prompt)
            therapist_prompt = self._build_therapist_prompt(user_message, conversation_history)
            self._log_full_prompt_request(stage_id, therapist_prompt, user_message)

            # Async streaming - combines async + streaming benefits
            full_response = ""
            stream = self._llm_provider.generate_stream_async(prompt=therapist_prompt)

            async for chunk in stream:
                full_response += chunk
                yield chunk  # Real-time async chunk delivery

            # Yield final metadata
            yield self._build_streaming_metadata(full_response, safety_check, start_time)

        except Exception as e:
            # Async error handling with streaming
            async for error_chunk in self._handle_async_streaming_error(e, locals().get('safety_check')):
                yield error_chunk

    # =====================================================================================
    # PRIVATE HELPER METHODS - THERAPIST-SPECIFIC BUSINESS LOGIC
    # =====================================================================================

    def _build_therapist_prompt(self, user_message: str, conversation_history: List[MessageData]) -> str:
        """
        Build comprehensive therapeutic prompt from user message and conversation context.

        This method combines the user's current message with conversation history
        to create a rich context for therapeutic response generation.

        Args:
            user_message: The current user message to respond to
            conversation_history: List of previous conversation messages

        Returns:
            Complete therapeutic prompt ready for LLM processing
        """
        # Build conversation context for therapeutic continuity (configurable limit for performance)
        from config import Config
        conversation_context = self._build_conversation_context(conversation_history, max_messages=Config.MAX_THERAPIST_CONTEXT_MESSAGES)

        # Combine user message and context into therapeutic prompt
        return self._prompt_service.build_therapist_prompt(user_message, conversation_context)

    def _build_success_response(self, response: str, safety_check: Dict, start_time: float) -> Dict[str, Any]:
        """
        Build successful response result with validation and performance metrics.

        This method processes the raw LLM response into a complete response object
        with safety validation, performance metrics, and metadata.

        Args:
            response: Raw LLM response text
            safety_check: Safety validation results from user input
            start_time: Request start time for performance measurement

        Returns:
            Complete response dictionary with all metadata
        """
        # Validate response for therapeutic appropriateness and safety
        validation = self._safety_service.validate_therapist_response(response)

        # Clean response text for proper display (handle escaped characters)
        clean_response = self._clean_response_text(response)

        # Calculate response performance metrics
        response_time_ms = self._calculate_response_time(start_time)

        # Log successful response for monitoring
        if self._logger:
            self._logger.log_therapist_response(clean_response, response_time_ms)

        return {
            "response": clean_response,           # Cleaned response text for display
            "original_response": response,        # Raw LLM response for debugging
            "safety_check": safety_check,         # User input safety validation
            "validation": validation,             # Response safety validation
            "success": True,                      # Success indicator
            "error": None,                        # No error occurred
            "response_time_ms": response_time_ms  # Performance metric
        }

    def _build_streaming_metadata(self, full_response: str, safety_check: Dict, start_time: float, first_chunk_time_ms: int = None) -> Dict[str, Any]:
        """
        Build metadata for streaming response completion.

        This method creates the final metadata object that is yielded after
        all streaming chunks have been delivered.

        Args:
            full_response: Complete assembled response from all chunks
            safety_check: Safety validation results from user input
            start_time: Request start time for performance measurement

        Returns:
            Complete metadata dictionary for streaming completion
        """
        # Validate complete response (important for streaming safety)
        validation = self._safety_service.validate_therapist_response(full_response)
        clean_response = self._clean_response_text(full_response)
        response_time_ms = self._calculate_response_time(start_time)

        # Log streaming completion with first chunk timing if available
        if self._logger:
            self._logger.log_therapist_response(clean_response, response_time_ms, first_chunk_time_ms)

        return {
            "response": clean_response,
            "original_response": full_response,
            "safety_check": safety_check,
            "validation": validation,
            "success": True,
            "error": None,
            "response_time_ms": response_time_ms
        }

    def _handle_response_error(self, error: Exception, safety_check: Dict) -> Dict[str, Any]:
        """
        Handle response generation errors with safe fallback.

        When response generation fails, we must provide a safe error response
        that maintains the therapeutic relationship while providing debugging info.

        Args:
            error: The exception that occurred during response generation
            safety_check: Safety validation results (may be None if error occurred early)

        Returns:
            Safe error response dictionary
        """
        self._log_operation_error("response generation", error)

        return {
            "response": f"[Błąd generowania odpowiedzi: {str(error)}]",  # User-friendly error
            "original_response": "",                                      # No response generated
            "safety_check": safety_check or {"has_risk": False},         # Use existing or safe default
            "validation": {"is_valid": False, "issues": [str(error)]},   # Mark as invalid with error
            "success": False,                                             # Indicate failure
            "error": str(error)                                           # Technical error details
        }

    def _handle_streaming_error(self, error: Exception, safety_check: Dict):
        """
        Handle streaming response errors with user-visible error messages.

        For streaming responses, we yield both a user-visible error message
        and error metadata for proper error handling.

        Args:
            error: The exception that occurred during streaming
            safety_check: Safety validation results (may be None)

        Yields:
            Error message string followed by error metadata dictionary
        """
        self._log_operation_error("streaming response", error)

        # Yield user-visible error message for immediate display
        yield f"[Błąd generowania odpowiedzi: {str(error)}]"

        # Yield error metadata for completion handling
        yield {
            "response": "",
            "original_response": "",
            "safety_check": safety_check or {"has_risk": False},
            "validation": {"is_valid": False, "issues": [str(error)]},
            "success": False,
            "error": str(error)
        }

    async def _handle_async_streaming_error(self, error: Exception, safety_check: Dict):
        """
        Handle async streaming response errors.

        Async version of streaming error handling for async generators.

        Args:
            error: The exception that occurred during async streaming
            safety_check: Safety validation results (may be None)

        Yields:
            Error message string followed by error metadata dictionary
        """
        self._log_operation_error("async streaming response", error)

        # Async yield of error message and metadata
        yield f"[Błąd generowania odpowiedzi: {str(error)}]"
        yield {
            "response": "",
            "original_response": "",
            "safety_check": safety_check or {"has_risk": False},
            "validation": {"is_valid": False, "issues": [str(error)]},
            "success": False,
            "error": str(error)
        }