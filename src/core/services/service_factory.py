"""Service factory using simple factory pattern instead of complex DI."""

from .simple_service_factory import SimpleServiceFactory


class ServiceFactory:
    """
    Backwards compatible service factory using SimpleServiceFactory.

    Simplified from complex DI container to simple factory pattern.
    """

    @staticmethod
    def create_services(prompt_manager=None, safety_checker=None, logger=None) -> tuple:
        """
        Create all services with proper dependencies using SimpleServiceFactory.

        Returns:
            Tuple of (prompt_service, parsing_service, safety_service, memory_service)
        """
        # Use SimpleServiceFactory instead of complex DI container
        agent_services = SimpleServiceFactory.create_agent_services()

        return (
            agent_services['prompt_service'],
            agent_services['parsing_service'],
            agent_services['safety_service'],
            agent_services['memory_service']
        )

    @staticmethod
    def create_supervisor_agent(llm_provider, prompt_manager=None, safety_checker=None, logger=None):
        """Create fully configured SupervisorAgent using SimpleServiceFactory."""
        from ...agents.supervisor import SupervisorAgent

        # Get services from SimpleServiceFactory
        prompt_service, parsing_service, safety_service, memory_service = (
            ServiceFactory.create_services()
        )

        # Use provided logger or create default
        if logger is None:
            logger = SimpleServiceFactory.create_logger()

        return SupervisorAgent(
            llm_provider=llm_provider,
            prompt_service=prompt_service,
            parsing_service=parsing_service,
            safety_service=safety_service,
            memory_service=memory_service,
            logger=logger
        )

    @staticmethod
    def create_therapist_agent(llm_provider, prompt_manager=None, safety_checker=None, logger=None):
        """Create fully configured TherapistAgent using SimpleServiceFactory."""
        from ...agents.therapist import TherapistAgent

        # Get services from SimpleServiceFactory
        prompt_service, parsing_service, safety_service, memory_service = (
            ServiceFactory.create_services()
        )

        # Use provided logger or create default
        if logger is None:
            logger = SimpleServiceFactory.create_logger()

        return TherapistAgent(
            llm_provider=llm_provider,
            prompt_service=prompt_service,
            safety_service=safety_service,
            memory_service=memory_service,
            logger=logger
        )