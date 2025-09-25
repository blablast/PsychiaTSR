"""
System prompt management for AI agents.
Handles loading and formatting of system-level prompts for AI agents.
"""

import json
from pathlib import Path
from typing import Dict, Optional


class SystemPromptManager:
    """
    Manages system-level prompts for therapy agents.

    Loads and formats base system prompts that define
    the core role and principles for therapist and supervisor agents.
    """

    def __init__(self, system_prompts_dir: str):
        """
        Initialize with system prompts directory.

        Args:
            system_prompts_dir: Path to directory containing system prompt files
        """
        self._system_dir = Path(system_prompts_dir)
        self._prompt_management_service = None

    def get_prompt(self, agent_type: str) -> Optional[str]:
        """
        Get formatted system prompt for specified agent type.

        Args:
            agent_type: "therapist" or "supervisor"

        Returns:
            Formatted system prompt string or None if not found
        """
        try:
            # Lazy import to avoid circular dependency
            if self._prompt_management_service is None:
                from .prompt_management_service import PromptManagementService
                config_dir = self._system_dir
                self._prompt_management_service = PromptManagementService(str(config_dir))

            # Use new PromptManagementService to get system prompt
            prompt_data = self._prompt_management_service.get_active_system_prompt(agent_type)

            if not prompt_data:
                return None

            # Generate prompt text from new structured format
            return self._prompt_management_service.generate_prompt_text(prompt_data, "system")

        except Exception:
            return None

    @staticmethod
    def _format_system_prompt(data: Dict) -> str:
        """
        Format system prompt data into a coherent prompt string.

        Args:
            data: System prompt data from JSON file

        Returns:
            Formatted prompt string
        """
        sections = []

        # Role
        if "role" in data:
            sections.append(data["role"])

        # Core principles
        if "core_principles" in data:
            sections.append(f"PODSTAWOWE ZASADY:\n{data['core_principles']}")

        # General guidelines
        if "general_guidelines" in data:
            guidelines = "\n".join(f"- {guideline}" for guideline in data["general_guidelines"])
            sections.append(f"OGÓLNE WYTYCZNE:\n{guidelines}")

        # Common phrases (for therapist)
        if "common_phrases" in data:
            phrases = "\n".join(f"- \"{phrase}\"" for phrase in data["common_phrases"])
            sections.append(f"PRZYDATNE FRAZY:\n{phrases}")

        # Response format (for supervisor)
        if "response_format" in data:
            sections.append(f"FORMAT ODPOWIEDZI:\n{json.dumps(data['response_format'], ensure_ascii=False, indent=2)}")

        return "\n\n".join(sections)

    def is_available(self, agent_type: str) -> bool:
        """
        Check if system prompt is available for agent type.

        Args:
            agent_type: "therapist" or "supervisor"

        Returns:
            True if system prompt file exists and is readable
        """
        try:
            prompt_file = self._system_dir / f"{agent_type}_base.json"
            return prompt_file.exists() and prompt_file.is_file()
        except Exception:
            return False