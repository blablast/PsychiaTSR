"""Service for migrating between legacy and new prompt formats."""

from pathlib import Path
from typing import Dict, Any, List
import json
import shutil
from datetime import datetime

from .json_prompt_repository import JsonPromptRepository


class PromptMigrationService:
    """
    Service for migrating prompt data between formats.

    Handles backward compatibility and data migration.
    """

    def __init__(self, config_dir: str = "config"):
        """
        Initialize migration service.

        Args:
            config_dir: Configuration directory path
        """
        self.config_dir = Path(config_dir)
        self.repository = JsonPromptRepository(config_dir)

    def backup_existing_prompts(self) -> str:
        """
        Create backup of existing prompt files.

        Returns:
            Path to backup directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.config_dir / f"backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)

        # Backup system prompts
        system_prompts = self.config_dir / "system_prompts.json"
        if system_prompts.exists():
            shutil.copy2(system_prompts, backup_dir / "system_prompts.json")

        # Backup stage prompts
        stage_prompts = self.config_dir / "stage_prompts.json"
        if stage_prompts.exists():
            shutil.copy2(stage_prompts, backup_dir / "stage_prompts.json")

        return str(backup_dir)

    def validate_migration_compatibility(self) -> Dict[str, Any]:
        """
        Validate that existing prompts can be migrated.

        Returns:
            Validation report with issues and statistics
        """
        report = {
            "compatible": True,
            "issues": [],
            "warnings": [],
            "statistics": {"system_prompts": 0, "stage_prompts": 0, "total_sections": 0},
        }

        # Validate system prompts
        system_prompts_file = self.config_dir / "system_prompts.json"
        if system_prompts_file.exists():
            try:
                with open(system_prompts_file, "r", encoding="utf-8") as f:
                    system_data = json.load(f)

                prompts_count = len(system_data.get("prompts", {}))
                report["statistics"]["system_prompts"] = prompts_count

                # Validate each prompt
                for prompt_id, prompt_data in system_data.get("prompts", {}).items():
                    issues = self._validate_prompt_structure(prompt_id, prompt_data, "system")
                    report["issues"].extend(issues)

                    # Count sections
                    sections = prompt_data.get("configuration", {}).get("sections", {})
                    report["statistics"]["total_sections"] += len(sections)

            except Exception as e:
                report["issues"].append(f"Failed to validate system_prompts.json: {e}")
                report["compatible"] = False

        # Validate stage prompts
        stage_prompts_file = self.config_dir / "stage_prompts.json"
        if stage_prompts_file.exists():
            try:
                with open(stage_prompts_file, "r", encoding="utf-8") as f:
                    stage_data = json.load(f)

                prompts_count = len(stage_data.get("prompts", {}))
                report["statistics"]["stage_prompts"] = prompts_count

                # Validate each prompt
                for prompt_id, prompt_data in stage_data.get("prompts", {}).items():
                    issues = self._validate_prompt_structure(prompt_id, prompt_data, "stage")
                    report["issues"].extend(issues)

                    # Count sections
                    sections = prompt_data.get("configuration", {}).get("sections", {})
                    report["statistics"]["total_sections"] += len(sections)

            except Exception as e:
                report["issues"].append(f"Failed to validate stage_prompts.json: {e}")
                report["compatible"] = False

        # Set compatibility based on critical issues
        if report["issues"]:
            report["compatible"] = False

        return report

    def test_round_trip_migration(self, prompt_id: str) -> Dict[str, Any]:
        """
        Test round-trip migration for a specific prompt.

        Args:
            prompt_id: ID of prompt to test

        Returns:
            Test results with comparison data
        """
        try:
            # Load original
            original_template = self.repository.get_template(prompt_id)

            # Convert to legacy and back
            legacy_format = self.repository._convert_template_to_legacy(original_template)
            reconstructed_template = self.repository._convert_legacy_to_template(
                prompt_id, legacy_format, original_template.prompt_type
            )

            # Compare
            comparison = {
                "success": True,
                "issues": [],
                "original_sections": len(original_template.sections),
                "reconstructed_sections": len(reconstructed_template.sections),
                "section_comparison": [],
            }

            # Compare sections
            for i, (orig, recon) in enumerate(
                zip(
                    original_template.get_sections_ordered(),
                    reconstructed_template.get_sections_ordered(),
                )
            ):
                section_comp = {
                    "index": i,
                    "title_match": orig.title == recon.title,
                    "content_match": orig.content == recon.content,
                    "order_match": orig.order == recon.order,
                }

                if not all(section_comp.values()):
                    comparison["issues"].append(f"Section {i} differs after round-trip")
                    comparison["success"] = False

                comparison["section_comparison"].append(section_comp)

            return comparison

        except Exception as e:
            return {"success": False, "error": str(e), "issues": [f"Round-trip test failed: {e}"]}

    def upgrade_prompt_format(self, prompt_id: str, create_backup: bool = True) -> Dict[str, Any]:
        """
        Upgrade specific prompt to new format with sections support.

        Args:
            prompt_id: ID of prompt to upgrade
            create_backup: Whether to create backup before upgrade

        Returns:
            Upgrade result report
        """
        result = {"success": False, "message": "", "backup_path": None, "sections_created": 0}

        try:
            if create_backup:
                result["backup_path"] = self.backup_existing_prompts()

            # Load and convert template
            template = self.repository.get_template(prompt_id)

            # Save back (this will update to latest format)
            self.repository.save_template(template)

            result["success"] = True
            result["message"] = f"Prompt {prompt_id} upgraded successfully"
            result["sections_created"] = len(template.sections)

        except Exception as e:
            result["message"] = f"Failed to upgrade prompt {prompt_id}: {e}"

        return result

    def _validate_prompt_structure(
        self, prompt_id: str, prompt_data: Dict[str, Any], prompt_type: str
    ) -> List[str]:
        """Validate individual prompt structure."""
        issues = []

        # Check required fields
        if "metadata" not in prompt_data:
            issues.append(f"{prompt_id}: Missing metadata section")

        if "configuration" not in prompt_data:
            issues.append(f"{prompt_id}: Missing configuration section")

        # Check sections structure
        config = prompt_data.get("configuration", {})
        sections = config.get("sections", {})

        if not sections:
            issues.append(f"{prompt_id}: No sections found")

        # Validate each section
        for section_key, section_data in sections.items():
            if not isinstance(section_data, dict):
                issues.append(f"{prompt_id}.{section_key}: Section data is not a dictionary")
                continue

            if "title" not in section_data:
                issues.append(f"{prompt_id}.{section_key}: Missing title")

            if "content" not in section_data:
                issues.append(f"{prompt_id}.{section_key}: Missing content")

            # Check for empty content
            if not section_data.get("content", "").strip():
                issues.append(f"{prompt_id}.{section_key}: Empty content")

        return issues
