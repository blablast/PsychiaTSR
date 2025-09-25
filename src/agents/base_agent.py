"""
AgentBase - Shared infrastructure for therapy agents.

This base class provides common functionality for all therapy agents, eliminating
code duplication and ensuring consistent behavior across different agent types.

Key shared responsibilities:
- Prompt management and memory optimization
- Logging and performance monitoring
- Error handling and safe fallbacks
- LLM provider interaction patterns
- Stage transition management

Concrete agents (TherapistAgent, SupervisorAgent) inherit this foundation
and implement their specific business logic.
"""
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from ..llm.base import LLMProvider
from ..core.services import PromptService, SafetyService, MemoryService
from ..core.models.schemas import MessageData


class AgentBase(ABC):
    """
    Base class for therapy agents providing shared infrastructure.

    This abstract base class handles all common agent concerns:
    - Dependency injection setup
    - Prompt configuration and memory optimization
    - Logging and performance monitoring
    - Error handling patterns
    - Stage transition management

    Concrete agent classes inherit this foundation and implement
    their specific business logic through abstract methods.
    """

    # =====================================================================================
    # INITIALIZATION AND CONFIGURATION
    # =====================================================================================

    def __init__(self,
                 llm_provider: LLMProvider,
                 prompt_service: PromptService,
                 safety_service: SafetyService,
                 memory_service: MemoryService,
                 logger=None,
                 agent_type: str = None):
        """
        Initialize agent with injected dependencies and agent type.

        Args:
            llm_provider: LLM provider for generating responses (OpenAI/Gemini)
            prompt_service: Service for managing and building prompts
            safety_service: Service for safety validation and checks
            memory_service: Service for managing LLM memory and context optimization
            logger: Optional logger for tracking agent operations
            agent_type: Type identifier for this agent ("therapist", "supervisor")
        """
        # Core dependencies - injected services
        self._llm_provider = llm_provider
        self._prompt_service = prompt_service
        self._safety_service = safety_service
        self._memory_service = memory_service
        self._logger = logger

        # Agent identification
        self._agent_type = agent_type or self._get_default_agent_type()

        # Shared agent state tracking
        self._current_stage_id: Optional[str] = None  # Currently active therapy stage
        self._system_prompt_set: bool = False         # Whether system prompt has been configured
        self._stage_prompt_set: bool = False          # Whether stage-specific prompt has been set

        # Allow concrete agents to perform additional configuration
        self._configure_agent_specific_features()

    @abstractmethod
    def _get_default_agent_type(self) -> str:
        """
        Get the default agent type identifier.

        Returns:
            Agent type string (e.g., "therapist", "supervisor")
        """
        pass

    @abstractmethod
    def _configure_agent_specific_features(self) -> None:
        """
        Configure agent-specific features during initialization.

        Override this method to perform agent-specific setup like
        structured output configuration, provider-specific features, etc.
        """
        pass

    # =====================================================================================
    # SHARED INFRASTRUCTURE - PROMPT MANAGEMENT
    # =====================================================================================

    def _ensure_prompts_configured(self, stage_id: str, stage_prompt: str) -> None:
        """
        Ensure system and stage prompts are properly configured for the LLM provider.

        This method handles memory optimization by setting prompts only when necessary:
        - System prompt: Set once per session (contains general agent guidelines)
        - Stage prompt: Updated only when therapy stage changes
        - Logs stage transitions for monitoring

        Args:
            stage_id: Current therapy stage identifier
            stage_prompt: Stage-specific prompt text for agent guidance
        """
        # Configure system prompt once per session (memory optimization)
        self._setup_system_prompt()

        # Handle stage transitions - only update when stage actually changes
        if self._current_stage_id != stage_id:
            self._handle_stage_transition(stage_id)

        # Configure stage-specific prompt if not already set for current stage
        if not self._stage_prompt_set and stage_prompt:
            self._setup_stage_prompt(stage_prompt, stage_id)

    def _setup_system_prompt(self) -> None:
        """Set up system prompt once per session for memory optimization."""
        if not self._system_prompt_set:
            system_prompt = self._prompt_service.get_system_prompt(self._agent_type)
            if system_prompt:
                self._memory_service.setup_system_prompt(self._llm_provider, system_prompt, self._agent_type)
                self._system_prompt_set = True

    def _handle_stage_transition(self, stage_id: str) -> None:
        """
        Handle therapy stage transitions with proper logging and state management.

        Args:
            stage_id: New therapy stage identifier
        """
        # Log stage transition for monitoring (important for therapy progression tracking)
        if self._logger and self._should_log_stage_transitions():
            self._logger.log_stage_transition(self._current_stage_id or "none", stage_id)

        # Update internal state and mark stage prompt as needing refresh
        self._current_stage_id = stage_id
        self._stage_prompt_set = False

    def _setup_stage_prompt(self, stage_prompt: str, stage_id: str) -> None:
        """
        Configure stage-specific prompt for current therapy stage.

        Args:
            stage_prompt: Stage-specific prompt text
            stage_id: Current therapy stage identifier
        """
        self._memory_service.setup_stage_prompt(self._llm_provider, stage_prompt, stage_id, self._agent_type)
        self._stage_prompt_set = True

    @abstractmethod
    def _should_log_stage_transitions(self) -> bool:
        """
        Determine if this agent should log stage transitions.

        Only supervisor typically logs stage transitions to avoid duplication.

        Returns:
            True if this agent should log stage transitions
        """
        pass

    # =====================================================================================
    # SHARED INFRASTRUCTURE - LOGGING
    # =====================================================================================

    def _log_request(self, stage_id: str) -> None:
        """
        Log agent request with minimal data to avoid performance issues.

        Logs only essential metadata for monitoring without fetching full prompts
        every time, which was causing performance problems in the original implementation.

        Args:
            stage_id: Current therapy stage being processed
        """
        if self._logger:
            # Log minimal data - avoid fetching full prompts every time for performance
            prompt_data = {"id": f"{self._agent_type}_{stage_id}", "stage": stage_id}
            self._log_agent_request(prompt_data)

    @abstractmethod
    def _log_agent_request(self, prompt_data: Dict[str, Any]) -> None:
        """
        Log agent-specific request data.

        Args:
            prompt_data: Minimal prompt data for logging
        """
        pass

    def _log_performance(self, operation: str, duration_ms: int, **metadata) -> None:
        """
        Log performance metrics for agent operations.

        Args:
            operation: Name of the operation being measured
            duration_ms: Operation duration in milliseconds
            **metadata: Additional metadata to log
        """
        if self._logger:
            perf_data = {
                "agent_type": self._agent_type,
                "operation": operation,
                "duration_ms": duration_ms,
                **metadata
            }
            self._logger.log_info(f"{self._agent_type} {operation} completed", perf_data)

    def _log_operation_error(self, operation: str, error: Exception) -> None:
        """
        Log operation errors with consistent formatting.

        Args:
            operation: Name of the operation that failed
            error: The exception that occurred
        """
        if self._logger:
            self._logger.log_error(f"{self._agent_type} {operation} failed: {str(error)}")

    # =====================================================================================
    # SHARED INFRASTRUCTURE - ERROR HANDLING
    # =====================================================================================

    def _create_error_metadata(self, error: Exception, safety_check: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create standardized error metadata for consistent error responses.

        Args:
            error: The exception that occurred
            safety_check: Optional safety validation results

        Returns:
            Standardized error metadata dictionary
        """
        return {
            "success": False,
            "error": str(error),
            "error_type": type(error).__name__,
            "agent_type": self._agent_type,
            "safety_check": safety_check or {"has_risk": False}
        }

    @staticmethod
    def _calculate_response_time(start_time: float) -> int:
        """
        Calculate response time in milliseconds.

        Args:
            start_time: Operation start time from time.time()

        Returns:
            Response time in milliseconds
        """
        return int((time.time() - start_time) * 1000)

    @staticmethod
    def _clean_response_text(response: str) -> str:
        """
        Clean response text for proper display.

        Args:
            response: Raw response text from LLM

        Returns:
            Cleaned response text with proper formatting
        """
        return response.replace('\\n', '\n')

    # =====================================================================================
    # SHARED INFRASTRUCTURE - CONTEXT BUILDING
    # =====================================================================================

    def _build_conversation_context(self, conversation_history: List[MessageData], max_messages: int = None) -> str:
        """
        Build optimized conversation context from message history with summarization support.

        Args:
            conversation_history: List of previous conversation messages
            max_messages: Optional limit on number of messages to include

        Returns:
            Formatted conversation context string (with summarization if enabled)
        """
        from config import Config

        # Use optimized context building with summarization if enabled
        if Config.ENABLE_CONVERSATION_SUMMARY and max_messages and len(conversation_history) > max_messages:
            return self._memory_service.build_optimized_conversation_context(
                conversation_history,
                max_messages=max_messages,
                enable_summarization=True
            )
        else:
            # Fallback to standard method
            return self._memory_service.build_conversation_context(conversation_history, max_messages=max_messages)

    def _build_safety_context(self, conversation_history: List[MessageData]) -> str:
        """
        Build safety context for risk assessment.

        Args:
            conversation_history: List of conversation messages

        Returns:
            Formatted safety context string
        """
        return self._safety_service.build_safety_context(conversation_history)

    # =====================================================================================
    # UTILITY METHODS
    # =====================================================================================

    def get_agent_type(self) -> str:
        """
        Get the agent type identifier.

        Returns:
            Agent type string
        """
        return self._agent_type

    def is_system_prompt_configured(self) -> bool:
        """
        Check if system prompt has been configured.

        Returns:
            True if system prompt is set
        """
        return self._system_prompt_set

    def get_current_stage(self) -> Optional[str]:
        """
        Get the currently active therapy stage.

        Returns:
            Current stage identifier or None if not set
        """
        return self._current_stage_id