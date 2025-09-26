"""Prompt repository - handles data access for system and stage prompts."""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..config.loaders.base_database_loader import BaseDatabaseLoader


class SystemPromptRepository:
    """Handles data access for system prompts."""

    def __init__(self, config_dir: str = "config", logger=None):
        self.config_dir = Path(config_dir)
        self.logger = logger
        self._db_loader = BaseDatabaseLoader(
            database_file=self.config_dir / "system_prompts.json",
            database_type="system prompts",
            logger=logger,
        )

    def get_active_prompt(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """Get active system prompt for agent type."""
        active_prompts = self._db_loader.find_records_by_metadata(
            {"agent": agent_type, "status": "active"}
        )

        if active_prompts:
            # Return first active prompt found
            return next(iter(active_prompts.values()))

        return None

    def save_prompt(self, agent_type: str, prompt_data: Dict[str, Any]) -> bool:
        """Save system prompt, archiving existing active prompts."""
        try:
            # Archive existing active prompts for this agent
            self._db_loader.archive_active_records({"agent": agent_type})

            # Get next unique ID
            next_id = self._db_loader.find_next_global_id()

            # Create new prompt record
            prompt_record = {
                "metadata": {
                    "id": next_id,
                    "agent": agent_type,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "status": "active",
                    "note": prompt_data.get("metadata", {}).get(
                        "note", f"{agent_type.title()} system prompt"
                    ),
                },
                "configuration": prompt_data.get("configuration", {"sections": {}}),
            }

            # Save to database
            record_key = f"{agent_type}_system_{next_id}"
            success = self._db_loader.save_record(record_key, prompt_record)

            if success and self.logger:
                self.logger.info(f"Saved system prompt: {agent_type} ID={next_id}")

            return success

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving system prompt for {agent_type}: {e}")
            return False

    def get_prompt_by_key(self, prompt_key: str) -> Optional[Dict[str, Any]]:
        """Get system prompt by database key."""
        return self._db_loader.get_record(prompt_key)

    def list_all_prompts(self) -> List[Dict[str, Any]]:
        """List all system prompts."""
        records = self._db_loader.list_all_records()
        results = []

        for prompt_key, prompt_record in records.items():
            record_with_key = prompt_record.copy()
            record_with_key["metadata"]["database_key"] = prompt_key
            results.append(record_with_key)

        # Sort by agent name
        results.sort(key=lambda x: x.get("metadata", {}).get("agent", ""))
        return results

    def list_versions(self, agent_type: str) -> List[Dict[str, Any]]:
        """List all versions for agent type."""
        all_prompts = self._db_loader.find_records_by_metadata({"agent": agent_type})
        results = []

        for prompt_key, prompt_record in all_prompts.items():
            metadata = prompt_record.get("metadata", {})
            results.append(
                {
                    "database_key": prompt_key,
                    "id": metadata.get("id"),
                    "status": metadata.get("status"),
                    "created_at": metadata.get("created_at"),
                    "updated_at": metadata.get("updated_at"),
                }
            )

        # Sort by ID (newest first)
        results.sort(key=lambda x: x.get("id", 0), reverse=True)
        return results


class StagePromptRepository:
    """Handles data access for stage prompts."""

    def __init__(self, config_dir: str = "config", logger=None):
        self.config_dir = Path(config_dir)
        self.logger = logger
        self._db_loader = BaseDatabaseLoader(
            database_file=self.config_dir / "stage_prompts.json",
            database_type="stage prompts",
            logger=logger,
        )

        # No stage mapping needed - we use stage_id strings directly

    def get_active_prompt(self, stage_id: str, agent_type: str) -> Optional[Dict[str, Any]]:
        """Get active stage prompt for stage and agent."""

        # Now we search directly by stage_id string (no conversion needed)
        search_criteria = {"agent": agent_type, "stage_id": stage_id, "status": "active"}

        active_prompts = self._db_loader.find_records_by_metadata(search_criteria)

        if active_prompts:
            result = next(iter(active_prompts.values()))
            return result

        return None

    def save_prompt(self, stage_id: str, agent_type: str, prompt_data: Dict[str, Any]) -> bool:
        """Save stage prompt, archiving existing active prompts."""
        try:
            # Archive existing active prompts for this agent and stage_id
            self._db_loader.archive_active_records({"agent": agent_type, "stage_id": stage_id})

            # Get next unique ID
            next_id = self._db_loader.find_next_global_id()

            # Create new prompt record
            prompt_record = {
                "metadata": {
                    "id": next_id,
                    "agent": agent_type,
                    "stage_id": stage_id,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "status": "active",
                    "note": prompt_data.get("metadata", {}).get(
                        "note", f"{agent_type.title()} stage {stage_id}"
                    ),
                },
                "configuration": prompt_data.get("configuration", {"sections": {}}),
            }

            # Save to database
            record_key = f"{agent_type}_stage_{stage_id}_{next_id}"
            success = self._db_loader.save_record(record_key, prompt_record)

            if success and self.logger:
                self.logger.info(f"Saved stage prompt: {stage_id}/{agent_type} ID={next_id}")

            return success

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving stage prompt for {stage_id}/{agent_type}: {e}")
            return False

    def get_prompt_by_key(self, prompt_key: str) -> Optional[Dict[str, Any]]:
        """Get stage prompt by database key."""
        return self._db_loader.get_record(prompt_key)

    def get_all_for_agent(self, agent_type: str) -> List[Dict[str, Any]]:
        """Get all stage prompts for specific agent."""
        agent_prompts = self._db_loader.find_records_by_metadata({"agent": agent_type})
        results = list(agent_prompts.values())

        # Sort by stage_id
        results.sort(key=lambda x: x.get("metadata", {}).get("stage_id", ""))
        return results

    def get_all_for_stage(self, stage_id: str) -> List[Dict[str, Any]]:
        """Get all stage prompts for specific stage."""
        stage_prompts = self._db_loader.find_records_by_metadata({"stage_id": stage_id})
        results = list(stage_prompts.values())

        # Sort by agent name
        results.sort(key=lambda x: x.get("metadata", {}).get("agent", ""))
        return results

    def list_all_prompts(self) -> List[Dict[str, Any]]:
        """List all stage prompts."""
        records = self._db_loader.list_all_records()
        results = []

        for prompt_key, prompt_record in records.items():
            record_with_key = prompt_record.copy()
            record_with_key["metadata"]["database_key"] = prompt_key
            results.append(record_with_key)

        # Sort by agent, then by stage_id
        results.sort(
            key=lambda x: (
                x.get("metadata", {}).get("agent", ""),
                x.get("metadata", {}).get("stage_id", ""),
            )
        )

        return results

    # _convert_stage_to_numeric method removed - no longer needed with stage_id strings
