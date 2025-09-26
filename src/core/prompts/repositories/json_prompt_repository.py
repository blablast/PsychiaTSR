"""JSON-based repository implementation for prompt persistence."""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..domain.prompt_template import PromptTemplate
from ..domain.prompt_section import PromptSection


class JsonPromptRepository:
    """
    Repository implementation using JSON files for persistence.

    Compatible with existing JSON format while supporting new domain models.
    """

    def __init__(self, config_dir: str = "config"):
        """
        Initialize repository with configuration directory.

        Args:
            config_dir: Directory containing JSON configuration files
        """
        self.config_dir = Path(config_dir)
        self.system_prompts_file = self.config_dir / "system_prompts.json"
        self.stage_prompts_file = self.config_dir / "stage_prompts.json"

    def get_template(self, prompt_id: str) -> PromptTemplate:
        """
        Get prompt template by ID.

        Args:
            prompt_id: Template identifier

        Returns:
            PromptTemplate instance

        Raises:
            ValueError: If template not found
        """
        # Try system prompts first
        if self.system_prompts_file.exists():
            system_data = self._load_json(self.system_prompts_file)
            if prompt_id in system_data.get("prompts", {}):
                return self._convert_legacy_to_template(
                    prompt_id, system_data["prompts"][prompt_id], "system"
                )

        # Try stage prompts
        if self.stage_prompts_file.exists():
            stage_data = self._load_json(self.stage_prompts_file)
            if prompt_id in stage_data.get("prompts", {}):
                return self._convert_legacy_to_template(
                    prompt_id, stage_data["prompts"][prompt_id], "stage"
                )

        raise ValueError(f"Template {prompt_id} not found")

    def save_template(self, template: PromptTemplate) -> None:
        """
        Save prompt template to appropriate JSON file.

        Args:
            template: Template to save
        """
        # Determine target file based on prompt type
        if template.prompt_type == "system":
            target_file = self.system_prompts_file
        elif template.prompt_type == "stage":
            target_file = self.stage_prompts_file
        else:
            raise ValueError(f"Unknown prompt type: {template.prompt_type}")

        # Load existing data
        if target_file.exists():
            data = self._load_json(target_file)
        else:
            data = {
                "metadata": {
                    "version": "2.0",  # New version with sections support
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "description": f"{template.prompt_type.title()} prompts database with sections support",
                },
                "prompts": {},
            }

        # Convert template to legacy format
        legacy_format = self._convert_template_to_legacy(template)
        data["prompts"][template.id] = legacy_format

        # Update metadata
        data["metadata"]["updated_at"] = datetime.now().isoformat()

        # Save back to file
        self._save_json(target_file, data)

    def search_templates(
        self, agent_type: str = None, prompt_type: str = None, stage_id: str = None
    ) -> List[PromptTemplate]:
        """
        Search templates by criteria.

        Args:
            agent_type: Agent type filter
            prompt_type: Prompt type filter
            stage_id: Stage ID filter

        Returns:
            List of matching templates
        """
        templates = []

        # Search system prompts
        if prompt_type is None or prompt_type == "system":
            templates.extend(
                self._search_in_file(self.system_prompts_file, agent_type, "system", stage_id)
            )

        # Search stage prompts
        if prompt_type is None or prompt_type == "stage":
            templates.extend(
                self._search_in_file(self.stage_prompts_file, agent_type, "stage", stage_id)
            )

        return templates

    def list_prompt_ids(self, prompt_type: str = None) -> List[str]:
        """
        List all prompt IDs.

        Args:
            prompt_type: Filter by prompt type

        Returns:
            List of prompt IDs
        """
        prompt_ids = []

        if prompt_type is None or prompt_type == "system":
            if self.system_prompts_file.exists():
                system_data = self._load_json(self.system_prompts_file)
                prompt_ids.extend(system_data.get("prompts", {}).keys())

        if prompt_type is None or prompt_type == "stage":
            if self.stage_prompts_file.exists():
                stage_data = self._load_json(self.stage_prompts_file)
                prompt_ids.extend(stage_data.get("prompts", {}).keys())

        return prompt_ids

    def delete_template(self, prompt_id: str) -> bool:
        """
        Delete template by ID.

        Args:
            prompt_id: Template to delete

        Returns:
            True if deleted, False if not found
        """
        # Try system prompts
        if self._delete_from_file(self.system_prompts_file, prompt_id):
            return True

        # Try stage prompts
        if self._delete_from_file(self.stage_prompts_file, prompt_id):
            return True

        return False

    def _search_in_file(
        self, file_path: Path, agent_type: str, prompt_type: str, stage_id: str
    ) -> List[PromptTemplate]:
        """Search templates in specific file."""
        if not file_path.exists():
            return []

        data = self._load_json(file_path)
        templates = []

        for prompt_id, prompt_data in data.get("prompts", {}).items():
            # Apply filters
            metadata = prompt_data.get("metadata", {})

            if agent_type and metadata.get("agent") != agent_type:
                continue

            if stage_id and metadata.get("stage_id") != stage_id:
                continue

            # Convert to template
            try:
                template = self._convert_legacy_to_template(prompt_id, prompt_data, prompt_type)
                templates.append(template)
            except Exception:
                continue  # Skip invalid entries

        return templates

    def _delete_from_file(self, file_path: Path, prompt_id: str) -> bool:
        """Delete prompt from specific file."""
        if not file_path.exists():
            return False

        data = self._load_json(file_path)

        if prompt_id in data.get("prompts", {}):
            del data["prompts"][prompt_id]
            data["metadata"]["updated_at"] = datetime.now().isoformat()
            self._save_json(file_path, data)
            return True

        return False

    def _convert_legacy_to_template(
        self, prompt_id: str, legacy_data: Dict[str, Any], prompt_type: str
    ) -> PromptTemplate:
        """Convert legacy JSON format to PromptTemplate."""
        metadata = legacy_data.get("metadata", {})
        configuration = legacy_data.get("configuration", {})
        sections_data = configuration.get("sections", {})

        # Create sections from legacy format
        sections = []
        for i, (section_key, section_data) in enumerate(sections_data.items()):
            # PRESERVE EXACT TITLE from JSON - never modify it
            original_title = section_data.get("title", section_key)

            section = PromptSection(
                id=f"{prompt_id}_section_{i}",
                title=original_title,  # EXACT title preservation
                content=section_data.get("content", ""),
                order=i,
                section_type="standard",
                metadata={"legacy_key": section_key},
                created_at=self._parse_datetime(metadata.get("created_at")),
                updated_at=self._parse_datetime(metadata.get("updated_at")),
            )
            sections.append(section)

        # Create template
        template = PromptTemplate(
            id=prompt_id,
            agent_type=metadata.get("agent", "unknown"),
            prompt_type=prompt_type,
            stage_id=metadata.get("stage_id"),
            sections=sections,
            metadata={
                "note": metadata.get("note"),
                "status": metadata.get("status"),
                "legacy_id": metadata.get("id"),
            },
            created_at=self._parse_datetime(metadata.get("created_at")),
            updated_at=self._parse_datetime(metadata.get("updated_at")),
        )

        return template

    def _convert_template_to_legacy(self, template: PromptTemplate) -> Dict[str, Any]:
        """Convert PromptTemplate to legacy JSON format."""
        sections_dict = {}

        for section in template.get_sections_ordered():
            # Use legacy key from metadata if available, otherwise generate
            legacy_key = section.metadata.get("legacy_key") if section.metadata else None
            if not legacy_key:
                # Generate legacy key from title BUT preserve original title exactly
                clean_title = section.title.lower().replace(" ", "_").replace("-", "_")
                # Remove any numbering from key generation to avoid conflicts
                clean_title = clean_title.replace(".", "").replace(":", "")
                legacy_key = clean_title

                # Ensure uniqueness by adding suffix, NOT by changing the title
                counter = 1
                original_key = legacy_key
                while legacy_key in sections_dict:
                    legacy_key = f"{original_key}_{counter}"
                    counter += 1

            sections_dict[legacy_key] = {
                "title": section.title,  # PRESERVE EXACT TITLE - no modifications
                "content": section.content,
            }

        return {
            "metadata": {
                "id": template.metadata.get("legacy_id") or 1,
                "agent": template.agent_type,
                "stage_id": template.stage_id,
                "created_at": template.created_at.isoformat() if template.created_at else None,
                "updated_at": template.updated_at.isoformat() if template.updated_at else None,
                "status": template.metadata.get("status", "active"),
                "note": template.metadata.get("note", ""),
            },
            "configuration": {"sections": sections_dict},
        }

    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON file safely."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load {file_path}: {e}")

    def _save_json(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Save JSON file safely."""
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ValueError(f"Failed to save {file_path}: {e}")

    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Parse datetime string safely."""
        if not datetime_str:
            return None
        try:
            return datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        except Exception:
            return None
