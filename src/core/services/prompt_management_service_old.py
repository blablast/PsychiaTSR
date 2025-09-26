"""
PromptManagementService - Core business service for managing prompts.

This service encapsulates all prompt management logic including CRUD operations,
versioning, template loading, and active prompt resolution. It treats JSON files
as a database and provides a clean business interface for prompt operations.

Key responsibilities:
- Load and save prompt configurations with proper versioning
- Manage active prompt resolution and status
- Handle template loading and default prompt creation
- Provide search and filtering capabilities
- Ensure data consistency and validation
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..models.schemas import MessageData


class PromptManagementService:
    """
    Business service for comprehensive prompt management.

    This service acts as the single source of truth for all prompt operations,
    separating business logic from UI concerns and data access patterns.
    """

    def __init__(self, config_dir: str = "config", logger=None):
        """
        Initialize the prompt management service.

        Args:
            config_dir: Base configuration directory path
            logger: Optional logger for operations tracking
        """
        self.config_dir = Path(config_dir)
        self.logger = logger

        # New database files
        self.stage_prompts_db = self.config_dir / "stage_prompts.json"
        self.system_prompts_db = self.config_dir / "system_prompts.json"

        # Cache for database content
        self._stage_db_cache = None
        self._system_db_cache = None

    # =====================================================================================
    # SYSTEM PROMPT OPERATIONS
    # =====================================================================================

    def get_active_system_prompt(self, agent_type: str) -> Dict[str, Any]:
        """
        Get the currently active system prompt for the specified agent type.

        Args:
            agent_type: Type of agent (therapist, supervisor)

        Returns:
            Active system prompt configuration or default if none found
        """
        try:
            # Load system prompts database
            database = self._load_system_prompts_database()

            # Look for active prompt with new numeric ID system
            base_key = f"{agent_type}_system"
            for key, prompt_record in database.get("prompts", {}).items():
                if (
                    key.startswith(base_key)
                    and prompt_record.get("metadata", {}).get("agent") == agent_type
                    and prompt_record.get("metadata", {}).get("status") == "active"
                ):
                    return prompt_record

            if self.logger:
                self.logger.info(f"Active system prompt not found in database for {agent_type}")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading system prompt for {agent_type}: {e}")

        # Return fallback if nothing found
        return self._create_fallback_system_prompt(agent_type)

    def save_system_prompt(self, agent_type: str, prompt_data: Dict[str, Any]) -> bool:
        """
        Save system prompt to database with unique ID and archiving.
        When saving, existing active prompt becomes inactive (archived).

        Args:
            agent_type: Type of agent (therapist, supervisor)
            prompt_data: Prompt configuration to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Load database
            database = self._load_system_prompts_database()

            # Find globally unique ID across all prompts in the file
            next_id = self._find_next_global_id(database)

            # Generate base prompt key for the agent
            base_key = f"{agent_type}_system"

            # Find existing active prompt and archive it
            for key, record in database["prompts"].items():
                if (
                    key.startswith(base_key)
                    and record.get("metadata", {}).get("agent") == agent_type
                    and record.get("metadata", {}).get("status") == "active"
                ):
                    # Mark existing as inactive (archived)
                    record["metadata"]["status"] = "inactive"
                    record["metadata"]["archived_at"] = datetime.now().isoformat()

            # Generate new prompt key with unique ID
            new_prompt_key = f"{base_key}_{next_id}"

            # Prepare new prompt record (removed version field)
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

            # Save new prompt to database
            database["prompts"][new_prompt_key] = prompt_record

            # Save database
            success = self._save_system_prompts_database(database)

            if success and self.logger:
                self.logger.info(
                    f"Saved system prompt: {agent_type} ID={next_id}, archived previous versions"
                )

            return success

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving system prompt for {agent_type}: {e}")
            return False

    def list_system_prompt_versions(self, agent_type: str) -> List[Dict[str, Any]]:
        """
        List all available versions of system prompts for an agent type.

        Args:
            agent_type: Type of agent to search for

        Returns:
            List of prompt metadata sorted by version
        """
        try:
            # Load database
            database = self._load_system_prompts_database()

            # Generate prompt key
            prompt_key = self._generate_system_prompt_key(agent_type)

            # For now, return single version from database (in future we might store version history)
            if prompt_key in database.get("prompts", {}):
                prompt_record = database["prompts"][prompt_key]
                metadata = prompt_record.get("metadata", {})

                return [
                    {
                        "database_key": prompt_key,
                        "id": metadata.get("id"),
                        "status": metadata.get("status"),
                        "created_at": metadata.get("created_at"),
                        "updated_at": metadata.get("updated_at"),
                    }
                ]
            else:
                return []

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error listing system prompt versions for {agent_type}: {e}")
            return []

    def get_system_prompt_by_key(self, prompt_key: str) -> Optional[Dict[str, Any]]:
        """
        Get system prompt by database key.

        Args:
            prompt_key: Database key (e.g., "therapist_system")

        Returns:
            System prompt record or None if not found
        """
        try:
            database = self._load_system_prompts_database()
            return database.get("prompts", {}).get(prompt_key)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting system prompt by key {prompt_key}: {e}")
            return None

    def list_all_system_prompts(self) -> List[Dict[str, Any]]:
        """
        List all system prompts in database.

        Returns:
            List of all system prompt records with metadata
        """
        try:
            database = self._load_system_prompts_database()
            results = []

            for prompt_key, prompt_record in database.get("prompts", {}).items():
                # Add database key to metadata for reference
                record_with_key = prompt_record.copy()
                record_with_key["metadata"]["database_key"] = prompt_key
                results.append(record_with_key)

            # Sort by agent name
            results.sort(key=lambda x: x.get("metadata", {}).get("agent", ""))

            return results

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error listing all system prompts: {e}")
            return []

    # =====================================================================================
    # DATABASE OPERATIONS
    # =====================================================================================

    def _load_stage_prompts_database(self) -> Dict[str, Any]:
        """Load stage prompts database with caching and string unescaping."""
        if self._stage_db_cache is None:
            try:
                with open(self.stage_prompts_db, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    # Apply string unescaping to the loaded data
                    self._stage_db_cache = self._unescape_json_strings(raw_data)
            except FileNotFoundError:
                if self.logger:
                    self.logger.warning(
                        f"Stage prompts database not found: {self.stage_prompts_db}"
                    )
                self._stage_db_cache = self._create_empty_stage_database()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error loading stage prompts database: {e}")
                self._stage_db_cache = self._create_empty_stage_database()

        return self._stage_db_cache

    def _save_stage_prompts_database(self, database: Dict[str, Any]) -> bool:
        """Save stage prompts database and update cache."""
        try:
            # Update timestamp
            database["metadata"]["updated_at"] = datetime.now().isoformat()

            with open(self.stage_prompts_db, "w", encoding="utf-8") as f:
                json.dump(database, f, indent=2, ensure_ascii=False)

            # Update cache
            self._stage_db_cache = database

            if self.logger:
                self.logger.info(f"Stage prompts database saved successfully")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving stage prompts database: {e}")
            return False

    def _create_empty_stage_database(self) -> Dict[str, Any]:
        """Create empty stage prompts database structure."""
        return {
            "metadata": {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "description": "Stage prompts database - all therapy stages for all agents",
            },
            "prompts": {},
        }

    def _generate_stage_prompt_key(self, stage_id: str, agent_type: str) -> str:
        """Generate database key for stage prompt."""
        return f"{agent_type}_stage_{stage_id}"

    def _load_system_prompts_database(self) -> Dict[str, Any]:
        """Load system prompts database with caching and string unescaping."""
        if self._system_db_cache is None:
            try:
                with open(self.system_prompts_db, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    # Apply string unescaping to the loaded data
                    self._system_db_cache = self._unescape_json_strings(raw_data)
            except FileNotFoundError:
                if self.logger:
                    self.logger.warning(
                        f"System prompts database not found: {self.system_prompts_db}"
                    )
                self._system_db_cache = self._create_empty_system_database()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error loading system prompts database: {e}")
                self._system_db_cache = self._create_empty_system_database()

        return self._system_db_cache

    def _save_system_prompts_database(self, database: Dict[str, Any]) -> bool:
        """Save system prompts database and update cache."""
        try:
            # Update timestamp
            database["metadata"]["updated_at"] = datetime.now().isoformat()

            with open(self.system_prompts_db, "w", encoding="utf-8") as f:
                json.dump(database, f, indent=2, ensure_ascii=False)

            # Update cache
            self._system_db_cache = database

            if self.logger:
                self.logger.info(f"System prompts database saved successfully")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving system prompts database: {e}")
            return False

    def _create_empty_system_database(self) -> Dict[str, Any]:
        """Create empty system prompts database structure."""
        return {
            "metadata": {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "description": "System prompts database - all system prompts for all agents",
            },
            "prompts": {},
        }

    def _generate_system_prompt_key(self, agent_type: str) -> str:
        """Generate database key for system prompt."""
        return f"{agent_type}_system"

    # =====================================================================================
    # STAGE PROMPT OPERATIONS
    # =====================================================================================

    def get_active_stage_prompt(self, stage_id: str, agent_type: str) -> Dict[str, Any]:
        """
        Get the currently active stage prompt for the specified stage and agent.

        Args:
            stage_id: Unique identifier for the therapy stage
            agent_type: Type of agent (therapist, supervisor)

        Returns:
            Active stage prompt configuration or default if none found
        """
        try:
            # Load stage prompts database
            database = self._load_stage_prompts_database()

            # Convert stage_id to numeric stage number for JSON lookup
            numeric_stage = self._convert_stage_id_to_numeric(stage_id)
            if numeric_stage is None:
                if self.logger:
                    self.logger.warning(f"Cannot convert stage_id '{stage_id}' to numeric stage")
                return self._create_fallback_stage_prompt(stage_id, agent_type)

            # Look for active prompt with numeric stage system
            base_key = f"{agent_type}_stage_{numeric_stage}"
            for key, prompt_record in database.get("prompts", {}).items():
                if (
                    key.startswith(base_key)
                    and prompt_record.get("metadata", {}).get("agent") == agent_type
                    and prompt_record.get("metadata", {}).get("stage") == numeric_stage
                    and prompt_record.get("metadata", {}).get("status") == "active"
                ):
                    return prompt_record

            if self.logger:
                self.logger.info(
                    f"Active stage prompt not found in database for {stage_id}/{agent_type} (numeric stage: {numeric_stage})"
                )

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading stage prompt for {stage_id}/{agent_type}: {e}")

        # Return fallback if nothing found
        return self._create_fallback_stage_prompt(stage_id, agent_type)

    def save_stage_prompt(
        self, stage_id: str, agent_type: str, prompt_data: Dict[str, Any]
    ) -> bool:
        """
        Save stage prompt to database with unique ID and archiving.
        When saving, existing active prompt becomes inactive (archived).

        Args:
            stage_id: Unique identifier for the therapy stage
            agent_type: Type of agent (therapist, supervisor)
            prompt_data: Prompt configuration to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Convert stage_id to numeric stage number for JSON database
            numeric_stage = self._convert_stage_id_to_numeric(stage_id)
            if numeric_stage is None:
                if self.logger:
                    self.logger.error(f"Cannot convert stage_id '{stage_id}' to numeric stage")
                return False

            # Load database
            database = self._load_stage_prompts_database()

            # Find globally unique ID across all prompts in the file
            next_id = self._find_next_global_id(database)

            # Generate base prompt key for the agent and stage
            base_key = f"{agent_type}_stage_{numeric_stage}"

            # Find existing active prompt and archive it
            for key, record in database["prompts"].items():
                if (
                    key.startswith(base_key)
                    and record.get("metadata", {}).get("agent") == agent_type
                    and record.get("metadata", {}).get("stage") == numeric_stage
                    and record.get("metadata", {}).get("status") == "active"
                ):
                    # Mark existing as inactive (archived)
                    record["metadata"]["status"] = "inactive"
                    record["metadata"]["archived_at"] = datetime.now().isoformat()

            # Generate new prompt key with unique ID
            new_prompt_key = f"{base_key}_{next_id}"

            # Prepare new prompt record (removed version field)
            prompt_record = {
                "metadata": {
                    "id": next_id,
                    "agent": agent_type,
                    "stage": numeric_stage,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "status": "active",
                    "note": prompt_data.get("metadata", {}).get(
                        "note", f"{agent_type.title()} stage {stage_id}"
                    ),
                },
                "configuration": prompt_data.get("configuration", {"sections": {}}),
            }

            # Save new prompt to database
            database["prompts"][new_prompt_key] = prompt_record

            # Save database
            success = self._save_stage_prompts_database(database)

            if success and self.logger:
                self.logger.info(
                    f"Saved stage prompt: {stage_id}/{agent_type} ID={next_id}, archived previous versions"
                )

            return success

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving stage prompt for {stage_id}/{agent_type}: {e}")
            return False

    def get_stage_prompt_by_key(self, prompt_key: str) -> Optional[Dict[str, Any]]:
        """
        Get stage prompt by database key.

        Args:
            prompt_key: Database key (e.g., "supervisor_stage_1")

        Returns:
            Stage prompt record or None if not found
        """
        try:
            database = self._load_stage_prompts_database()
            return database.get("prompts", {}).get(prompt_key)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting stage prompt by key {prompt_key}: {e}")
            return None

    def get_all_stage_prompts_for_agent(self, agent: str) -> List[Dict[str, Any]]:
        """
        Get all stage prompts for specific agent.

        Args:
            agent: Agent type (therapist, supervisor)

        Returns:
            List of stage prompt records for the agent
        """
        try:
            database = self._load_stage_prompts_database()
            results = []

            for prompt_key, prompt_record in database.get("prompts", {}).items():
                if prompt_record.get("metadata", {}).get("agent") == agent:
                    results.append(prompt_record)

            # Sort by stage number
            results.sort(key=lambda x: int(x.get("metadata", {}).get("stage", "0")))
            return results

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting stage prompts for agent {agent}: {e}")
            return []

    def get_all_stage_prompts_for_stage(self, stage: str) -> List[Dict[str, Any]]:
        """
        Get all stage prompts for specific stage.

        Args:
            stage: Stage identifier

        Returns:
            List of stage prompt records for the stage
        """
        try:
            # Convert stage_id to numeric stage number for JSON database lookup
            numeric_stage = self._convert_stage_id_to_numeric(stage)
            if numeric_stage is None:
                if self.logger:
                    self.logger.warning(f"Cannot convert stage '{stage}' to numeric stage")
                return []

            database = self._load_stage_prompts_database()
            results = []

            for prompt_key, prompt_record in database.get("prompts", {}).items():
                if prompt_record.get("metadata", {}).get("stage") == numeric_stage:
                    results.append(prompt_record)

            # Sort by agent name
            results.sort(key=lambda x: x.get("metadata", {}).get("agent", ""))
            return results

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting stage prompts for stage {stage}: {e}")
            return []

    def list_all_stage_prompts(self) -> List[Dict[str, Any]]:
        """
        List all stage prompts in database.

        Returns:
            List of all stage prompt records with metadata
        """
        try:
            database = self._load_stage_prompts_database()
            results = []

            for prompt_key, prompt_record in database.get("prompts", {}).items():
                # Add database key to metadata for reference
                record_with_key = prompt_record.copy()
                record_with_key["metadata"]["database_key"] = prompt_key
                results.append(record_with_key)

            # Sort by agent, then by stage
            results.sort(
                key=lambda x: (
                    x.get("metadata", {}).get("agent", ""),
                    int(x.get("metadata", {}).get("stage", "0")),
                )
            )

            return results

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error listing all stage prompts: {e}")
            return []

    def _create_fallback_system_prompt(self, agent_type: str) -> Dict[str, Any]:
        """Create fallback system prompt if database is empty."""
        return {
            "metadata": {
                "id": 999,  # High fallback ID
                "agent": agent_type,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "active",
                "note": f"Fallback {agent_type} system prompt - populate database for better prompts",
            },
            "configuration": {
                "sections": {
                    "ai_role": {
                        "title": "1. Rola AI",
                        "content": f"System prompt dla {agent_type} - skonfiguruj w bazie danych system_prompts.json",
                    }
                }
            },
        }

    def _create_fallback_stage_prompt(self, stage_id: str, agent_type: str) -> Dict[str, Any]:
        """Create fallback stage prompt if database is empty."""
        return {
            "metadata": {
                "id": 998,  # High fallback ID
                "agent": agent_type,
                "stage": stage_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "active",
                "note": f"Fallback {agent_type} stage {stage_id} prompt - populate database for better prompts",
            },
            "configuration": {
                "sections": {
                    "placeholder": {
                        "title": f"Etap {stage_id} - {agent_type}",
                        "content": f"Prompt etapowy dla {agent_type} etap {stage_id} - skonfiguruj w bazie danych stage_prompts.json",
                    }
                }
            },
        }

    # =====================================================================================
    # UTILITY METHODS
    # =====================================================================================

    def generate_prompt_text(self, prompt_data: Dict[str, Any], prompt_type: str = "stage") -> str:
        """
        Generate final prompt text from structured data.

        Args:
            prompt_data: Structured prompt configuration
            prompt_type: Type of prompt (stage, system)

        Returns:
            Generated prompt text ready for LLM consumption
        """
        prompt_parts = []

        # Get metadata
        metadata = prompt_data.get("metadata", {})
        prompt_parts.append(f"# PROMPT {prompt_type.upper()} - ID {metadata.get('id', 'unknown')}")
        prompt_parts.append("")

        # Generate content from sections
        sections = prompt_data.get("configuration", {}).get("sections", {})

        for key, section in sections.items():
            title = section.get("title", key.title())
            content = section.get("content", "")

            if content.strip():
                prompt_parts.append(f"## {title}")
                prompt_parts.append(content)
                prompt_parts.append("")

        return "\n".join(prompt_parts)

    def validate_prompt_structure(self, prompt_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate prompt data structure and return validation results.

        Args:
            prompt_data: Prompt data to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required top-level structure
        if "metadata" not in prompt_data:
            errors.append("Missing 'metadata' section")

        if "configuration" not in prompt_data:
            errors.append("Missing 'configuration' section")

        # Check metadata structure (removed version from required fields)
        metadata = prompt_data.get("metadata", {})
        required_metadata = ["id", "status"]
        for field in required_metadata:
            if field not in metadata:
                errors.append(f"Missing metadata field: {field}")

        # Check ID is numeric (removed version validation)
        prompt_id = metadata.get("id")
        if not isinstance(prompt_id, int):
            errors.append("ID must be a numeric integer")

        # Check configuration structure
        config = prompt_data.get("configuration", {})
        if "sections" not in config:
            errors.append("Missing 'sections' in configuration")

        sections = config.get("sections", {})
        if not sections:
            errors.append("At least one section is required")

        # Check section structure
        for section_name, section_data in sections.items():
            if "title" not in section_data:
                errors.append(f"Section '{section_name}' missing title")
            if "content" not in section_data:
                errors.append(f"Section '{section_name}' missing content")

        return len(errors) == 0, errors

    def _find_next_global_id(self, database: Dict[str, Any]) -> int:
        """
        Find next globally unique ID across all prompts in the database.

        Args:
            database: The database to search

        Returns:
            Next available unique ID
        """
        max_id = 0

        for prompt_key, prompt_record in database.get("prompts", {}).items():
            prompt_id = prompt_record.get("metadata", {}).get("id", 0)
            if isinstance(prompt_id, int):
                max_id = max(max_id, prompt_id)

        return max_id + 1

    def _unescape_json_strings(self, data: Any) -> Any:
        """
        Recursively unescape JSON strings in data structure.
        Converts all escaped strings: \\" to ", \\\\n to newline, \\\\\\\\ to \\, etc.

        Args:
            data: Data structure to process

        Returns:
            Data with unescaped strings
        """
        if isinstance(data, dict):
            return {key: self._unescape_json_strings(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._unescape_json_strings(item) for item in data]
        elif isinstance(data, str):
            # Comprehensive unescaping of all common JSON escape sequences
            # Order matters - do \\\\ first to avoid double processing
            return (
                data.replace("\\\\", "\\")  # Double backslash to single
                .replace('\\"', '"')  # Escaped quote to quote
                .replace("\\'", "'")  # Escaped single quote
                .replace("\\n", "\n")  # Escaped newline to newline
                .replace("\\r", "\r")  # Escaped carriage return
                .replace("\\t", "\t")  # Escaped tab to tab
                .replace("\\b", "\b")  # Escaped backspace
                .replace("\\f", "\f")  # Escaped form feed
                .replace("\\/", "/")
            )  # Escaped forward slash
        else:
            return data

    def _convert_stage_id_to_numeric(self, stage_id: str) -> Optional[int]:
        """
        Convert stage ID to numeric stage number for JSON database lookup.

        Maps stage IDs from stages.json to numeric stages used in stage_prompts.json:
        - "opening" (order 1) -> 1
        - "resources" (order 2) -> 2
        - "scaling" (order 3) -> 3
        - "small_steps" (order 4) -> 4
        - "summary" (order 5) -> 5
        - Stage 6 is safety monitoring (not in stages.json, but exists in prompts)

        Args:
            stage_id: Stage identifier (e.g., "opening", "resources")

        Returns:
            Numeric stage number or None if not found
        """
        stage_mapping = {
            "opening": 1,
            "resources": 2,
            "scaling": 3,
            "small_steps": 4,
            "summary": 5,
            "rest": 6,  # Rest and casual conversation stage
            "safety_monitoring": 6,  # Special stage for crisis monitoring (same as rest)
        }

        # Also support direct numeric conversion for backwards compatibility
        if stage_id.isdigit():
            numeric_stage = int(stage_id)
            if 1 <= numeric_stage <= 6:
                return numeric_stage

        return stage_mapping.get(stage_id)
