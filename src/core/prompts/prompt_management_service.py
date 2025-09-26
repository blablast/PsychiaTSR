"""
Refactored PromptManagementService - Clean facade using focused services.

Old: 786-line God class with 10+ responsibilities
New: ~100-line orchestrator using specialized services
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from .prompt_repository import SystemPromptRepository, StagePromptRepository
from .prompt_validator import PromptValidator
from .prompt_formatter import PromptFormatter
from .prompt_query_service import PromptQueryService


class PromptManagementService:
    """
    Clean prompt management service using focused components.

    Acts as a facade orchestrating specialized services:
    - PromptRepository: Data access
    - PromptValidator: Validation logic
    - PromptFormatter: Text formatting
    - PromptQueryService: Complex queries
    """

    def __init__(self, config_dir: str = "config", logger=None):
        """Initialize service with focused components."""
        self.config_dir = Path(config_dir)
        self.logger = logger

        # Initialize focused services
        self.system_repo = SystemPromptRepository(config_dir, logger)
        self.stage_repo = StagePromptRepository(config_dir, logger)
        self.validator = PromptValidator()
        self.formatter = PromptFormatter()
        self.query_service = PromptQueryService(self.system_repo, self.stage_repo)

    # =====================================================================================
    # SYSTEM PROMPT OPERATIONS
    # =====================================================================================

    def get_active_system_prompt(self, agent_type: str) -> Dict[str, Any]:
        """Get active system prompt for agent type."""
        # Validate agent type
        is_valid, error = self.validator.validate_agent_type(agent_type)
        if not is_valid:
            if self.logger:
                self.logger.error(f"Invalid agent type '{agent_type}': {error}")
            return self._create_fallback_system_prompt(agent_type)

        # Get from repository
        prompt = self.system_repo.get_active_prompt(agent_type)
        if prompt:
            return prompt

        # Return fallback
        if self.logger:
            self.logger.warning(f"No active system prompt found for {agent_type}")
        return self._create_fallback_system_prompt(agent_type)

    def save_system_prompt(self, agent_type: str, prompt_data: Dict[str, Any]) -> bool:
        """Save system prompt with validation."""
        # Validate agent type
        is_valid, error = self.validator.validate_agent_type(agent_type)
        if not is_valid:
            if self.logger:
                self.logger.error(f"Invalid agent type '{agent_type}': {error}")
            return False

        # Validate prompt structure
        is_valid, errors = self.validator.validate_system_prompt(prompt_data, agent_type)
        if not is_valid:
            if self.logger:
                self.logger.error(f"System prompt validation failed: {'; '.join(errors)}")
            return False

        # Save through repository
        return self.system_repo.save_prompt(agent_type, prompt_data)

    def get_system_prompt_by_key(self, prompt_key: str) -> Optional[Dict[str, Any]]:
        """Get system prompt by database key."""
        return self.system_repo.get_prompt_by_key(prompt_key)

    def list_all_system_prompts(self) -> List[Dict[str, Any]]:
        """List all system prompts."""
        return self.system_repo.list_all_prompts()

    def list_system_prompt_versions(self, agent_type: str) -> List[Dict[str, Any]]:
        """List all versions of system prompts for agent."""
        return self.system_repo.list_versions(agent_type)

    # =====================================================================================
    # STAGE PROMPT OPERATIONS
    # =====================================================================================

    def get_active_stage_prompt(self, stage_id: str, agent_type: str) -> Dict[str, Any]:
        """Get active stage prompt for stage and agent."""
        # Validate inputs
        is_valid, error = self.validator.validate_agent_type(agent_type)
        if not is_valid:
            if self.logger:
                self.logger.error(f"Invalid agent type '{agent_type}': {error}")
            return self._create_fallback_stage_prompt(stage_id, agent_type)

        is_valid, error = self.validator.validate_stage_id(stage_id)
        if not is_valid:
            if self.logger:
                self.logger.error(f"Invalid stage ID '{stage_id}': {error}")
            return self._create_fallback_stage_prompt(stage_id, agent_type)

        # Get from repository
        prompt = self.stage_repo.get_active_prompt(stage_id, agent_type)
        if prompt:
            return prompt

        # Return fallback
        if self.logger:
            self.logger.warning(f"No active stage prompt found for {stage_id}/{agent_type}")
        return self._create_fallback_stage_prompt(stage_id, agent_type)

    def save_stage_prompt(
        self, stage_id: str, agent_type: str, prompt_data: Dict[str, Any]
    ) -> bool:
        """Save stage prompt with validation."""
        # Validate inputs
        is_valid, error = self.validator.validate_agent_type(agent_type)
        if not is_valid:
            if self.logger:
                self.logger.error(f"Invalid agent type '{agent_type}': {error}")
            return False

        is_valid, error = self.validator.validate_stage_id(stage_id)
        if not is_valid:
            if self.logger:
                self.logger.error(f"Invalid stage ID '{stage_id}': {error}")
            return False

        # Validate prompt structure
        is_valid, errors = self.validator.validate_stage_prompt(prompt_data, stage_id, agent_type)
        if not is_valid:
            if self.logger:
                self.logger.error(f"Stage prompt validation failed: {'; '.join(errors)}")
            return False

        # Save through repository
        return self.stage_repo.save_prompt(stage_id, agent_type, prompt_data)

    def get_stage_prompt_by_key(self, prompt_key: str) -> Optional[Dict[str, Any]]:
        """Get stage prompt by database key."""
        return self.stage_repo.get_prompt_by_key(prompt_key)

    def get_all_stage_prompts_for_agent(self, agent_type: str) -> List[Dict[str, Any]]:
        """Get all stage prompts for agent."""
        return self.stage_repo.get_all_for_agent(agent_type)

    def get_all_stage_prompts_for_stage(self, stage_id: str) -> List[Dict[str, Any]]:
        """Get all stage prompts for stage."""
        return self.stage_repo.get_all_for_stage(stage_id)

    def list_all_stage_prompts(self) -> List[Dict[str, Any]]:
        """List all stage prompts."""
        return self.stage_repo.list_all_prompts()

    # =====================================================================================
    # FORMATTING AND UTILITY OPERATIONS
    # =====================================================================================

    def generate_prompt_text(self, prompt_data: Dict[str, Any], prompt_type: str = "stage") -> str:
        """Generate final prompt text from structured data."""
        return self.formatter.generate_prompt_text(prompt_data, prompt_type)

    def validate_prompt_structure(self, prompt_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate prompt data structure."""
        return self.validator.validate_prompt_structure(prompt_data)

    def format_prompt_summary(self, prompt_data: Dict[str, Any]) -> str:
        """Generate brief prompt summary."""
        return self.formatter.format_prompt_summary(prompt_data)

    def format_metadata_display(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Format metadata for UI display."""
        return self.formatter.format_metadata_display(metadata)

    # =====================================================================================
    # ADVANCED QUERY OPERATIONS
    # =====================================================================================

    def search_prompts(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search prompts by text content."""
        return self.query_service.search_prompts(query, **kwargs)

    def get_prompts_by_status(self, status: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get all prompts with specific status."""
        return self.query_service.get_prompts_by_status(status)

    def get_agent_prompt_summary(self, agent_type: str) -> Dict[str, Any]:
        """Get comprehensive summary for agent."""
        return self.query_service.get_agent_prompt_summary(agent_type)

    def find_duplicate_prompts(self, similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Find potentially duplicate prompts."""
        return self.query_service.find_duplicates(similarity_threshold)

    # =====================================================================================
    # FALLBACK METHODS (Unchanged from original)
    # =====================================================================================

    def _create_fallback_system_prompt(self, agent_type: str) -> Dict[str, Any]:
        """Create fallback system prompt."""
        from datetime import datetime

        return {
            "metadata": {
                "id": 999,
                "agent": agent_type,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "active",
                "note": f"Fallback {agent_type} system prompt",
            },
            "configuration": {
                "sections": {
                    "ai_role": {
                        "title": "1. Rola AI",
                        "content": f"System prompt dla {agent_type} - skonfiguruj w bazie danych",
                    }
                }
            },
        }

    def _create_fallback_stage_prompt(self, stage_id: str, agent_type: str) -> Dict[str, Any]:
        """Create fallback stage prompt."""
        from datetime import datetime

        return {
            "metadata": {
                "id": 998,
                "agent": agent_type,
                "stage": stage_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "active",
                "note": f"Fallback {agent_type} stage {stage_id} prompt",
            },
            "configuration": {
                "sections": {
                    "placeholder": {
                        "title": f"Etap {stage_id} - {agent_type}",
                        "content": f"Prompt etapowy - skonfiguruj w bazie danych",
                    }
                }
            },
        }
