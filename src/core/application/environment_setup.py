"""Environment setup for Psychia TSR application."""

import os
from dotenv import load_dotenv
from ..di.service_locator import ServiceLocator


class EnvironmentSetup:
    """Handles environment variable loading and system configuration."""

    @staticmethod
    def initialize():
        """Initialize environment variables and system settings."""
        # Load environment variables from .env file
        load_dotenv()

        # Optimize GPU memory allocation for HuggingFace models
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

        # Initialize dependency injection container
        ServiceLocator.initialize()
