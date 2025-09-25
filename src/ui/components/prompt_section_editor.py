"""Main Prompt Section Editor - Orchestrates UI components with business logic."""

import streamlit as st
from typing import List, Dict, Any, Optional

from ...core.prompts.services.prompt_section_service import PromptSectionService
from ...core.prompts.domain.prompt_section import PromptSection
from .section_crud_widget import SectionCRUDWidget, SectionCRUDConfig, SectionCRUDCallbacks
from .section_reorder_widget import SectionReorderWidget, ReorderConfig


class PromptSectionEditor:
    """
    Main editor orchestrating UI components with business logic.

    Responsibilities:
    - Coordinate between UI widgets and business services
    - Handle business logic delegation
    - Manage editor state and error handling
    - Provide clean interface for page-level components

    Maintains strict separation:
    - UI widgets are pure UI (no business logic)
    - Business services are pure BL (no UI dependencies)
    - This class is the adapter layer between them
    """

    def __init__(self, config_dir: str = "config"):
        """Initialize editor with business service."""
        self.service = PromptSectionService(config_dir)
        self.crud_widget = SectionCRUDWidget()
        self.reorder_widget = SectionReorderWidget()

    def render_full_editor(self, prompt_id: str, editor_key: str = "section_editor") -> None:
        """
        Render complete section editor with all functionality.

        Args:
            prompt_id: ID of prompt to edit
            editor_key: Unique key for this editor instance
        """
        # Load data from business layer
        sections_result = self.service.get_sections(prompt_id)

        if not sections_result.success:
            st.error(f"Failed to load sections: {sections_result.error}")
            return

        sections = sections_result.sections

        # Editor tabs
        tab_crud, tab_reorder, tab_preview = st.tabs([
            "✏️ Edit Sections",
            "🔄 Reorder",
            "👀 Preview"
        ])

        with tab_crud:
            self._render_crud_tab(prompt_id, sections, editor_key)

        with tab_reorder:
            self._render_reorder_tab(prompt_id, sections, editor_key)

        with tab_preview:
            self._render_preview_tab(prompt_id, sections, editor_key)

    def _render_crud_tab(self, prompt_id: str, sections: List[PromptSection], editor_key: str) -> None:
        """Render CRUD operations tab."""
        st.markdown("### ✏️ Section Management")

        # Create callbacks that delegate to business service
        callbacks = SectionCRUDCallbacks(
            on_create=lambda title, content, position: self._handle_create_section(
                prompt_id, title, content, position
            ),
            on_update=lambda section_id, title, content: self._handle_update_section(
                prompt_id, section_id, title, content
            ),
            on_delete=lambda section_id: self._handle_delete_section(prompt_id, section_id),
            on_duplicate=lambda section_id: self._handle_duplicate_section(prompt_id, section_id),
            on_move_up=lambda section_id: self._handle_move_section(
                prompt_id, section_id, sections, "up"
            ),
            on_move_down=lambda section_id: self._handle_move_section(
                prompt_id, section_id, sections, "down"
            )
        )

        # Configure CRUD widget
        config = SectionCRUDConfig(
            show_add_button=True,
            show_edit_inline=True,
            show_delete_button=True,
            show_duplicate_button=True,
            show_move_buttons=True,
            confirm_delete=True
        )

        # Render CRUD widget (pure UI)
        self.crud_widget = SectionCRUDWidget(config)
        self.crud_widget.render(sections, callbacks, f"{editor_key}_crud")

    def _render_reorder_tab(self, prompt_id: str, sections: List[PromptSection], editor_key: str) -> None:
        """Render reordering tab."""
        st.markdown("### 🔄 Section Reordering")

        # Create reorder callback
        def handle_reorder(new_section_ids: List[str]) -> None:
            self._handle_reorder_sections(prompt_id, new_section_ids)

        # Configure reorder widget
        config = ReorderConfig(
            show_preview=True,
            show_positions=True,
            compact_mode=False
        )

        # Render reorder widget (pure UI)
        self.reorder_widget = SectionReorderWidget(config)
        self.reorder_widget.render(sections, handle_reorder, f"{editor_key}_reorder")

    def _render_preview_tab(self, prompt_id: str, sections: List[PromptSection], editor_key: str) -> None:
        """Render preview and statistics tab."""
        st.markdown("### 👀 Preview & Statistics")

        # Get statistics from business layer
        stats_result = self.service.get_statistics(prompt_id)

        if stats_result.success:
            # Display statistics
            col1, col2, col3, col4 = st.columns(4)

            stats = stats_result.statistics

            with col1:
                st.metric("Sections", stats.get("section_count", 0))

            with col2:
                st.metric("Total Words", stats.get("total_words", 0))

            with col3:
                st.metric("Total Characters", stats.get("total_characters", 0))

            with col4:
                st.metric("Empty Sections", stats.get("empty_sections", 0))

            # Preview generated prompt
            st.markdown("---")
            st.subheader("Generated Prompt Preview")

            try:
                prompt_text = self.service.generate_prompt_text(prompt_id)

                if prompt_text:
                    with st.expander("Full Prompt Text", expanded=False):
                        st.code(prompt_text, language="text")

                    # Show first 500 characters as preview
                    preview_text = prompt_text[:500] + ("..." if len(prompt_text) > 500 else "")
                    st.text_area("Preview (first 500 chars)", preview_text, height=200, disabled=True)
                else:
                    st.info("No content to preview")

            except Exception as e:
                st.error(f"Failed to generate preview: {e}")

        else:
            st.error(f"Failed to load statistics: {stats_result.error}")

    # =====================================================================================
    # BUSINESS LOGIC DELEGATION METHODS
    # =====================================================================================

    def _handle_create_section(self, prompt_id: str, title: str, content: str, position: Optional[int]) -> None:
        """Handle section creation by delegating to business service."""
        try:
            result = self.service.create_section(prompt_id, title, content, position)

            if result.success:
                st.success(f"✅ Section '{title}' created successfully")
            else:
                st.error(f"❌ Failed to create section: {result.error}")

        except Exception as e:
            st.error(f"❌ Error creating section: {e}")

    def _handle_update_section(self, prompt_id: str, section_id: str, title: str, content: str) -> None:
        """Handle section update by delegating to business service."""
        try:
            result = self.service.update_section(prompt_id, section_id, title, content)

            if result.success:
                st.success("✅ Section updated successfully")
            else:
                st.error(f"❌ Failed to update section: {result.error}")

        except Exception as e:
            st.error(f"❌ Error updating section: {e}")

    def _handle_delete_section(self, prompt_id: str, section_id: str) -> None:
        """Handle section deletion by delegating to business service."""
        try:
            result = self.service.delete_section(prompt_id, section_id)

            if result.success:
                st.success("✅ Section deleted successfully")
            else:
                st.error(f"❌ Failed to delete section: {result.error}")

        except Exception as e:
            st.error(f"❌ Error deleting section: {e}")

    def _handle_duplicate_section(self, prompt_id: str, section_id: str) -> None:
        """Handle section duplication by delegating to business service."""
        try:
            result = self.service.duplicate_section(prompt_id, section_id)

            if result.success:
                st.success("✅ Section duplicated successfully")
            else:
                st.error(f"❌ Failed to duplicate section: {result.error}")

        except Exception as e:
            st.error(f"❌ Error duplicating section: {e}")

    def _handle_move_section(self, prompt_id: str, section_id: str, sections: List[PromptSection], direction: str) -> None:
        """Handle section movement by delegating to business service."""
        try:
            # Find current position
            current_pos = None
            for i, section in enumerate(sections):
                if section.id == section_id:
                    current_pos = i
                    break

            if current_pos is None:
                st.error("Section not found")
                return

            # Calculate new position
            if direction == "up" and current_pos > 0:
                new_pos = current_pos - 1
            elif direction == "down" and current_pos < len(sections) - 1:
                new_pos = current_pos + 1
            else:
                return  # Can't move

            result = self.service.move_section(prompt_id, section_id, new_pos)

            if result.success:
                st.success(f"✅ Section moved {direction}")
            else:
                st.error(f"❌ Failed to move section: {result.error}")

        except Exception as e:
            st.error(f"❌ Error moving section: {e}")

    def _handle_reorder_sections(self, prompt_id: str, new_order: List[str]) -> None:
        """Handle section reordering by delegating to business service."""
        try:
            result = self.service.reorder_sections(prompt_id, new_order)

            if result.success:
                st.success("✅ Sections reordered successfully")
            else:
                st.error(f"❌ Failed to reorder sections: {result.error}")

        except Exception as e:
            st.error(f"❌ Error reordering sections: {e}")

    # =====================================================================================
    # CONVENIENCE METHODS
    # =====================================================================================

    def render_compact_editor(self, prompt_id: str, editor_key: str = "compact_editor") -> None:
        """
        Render compact version suitable for sidebars or smaller spaces.

        Args:
            prompt_id: ID of prompt to edit
            editor_key: Unique key for this editor
        """
        sections_result = self.service.get_sections(prompt_id)

        if not sections_result.success:
            st.error("Failed to load sections")
            return

        sections = sections_result.sections

        # Compact display
        st.markdown(f"**📝 {len(sections)} sections**")

        # Show compact CRUD or reorder based on mode
        mode = st.selectbox("Mode", ["Edit", "Reorder"], key=f"{editor_key}_mode")

        if mode == "Edit":
            callbacks = SectionCRUDCallbacks(
                on_delete=lambda section_id: self._handle_delete_section(prompt_id, section_id)
            )
            self.crud_widget.render_compact(sections, callbacks, f"{editor_key}_compact_crud")

        elif mode == "Reorder":
            def handle_compact_reorder(new_order: List[str]) -> None:
                self._handle_reorder_sections(prompt_id, new_order)

            self.reorder_widget.render_compact_reorder(
                sections, handle_compact_reorder, f"{editor_key}_compact_reorder"
            )

    def get_sections_summary(self, prompt_id: str) -> Dict[str, Any]:
        """
        Get summary information about sections (for external use).

        Args:
            prompt_id: Prompt ID

        Returns:
            Summary dictionary with stats
        """
        stats_result = self.service.get_statistics(prompt_id)
        sections_result = self.service.get_sections(prompt_id)

        return {
            "success": stats_result.success and sections_result.success,
            "section_count": stats_result.statistics.get("section_count", 0) if stats_result.success else 0,
            "total_chars": stats_result.statistics.get("total_characters", 0) if stats_result.success else 0,
            "has_empty": stats_result.statistics.get("empty_sections", 0) > 0 if stats_result.success else False,
            "error": stats_result.error if not stats_result.success else sections_result.error
        }