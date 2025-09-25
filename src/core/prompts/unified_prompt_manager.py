"""
Unified prompt management orchestrating system and stage prompts.
Composes specialized managers for unified prompt access.
"""

from .system_prompt_manager import SystemPromptManager
from .stage_prompt_manager import StagePromptManager
from typing import Optional


class UnifiedPromptManager:
    """
    Orchestrates system and stage prompt managers to provide unified prompt access.

    Coordinates between SystemPromptManager and StagePromptManager
    to provide combined prompts for therapy workflow.
    """

    def __init__(self, prompts_base_dir: str):
        """
        Initialize with base prompts directory.

        Args:
            prompts_base_dir: Base path to prompts directory (now pointing to config dir)
        """

        # Adjust paths - our files are directly in config/ not config/prompts/
        config_dir = prompts_base_dir.replace("/prompts", "").replace("\\prompts", "")

        self._system_manager = SystemPromptManager(config_dir)  # SystemPromptManager handles system_prompts.json directly
        self._stage_manager = StagePromptManager(config_dir)   # StagePromptManager handles stage_prompts.json directly

    def get_full_prompt(self, stage_id: str, agent_type: str) -> Optional[str]:
        """
        Get complete prompt combining system and stage-specific prompts.

        Args:
            stage_id: Stage identifier (e.g., "opening")
            agent_type: "therapist" or "supervisor"

        Returns:
            Combined system + stage prompt or None if either component missing
        """
        # Get system prompt (base role and principles)
        system_prompt = self._system_manager.get_prompt(agent_type)
        if not system_prompt:
            return None

        # Get stage-specific prompt (goals, guidelines, examples)
        stage_prompt = self._stage_manager.get_prompt(stage_id, agent_type)
        if not stage_prompt:
            return None

        # Combine system and stage prompts
        return f"{system_prompt}\n\n{stage_prompt}"

    def get_system_prompt(self, agent_type: str) -> Optional[str]:
        """
        Get system prompt only.

        Args:
            agent_type: "therapist" or "supervisor"

        Returns:
            System prompt string or None if not found
        """
        return self._system_manager.get_prompt(agent_type)

    def get_stage_prompt(self, stage_id: str, agent_type: str) -> Optional[str]:
        """
        Get stage prompt only.

        Args:
            stage_id: Stage identifier
            agent_type: "therapist" or "supervisor"

        Returns:
            Stage prompt string or None if not found
        """
        result = self._stage_manager.get_prompt(stage_id, agent_type)
        return result

    def is_available(self, stage_id: str, agent_type: str) -> bool:
        """
        Check if complete prompt (system + stage) is available.

        Args:
            stage_id: Stage identifier
            agent_type: "therapist" or "supervisor"

        Returns:
            True if both system and stage prompts are available
        """
        return (
            self._system_manager.is_available(agent_type) and
            self._stage_manager.is_available(stage_id, agent_type)
        )