"""Service factory for dependency injection setup."""

from ..prompts.unified_prompt_manager import UnifiedPromptManager
from ...utils.safety import SafetyChecker
from .prompt_service import PromptService
from .parsing_service import ParsingService
from .safety_service import SafetyService
from .memory_service import MemoryService


class ServiceFactory:
    """Factory for creating and wiring services with proper dependencies."""

    @staticmethod
    def create_services(prompt_manager: UnifiedPromptManager,
                       safety_checker: SafetyChecker,
                       logger=None) -> tuple:
        """
        Create all services with proper dependencies.

        Returns:
            Tuple of (prompt_service, parsing_service, safety_service, memory_service)
        """
        # Create services
        prompt_service = PromptService(prompt_manager)
        parsing_service = ParsingService(logger)
        safety_service = SafetyService(safety_checker)
        memory_service = MemoryService(logger)

        return prompt_service, parsing_service, safety_service, memory_service

    @staticmethod
    def create_supervisor_agent(llm_provider, prompt_manager: UnifiedPromptManager,
                              safety_checker: SafetyChecker, logger=None):
        """Create fully configured SupervisorAgent with dependency injection."""
        from ...agents.supervisor import SupervisorAgent

        prompt_service, parsing_service, safety_service, memory_service = (
            ServiceFactory.create_services(prompt_manager, safety_checker, logger)
        )

        return SupervisorAgent(
            llm_provider=llm_provider,
            prompt_service=prompt_service,
            parsing_service=parsing_service,
            safety_service=safety_service,
            memory_service=memory_service,
            logger=logger
        )

    @staticmethod
    def create_therapist_agent(llm_provider, prompt_manager: UnifiedPromptManager,
                             safety_checker: SafetyChecker, logger=None):
        """Create fully configured TherapistAgent with dependency injection."""
        from ...agents.therapist import TherapistAgent

        prompt_service, parsing_service, safety_service, memory_service = (
            ServiceFactory.create_services(prompt_manager, safety_checker, logger)
        )

        return TherapistAgent(
            llm_provider=llm_provider,
            prompt_service=prompt_service,
            safety_service=safety_service,
            memory_service=memory_service,
            logger=logger
        )