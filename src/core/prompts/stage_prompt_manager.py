"""
Stage prompt management for therapy phases.
Handles loading and formatting of stage-specific prompts for therapy phases.
"""

import json
from pathlib import Path
from typing import Dict, Optional, List


class StagePromptManager:
    """
    Manages stage-specific prompts for therapy workflow.

    Loads and formats stage-specific prompts that define
    goals, guidelines, and examples for each therapy stage.
    """

    def __init__(self, stages_prompts_dir: str):
        """
        Initialize with stages prompts directory.

        Args:
            stages_prompts_dir: Path to directory containing stage prompt files
        """
        self._stages_dir = Path(stages_prompts_dir)
        self._prompt_management_service = None

    def get_prompt(self, stage_id: str, agent_type: str) -> Optional[str]:
        """
        Get formatted stage prompt for specified stage and agent type.

        Args:
            stage_id: Stage identifier (e.g., "opening", "resources")
            agent_type: "therapist" or "supervisor"

        Returns:
            Formatted stage prompt string or None if not found
        """
        try:

            # Lazy import to avoid circular dependency
            if self._prompt_management_service is None:
                from .prompt_management_service import PromptManagementService
                config_dir = self._stages_dir
                self._prompt_management_service = PromptManagementService(str(config_dir))

            # Use new PromptManagementService to get stage prompt
            prompt_data = self._prompt_management_service.get_active_stage_prompt(stage_id, agent_type)

            if not prompt_data:
                return None

            # Generate prompt text from new structured format
            result = self._prompt_management_service.generate_prompt_text(prompt_data, "stage")
            return result

        except Exception as e:
            return None

    @staticmethod
    def _format_therapist_stage_prompt(data: Dict) -> str:
        """
        Format therapist stage prompt data into a coherent prompt string.

        Args:
            data: Stage prompt data from JSON file

        Returns:
            Formatted prompt string for therapist
        """
        # New TSR format: use direct prompt field if available
        if "prompt" in data:
            return data["prompt"]

        # Component-based format: build from components
        sections = []

        # Stage goals
        if "stage_goals" in data:
            goals = "\n".join(f"- {goal}" for goal in data["stage_goals"])
            sections.append(f"CELE TEGO ETAPU:\n{goals}")

        # Stage-specific guidelines
        if "stage_specific_guidelines" in data:
            guidelines = "\n".join(f"- {guideline}" for guideline in data["stage_specific_guidelines"])
            sections.append(f"ZASADY ETAPU:\n{guidelines}")

        # Suggested questions
        if "suggested_questions" in data:
            questions = "\n".join(f"- \"{question}\"" for question in data["suggested_questions"])
            sections.append(f"PRZYKŁADOWE PYTANIA:\n{questions}")

        # Key phrases
        if "key_phrases" in data:
            phrases = "\n".join(f"- \"{phrase}\"" for phrase in data["key_phrases"])
            sections.append(f"KLUCZOWE FRAZY:\n{phrases}")

        # Response templates
        if "response_templates" in data:
            templates = "\n".join(f"- \"{template}\"" for template in data["response_templates"])
            sections.append(f"SZABLONY ODPOWIEDZI:\n{templates}")

        # Good examples
        if "good_examples" in data:
            examples = "\n".join(f"- \"{example}\"" for example in data["good_examples"])
            sections.append(f"DOBRE PRZYKŁADY:\n{examples}")

        # What to avoid
        if "avoid_examples" in data:
            avoid = "\n".join(f"- {example}" for example in data["avoid_examples"])
            sections.append(f"UNIKAJ:\n{avoid}")

        return "\n\n".join(sections)

    @staticmethod
    def _format_supervisor_stage_prompt(data: Dict) -> str:
        """
        Format supervisor stage prompt data into a coherent prompt string.

        Args:
            data: Stage prompt data from JSON file

        Returns:
            Formatted prompt string for supervisor
        """
        # New TSR format: use direct prompt field if available
        if "prompt" in data:
            return data["prompt"]

        # Component-based format: build from components
        sections = []

        # Stage info
        if "stage_name" in data and "stage_description" in data:
            sections.append(f"ETAP: {data['stage_name']}")
            sections.append(f"OPIS: {data['stage_description']}")

        # Criteria
        if "criteria" in data:
            criteria_text = "KRYTERIA DO SPEŁNIENIA:\n"
            for criterion_id, criterion_data in data["criteria"].items():
                criteria_text += f"\n{criterion_id.upper()}:\n"
                criteria_text += f"- {criterion_data.get('description', '')}\n"

                if "requirements" in criterion_data:
                    for req in criterion_data["requirements"]:
                        criteria_text += f"  • {req}\n"

                if "positive_examples" in criterion_data:
                    criteria_text += "  ✅ Przykłady pozytywne:\n"
                    for example in criterion_data["positive_examples"]:
                        criteria_text += f"    - {example}\n"

                if "negative_examples" in criterion_data:
                    criteria_text += "  ❌ Przykłady negatywne:\n"
                    for example in criterion_data["negative_examples"]:
                        criteria_text += f"    - {example}\n"

            sections.append(criteria_text.rstrip())

        # Evaluation rules
        if "evaluation_rules" in data:
            rules = "\n".join(f"- {rule}" for rule in data["evaluation_rules"])
            sections.append(f"ZASADY OCENY:\n{rules}")

        return "\n\n".join(sections)

    def is_available(self, stage_id: str, agent_type: str) -> bool:
        """
        Check if stage prompt is available for given stage and agent type.

        Args:
            stage_id: Stage identifier
            agent_type: "therapist" or "supervisor"

        Returns:
            True if stage prompt file exists and is readable
        """
        try:
            prompt_file = self._stages_dir / agent_type / f"{stage_id}.json"
            return prompt_file.exists() and prompt_file.is_file()
        except Exception:
            return False

    def get_available_stages(self, agent_type: str) -> List[str]:
        """
        Get list of available stages for given agent type.

        Args:
            agent_type: "therapist" or "supervisor"

        Returns:
            List of stage IDs that have prompt files
        """
        try:
            agent_dir = self._stages_dir / agent_type
            if not agent_dir.exists():
                return []

            return [
                file.stem for file in agent_dir.glob("*.json")
                if file.is_file()
            ]
        except Exception:
            return []