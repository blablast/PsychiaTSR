"""Prompt validation service - handles validation logic."""

from typing import Dict, Any, List, Tuple


class PromptValidator:
    """Handles validation of prompt data structures."""

    @staticmethod
    def validate_prompt_structure(prompt_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate prompt data structure and return validation results.

        Args:
            prompt_data: Prompt data to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required top-level structure
        if not isinstance(prompt_data, dict):
            errors.append("Prompt data must be a dictionary")
            return False, errors

        if "metadata" not in prompt_data:
            errors.append("Missing 'metadata' section")

        if "configuration" not in prompt_data:
            errors.append("Missing 'configuration' section")

        # Check metadata structure
        metadata = prompt_data.get("metadata", {})
        if not isinstance(metadata, dict):
            errors.append("Metadata must be a dictionary")
        else:
            required_metadata = ["id", "status"]
            for field in required_metadata:
                if field not in metadata:
                    errors.append(f"Missing metadata field: {field}")

            # Check ID is numeric
            prompt_id = metadata.get("id")
            if prompt_id is not None and not isinstance(prompt_id, int):
                errors.append("ID must be a numeric integer")

            # Check status is valid
            status = metadata.get("status")
            if status is not None and status not in ["active", "inactive", "draft"]:
                errors.append("Status must be 'active', 'inactive', or 'draft'")

        # Check configuration structure
        config = prompt_data.get("configuration", {})
        if not isinstance(config, dict):
            errors.append("Configuration must be a dictionary")
        else:
            if "sections" not in config:
                errors.append("Missing 'sections' in configuration")

            sections = config.get("sections", {})
            if not isinstance(sections, dict):
                errors.append("Sections must be a dictionary")
            elif not sections:
                errors.append("At least one section is required")
            else:
                # Check section structure
                for section_name, section_data in sections.items():
                    if not isinstance(section_data, dict):
                        errors.append(f"Section '{section_name}' must be a dictionary")
                        continue

                    if "title" not in section_data:
                        errors.append(f"Section '{section_name}' missing title")
                    elif not isinstance(section_data["title"], str):
                        errors.append(f"Section '{section_name}' title must be a string")

                    if "content" not in section_data:
                        errors.append(f"Section '{section_name}' missing content")
                    elif not isinstance(section_data["content"], str):
                        errors.append(f"Section '{section_name}' content must be a string")

        return len(errors) == 0, errors

    @staticmethod
    def validate_system_prompt(
        prompt_data: Dict[str, Any], agent_type: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate system prompt data with agent-specific checks.

        Args:
            prompt_data: Prompt data to validate
            agent_type: Type of agent (therapist, supervisor)

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        # First do basic structure validation
        is_valid, errors = PromptValidator.validate_prompt_structure(prompt_data)

        if not is_valid:
            return False, errors

        # Check agent type in metadata matches expected
        metadata = prompt_data.get("metadata", {})
        metadata_agent = metadata.get("agent")
        if metadata_agent and metadata_agent != agent_type:
            errors.append(
                f"Metadata agent '{metadata_agent}' doesn't match expected '{agent_type}'"
            )

        # Check for required sections in system prompts
        sections = prompt_data.get("configuration", {}).get("sections", {})
        recommended_sections = {
            "therapist": ["ai_role", "therapy_approach", "communication_style"],
            "supervisor": ["ai_role", "evaluation_criteria", "decision_process"],
        }

        if agent_type in recommended_sections:
            missing_sections = []
            for recommended in recommended_sections[agent_type]:
                if recommended not in sections:
                    missing_sections.append(recommended)

            if missing_sections:
                errors.append(
                    f"Missing recommended sections for {agent_type}: {', '.join(missing_sections)}"
                )

        return len(errors) == 0, errors

    @staticmethod
    def validate_stage_prompt(
        prompt_data: Dict[str, Any], stage_id: str, agent_type: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate stage prompt data with stage-specific checks.

        Args:
            prompt_data: Prompt data to validate
            stage_id: Stage identifier
            agent_type: Type of agent (therapist, supervisor)

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        # First do basic structure validation
        is_valid, errors = PromptValidator.validate_prompt_structure(prompt_data)

        if not is_valid:
            return False, errors

        # Check agent type and stage in metadata
        metadata = prompt_data.get("metadata", {})

        metadata_agent = metadata.get("agent")
        if metadata_agent and metadata_agent != agent_type:
            errors.append(
                f"Metadata agent '{metadata_agent}' doesn't match expected '{agent_type}'"
            )

        # Stage validation - convert stage_id to numeric for comparison
        stage_mapping = {
            "opening": 1,
            "resources": 2,
            "scaling": 3,
            "small_steps": 4,
            "summary": 5,
            "rest": 6,
            "safety_monitoring": 6,
        }

        expected_stage = stage_mapping.get(stage_id)
        if expected_stage is None and stage_id.isdigit():
            expected_stage = int(stage_id)

        metadata_stage = metadata.get("stage")
        if (
            metadata_stage is not None
            and expected_stage is not None
            and metadata_stage != expected_stage
        ):
            errors.append(
                f"Metadata stage '{metadata_stage}' doesn't match expected '{expected_stage}' for stage '{stage_id}'"
            )

        # Check for stage-specific content requirements
        sections = prompt_data.get("configuration", {}).get("sections", {})

        # Different stages might have different content requirements
        stage_requirements = {
            "opening": ["objectives", "approach"],
            "summary": ["summary_format", "next_steps"],
            # Add more as needed
        }

        if stage_id in stage_requirements:
            missing_sections = []
            for required in stage_requirements[stage_id]:
                if required not in sections:
                    missing_sections.append(required)

            if missing_sections:
                errors.append(
                    f"Missing sections for stage '{stage_id}': {', '.join(missing_sections)}"
                )

        return len(errors) == 0, errors

    @staticmethod
    def validate_agent_type(agent_type: str) -> Tuple[bool, str]:
        """
        Validate agent type.

        Args:
            agent_type: Agent type to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_agents = ["therapist", "supervisor"]

        if not isinstance(agent_type, str):
            return False, "Agent type must be a string"

        if not agent_type:
            return False, "Agent type cannot be empty"

        if agent_type not in valid_agents:
            return False, f"Agent type must be one of: {', '.join(valid_agents)}"

        return True, ""

    @staticmethod
    def validate_stage_id(stage_id: str) -> Tuple[bool, str]:
        """
        Validate stage ID.

        Args:
            stage_id: Stage ID to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_stages = [
            "opening",
            "resources",
            "scaling",
            "small_steps",
            "summary",
            "rest",
            "safety_monitoring",
        ]

        if not isinstance(stage_id, str):
            return False, "Stage ID must be a string"

        if not stage_id:
            return False, "Stage ID cannot be empty"

        # Allow numeric stages 1-6
        if stage_id.isdigit():
            numeric_stage = int(stage_id)
            if 1 <= numeric_stage <= 6:
                return True, ""
            else:
                return False, "Numeric stage ID must be between 1 and 6"

        if stage_id not in valid_stages:
            return False, f"Stage ID must be one of: {', '.join(valid_stages)} or numeric (1-6)"

        return True, ""
