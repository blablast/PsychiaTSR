"""Service factory for dependency injection setup."""

from ..di.service_locator import ServiceLocator
from ..prompts.unified_prompt_manager import UnifiedPromptManager
from ...core.safety import SafetyChecker
from .prompt_service import PromptService
from .parsing_service import ParsingService
from .safety_service import SafetyService
from .memory_service import MemoryService


class ServiceFactory:
    """Factory for creating and wiring services with proper dependencies."""

    @staticmethod
    def create_services(prompt_manager: UnifiedPromptManager = None,
                       safety_checker: SafetyChecker = None,
                       logger=None) -> tuple:
        """
        Create all services with proper dependencies using DI container.

        Returns:
            Tuple of (prompt_service, parsing_service, safety_service, memory_service)
        """
        # Resolve dependencies through DI if not provided
        if prompt_manager is None:
            prompt_manager = ServiceLocator.resolve(UnifiedPromptManager)
        if safety_checker is None:
            safety_checker = ServiceLocator.resolve(SafetyChecker)

        # Create services - DI container will handle dependencies automatically
        prompt_service = ServiceLocator.resolve(PromptService)
        parsing_service = ServiceLocator.resolve(ParsingService)
        safety_service = ServiceLocator.resolve(SafetyService)
        memory_service = ServiceLocator.resolve(MemoryService)

        return prompt_service, parsing_service, safety_service, memory_service

    @staticmethod
    def create_supervisor_agent(llm_provider, prompt_manager: UnifiedPromptManager = None,
                              safety_checker: SafetyChecker = None, logger=None):
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
    def create_therapist_agent(llm_provider, prompt_manager: UnifiedPromptManager = None,
                             safety_checker: SafetyChecker = None, logger=None):
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