"""
PromptUIService - UI Facade for prompt management operations.

This service acts as a facade between UI components and the core business logic,
providing UI-specific methods while delegating actual business operations to
the PromptManagementService. It handles UI concerns like error messaging,
validation feedback, and data formatting for display.

Key responsibilities:
- Provide UI-friendly methods for prompt operations
- Handle UI-specific error messaging and validation feedback
- Format data for display in UI components
- Manage UI state and user feedback
- Delegate business operations to core services
"""
import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from ...core.services.prompt_management_service import PromptManagementService
from ...core.session import load_stages


class PromptUIService:
    """
    UI Facade service for prompt management operations.

    This service provides a clean interface for UI components to interact
    with prompt management functionality while keeping business logic
    separated from UI concerns.
    """

    def __init__(self, config_dir: str = "config", logger=None):
        """
        Initialize the UI service with dependencies.

        Args:
            config_dir: Configuration directory path
            logger: Optional logger for operations
        """
        self.prompt_service = PromptManagementService(config_dir, logger)
        self.logger = logger

    # =====================================================================================
    # SYSTEM PROMPT UI OPERATIONS
    # =====================================================================================

    def load_system_prompt_for_editing(self, agent_type: str) -> Dict[str, Any]:
        """
        Load system prompt for editing in the UI.

        Args:
            agent_type: Type of agent (therapist, supervisor)

        Returns:
            System prompt data ready for editing
        """
        try:
            prompt_data = self.prompt_service.get_active_system_prompt(agent_type)

            # Show loading feedback
            if prompt_data.get("metadata", {}).get("note") == "Converted from legacy format":
                st.info("🔄 Załadowano prompt w starym formacie - zaleca się aktualizację")

            return prompt_data

        except Exception as e:
            st.error(f"❌ Błąd ładowania promptu systemowego: {e}")
            if self.logger:
                self.logger.error(f"UI error loading system prompt for {agent_type}: {e}")

            # Return minimal fallback for UI
            return self._create_ui_fallback_system_prompt(agent_type)

    def save_system_prompt_from_ui(self, agent_type: str, prompt_data: Dict[str, Any]) -> bool:
        """
        Save system prompt from UI with user feedback.

        Args:
            agent_type: Type of agent (therapist, supervisor)
            prompt_data: Prompt data from UI form

        Returns:
            True if saved successfully
        """
        try:
            # Validate data structure
            is_valid, errors = self.prompt_service.validate_prompt_structure(prompt_data)

            if not is_valid:
                st.error("❌ Błąd walidacji danych:")
                for error in errors:
                    st.error(f"  • {error}")
                return False

            # Attempt to save
            success = self.prompt_service.save_system_prompt(agent_type, prompt_data)

            if success:
                prompt_id = prompt_data["metadata"].get("id", "unknown")
                st.success(f"✅ Zapisano prompt systemowy: {agent_type}")
                return True
            else:
                st.error("❌ Błąd zapisu - sprawdź logi systemu")
                return False

        except Exception as e:
            st.error(f"❌ Nieoczekiwany błąd zapisu: {e}")
            if self.logger:
                self.logger.error(f"UI error saving system prompt for {agent_type}: {e}")
            return False

    def get_system_prompt_versions_for_ui(self, agent_type: str) -> List[Dict[str, Any]]:
        """
        Get list of system prompt versions formatted for UI display.

        Args:
            agent_type: Type of agent to search for

        Returns:
            List of versions with UI-friendly formatting
        """
        versions = self.prompt_service.list_system_prompt_versions(agent_type)

        # Add UI-friendly formatting
        for version in versions:
            # Use ID instead of version for display
            prompt_id = version.get("id", "unknown")
            version["display_version"] = f"ID {prompt_id}"

            status = version.get("status", "unknown")
            version["status_emoji"] = "🟢" if status == "active" else "⚪"

            # Format dates for UI
            created = version.get("created_at", "")
            if created:
                version["display_created"] = created.split("T")[0]  # Just the date part

        return versions

    # =====================================================================================
    # STAGE PROMPT UI OPERATIONS
    # =====================================================================================

    def load_stage_prompt_for_editing(self, stage_id: str, agent_type: str) -> Dict[str, Any]:
        """
        Load stage prompt for editing in the UI.

        Args:
            stage_id: Stage identifier
            agent_type: Type of agent (therapist, supervisor)

        Returns:
            Stage prompt data ready for editing
        """
        try:
            prompt_data = self.prompt_service.get_active_stage_prompt(stage_id, agent_type)

            # Show loading feedback
            if prompt_data.get("metadata", {}).get("note") == "Converted from legacy format":
                st.info("🔄 Załadowano prompt w starym formacie - zaleca się aktualizację")

            return prompt_data

        except Exception as e:
            st.error(f"❌ Błąd ładowania promptu etapowego: {e}")
            if self.logger:
                self.logger.error(f"UI error loading stage prompt for {stage_id}/{agent_type}: {e}")

            # Return minimal fallback for UI
            return self._create_ui_fallback_stage_prompt(stage_id, agent_type)

    def save_stage_prompt_from_ui(self, stage_id: str, agent_type: str, prompt_data: Dict[str, Any]) -> bool:
        """
        Save stage prompt from UI with user feedback.

        Args:
            stage_id: Stage identifier
            agent_type: Type of agent (therapist, supervisor)
            prompt_data: Prompt data from UI form

        Returns:
            True if saved successfully
        """
        try:
            # Validate data structure
            is_valid, errors = self.prompt_service.validate_prompt_structure(prompt_data)

            if not is_valid:
                st.error("❌ Błąd walidacji danych:")
                for error in errors:
                    st.error(f"  • {error}")
                return False

            # Attempt to save
            success = self.prompt_service.save_stage_prompt(stage_id, agent_type, prompt_data)

            if success:
                prompt_id = prompt_data["metadata"].get("id", "unknown")
                st.success(f"✅ Zapisano prompt etapowy: {stage_id} ({agent_type}) - ID {prompt_id}")
                return True
            else:
                st.error("❌ Błąd zapisu - sprawdź logi systemu")
                return False

        except Exception as e:
            st.error(f"❌ Nieoczekiwany błąd zapisu: {e}")
            if self.logger:
                self.logger.error(f"UI error saving stage prompt for {stage_id}/{agent_type}: {e}")
            return False

    def get_available_stages_for_ui(self) -> List[Dict[str, Any]]:
        """
        Get list of available therapy stages formatted for UI.

        Returns:
            List of stages with UI-friendly formatting
        """
        try:
            stages = load_stages()

            # Add UI-friendly formatting
            for stage in stages:
                stage["display_name"] = f"{stage.get('order', '?')}. {stage.get('name', 'Unknown')}"

            return stages

        except Exception as e:
            st.error(f"❌ Błąd ładowania listy etapów: {e}")
            if self.logger:
                self.logger.error(f"UI error loading stages: {e}")
            return []

    def check_stage_prompt_availability(self, stage_id: str, agent_type: str) -> Tuple[bool, str]:
        """
        Check if stage prompt is available and return status message.

        Args:
            stage_id: Stage identifier
            agent_type: Type of agent

        Returns:
            Tuple of (is_available, status_message)
        """
        try:
            prompt_data = self.prompt_service.get_active_stage_prompt(stage_id, agent_type)
            metadata = prompt_data.get("metadata", {})

            # Check if this is a fallback prompt (high ID numbers 998, 999)
            prompt_id = metadata.get("id", 0)
            if isinstance(prompt_id, int) and prompt_id >= 998:
                return False, "➕ Prompt będzie utworzony z template"
            else:
                return True, "✅ Prompt istnieje - gotowy do edycji"

        except Exception:
            return False, "⚠️ Błąd sprawdzania dostępności"

    # =====================================================================================
    # PROMPT GENERATION AND PREVIEW
    # =====================================================================================

    def generate_prompt_for_preview(self, prompt_data: Dict[str, Any], prompt_type: str = "stage") -> str:
        """
        Generate prompt text for preview in UI.

        Args:
            prompt_data: Structured prompt data
            prompt_type: Type of prompt (stage, system)

        Returns:
            Generated prompt text for display
        """
        try:
            return self.prompt_service.generate_prompt_text(prompt_data, prompt_type)
        except Exception as e:
            st.error(f"❌ Błąd generowania podglądu: {e}")
            return f"Błąd generowania podglądu: {e}"

    def show_prompt_statistics(self, prompt_text: str):
        """
        Display prompt statistics in UI.

        Args:
            prompt_text: Generated prompt text
        """
        if prompt_text:
            char_count = len(prompt_text)
            word_count = len(prompt_text.split())
            st.info(f"📊 **Statystyki:** {char_count} znaków, {word_count} słów")

    # =====================================================================================
    # UI HELPER METHODS
    # =====================================================================================

    def render_dynamic_sections_form(self, prompt_data: Dict[str, Any], form_key_prefix: str) -> Dict[str, Any]:
        """
        Render dynamic sections form based on prompt configuration.

        Args:
            prompt_data: Prompt data containing sections
            form_key_prefix: Prefix for form field keys

        Returns:
            Updated prompt data with form input values
        """
        sections = prompt_data.get("configuration", {}).get("sections", {})

        for key, section in sections.items():
            st.markdown(f"#### {section.get('title', key.title())}")

            new_content = st.text_area(
                "Treść sekcji:",
                value=section.get("content", ""),
                key=f"{form_key_prefix}_{key}",
                height=150,
                help=f"Edytuj zawartość sekcji: {section.get('title', key)}"
            )

            sections[key]["content"] = new_content

        return prompt_data

    # =====================================================================================
    # PRIVATE UI HELPER METHODS
    # =====================================================================================

    def _create_ui_fallback_system_prompt(self, agent_type: str) -> Dict[str, Any]:
        """Create minimal system prompt fallback for UI."""
        from datetime import datetime

        return {
            "metadata": {
                "id": f"{agent_type}_ui_fallback_v1_0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "active"
            },
            "configuration": {
                "sections": {
                    "error_notice": {
                        "title": "⚠️ Błąd ładowania",
                        "content": f"Nie udało się załadować promptu dla {agent_type}. Sprawdź logi i spróbuj ponownie."
                    }
                }
            }
        }

    def _create_ui_fallback_stage_prompt(self, stage_id: str, agent_type: str) -> Dict[str, Any]:
        """Create minimal stage prompt fallback for UI."""
        from datetime import datetime

        return {
            "metadata": {
                "id": f"{agent_type}_{stage_id}_ui_fallback_v1_0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "active"
            },
            "configuration": {
                "sections": {
                    "error_notice": {
                        "title": "⚠️ Błąd ładowania",
                        "content": f"Nie udało się załadować promptu dla {stage_id}/{agent_type}. Sprawdź logi i spróbuj ponownie."
                    }
                }
            }
        }