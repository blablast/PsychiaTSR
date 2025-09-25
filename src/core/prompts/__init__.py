"""Core prompts module for managing AI agent prompts."""

# New refactored services (preferred)
from .prompt_management_service import PromptManagementService
from .prompt_repository import SystemPromptRepository, StagePromptRepository
from .prompt_validator import PromptValidator
from .prompt_formatter import PromptFormatter
from .prompt_query_service import PromptQueryService

# Legacy managers (backwards compatibility)
from .system_prompt_manager import SystemPromptManager
from .stage_prompt_manager import StagePromptManager
from .unified_prompt_manager import UnifiedPromptManager

__all__ = [
    # New refactored services
    "PromptManagementService",
    "SystemPromptRepository",
    "StagePromptRepository",
    "PromptValidator",
    "PromptFormatter",
    "PromptQueryService",

    # Legacy managers (backwards compatibility)
    "SystemPromptManager",
    "StagePromptManager",
    "UnifiedPromptManager"
]
