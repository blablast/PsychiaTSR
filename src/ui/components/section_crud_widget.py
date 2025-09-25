"""Section CRUD Widget - Pure UI Component with clean separation."""

import streamlit as st
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass

from ...core.prompts.domain.prompt_section import PromptSection


@dataclass
class SectionCRUDConfig:
    """Configuration for section CRUD widget."""

    show_add_button: bool = True
    show_edit_inline: bool = True
    show_delete_button: bool = True
    show_duplicate_button: bool = True
    show_move_buttons: bool = True
    max_title_length: int = 100
    max_content_length: int = 5000
    confirm_delete: bool = True


@dataclass
class SectionCRUDCallbacks:
    """Callbacks for section CRUD operations - pure functions."""

    on_create: Optional[Callable[[str, str, int], Any]] = None
    on_update: Optional[Callable[[str, str, str], Any]] = None  # section_id, title, content
    on_delete: Optional[Callable[[str], Any]] = None  # section_id
    on_duplicate: Optional[Callable[[str], Any]] = None  # section_id
    on_move_up: Optional[Callable[[str], Any]] = None  # section_id
    on_move_down: Optional[Callable[[str], Any]] = None  # section_id


class SectionCRUDWidget:
    """
    Pure UI widget for section CRUD operations.

    Pure UI widget that:
    - Handles UI logic only (Streamlit components, state management)
    - Delegates business logic via callbacks
    - Receives data as parameters rather than accessing directly
    - Uses Streamlit session state properly
    """

    def __init__(self, config: SectionCRUDConfig = None):
        """Initialize widget with configuration."""
        self.config = config or SectionCRUDConfig()

    def render(self,
               sections: List[PromptSection],
               callbacks: SectionCRUDCallbacks,
               widget_key: str = "section_crud") -> None:
        """
        Render the complete CRUD interface.

        Args:
            sections: List of sections to display (from business layer)
            callbacks: Callback functions for operations (to business layer)
            widget_key: Unique key for this widget instance
        """
        # Initialize widget state
        if f"{widget_key}_state" not in st.session_state:
            st.session_state[f"{widget_key}_state"] = {
                "editing_section": None,
                "show_add_form": False
            }

        state = st.session_state[f"{widget_key}_state"]

        # Header with add button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"📝 Sections ({len(sections)})")

        with col2:
            if self.config.show_add_button:
                if st.button("➕ Add", key=f"{widget_key}_add_btn"):
                    state["show_add_form"] = not state["show_add_form"]

        # Add new section form
        if state["show_add_form"]:
            self._render_add_form(callbacks, widget_key)

        # Sections list
        if sections:
            self._render_sections_list(sections, callbacks, widget_key, state)
        else:
            st.info("No sections found. Add your first section above.")

    def _render_add_form(self, callbacks: SectionCRUDCallbacks, widget_key: str) -> None:
        """Render form for adding new section."""
        st.markdown("---")
        st.markdown("**Add New Section**")

        with st.form(f"{widget_key}_add_form"):
            col1, col2 = st.columns([1, 2])

            with col1:
                title = st.text_input(
                    "Title",
                    max_chars=self.config.max_title_length,
                    key=f"{widget_key}_add_title"
                )

                position = st.number_input(
                    "Position",
                    min_value=0,
                    value=0,
                    help="0 = beginning, -1 = end",
                    key=f"{widget_key}_add_position"
                )

            with col2:
                content = st.text_area(
                    "Content",
                    height=100,
                    max_chars=self.config.max_content_length,
                    key=f"{widget_key}_add_content"
                )

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.form_submit_button("✅ Create"):
                    if title and content:
                        if callbacks.on_create:
                            pos = None if position < 0 else position
                            callbacks.on_create(title, content, pos)
                        st.session_state[f"{widget_key}_state"]["show_add_form"] = False
                        st.rerun()
                    else:
                        st.error("Title and content are required")

            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state[f"{widget_key}_state"]["show_add_form"] = False
                    st.rerun()

        st.markdown("---")

    def _render_sections_list(self,
                            sections: List[PromptSection],
                            callbacks: SectionCRUDCallbacks,
                            widget_key: str,
                            state: Dict[str, Any]) -> None:
        """Render list of sections with CRUD operations."""

        for i, section in enumerate(sections):
            self._render_section_item(section, i, len(sections), callbacks, widget_key, state)

    def _render_section_item(self,
                           section: PromptSection,
                           index: int,
                           total_sections: int,
                           callbacks: SectionCRUDCallbacks,
                           widget_key: str,
                           state: Dict[str, Any]) -> None:
        """Render individual section with CRUD controls."""

        section_key = f"{widget_key}_section_{section.id}"

        # Section container
        with st.container():
            # Header with controls
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                # Editable title
                if self.config.show_edit_inline and state["editing_section"] == section.id:
                    new_title = st.text_input(
                        "Title",
                        value=section.title,
                        key=f"{section_key}_edit_title"
                    )
                else:
                    st.markdown(f"**{index + 1}. {section.title}**")

            with col2:
                # Move buttons
                if self.config.show_move_buttons:
                    move_col1, move_col2 = st.columns(2)

                    with move_col1:
                        if index > 0:
                            if st.button("⬆️", key=f"{section_key}_up", help="Move up"):
                                if callbacks.on_move_up:
                                    callbacks.on_move_up(section.id)
                                st.rerun()

                    with move_col2:
                        if index < total_sections - 1:
                            if st.button("⬇️", key=f"{section_key}_down", help="Move down"):
                                if callbacks.on_move_down:
                                    callbacks.on_move_down(section.id)
                                st.rerun()

            with col3:
                # Action buttons
                action_col1, action_col2, action_col3, action_col4 = st.columns(4)

                with action_col1:
                    # Edit toggle
                    if self.config.show_edit_inline:
                        if state["editing_section"] == section.id:
                            if st.button("💾", key=f"{section_key}_save", help="Save"):
                                # Save changes
                                new_title = st.session_state.get(f"{section_key}_edit_title", section.title)
                                new_content = st.session_state.get(f"{section_key}_edit_content", section.content)

                                if callbacks.on_update:
                                    callbacks.on_update(section.id, new_title, new_content)
                                state["editing_section"] = None
                                st.rerun()
                        else:
                            if st.button("✏️", key=f"{section_key}_edit", help="Edit"):
                                state["editing_section"] = section.id
                                st.rerun()

                with action_col2:
                    # Duplicate button
                    if self.config.show_duplicate_button:
                        if st.button("📋", key=f"{section_key}_dup", help="Duplicate"):
                            if callbacks.on_duplicate:
                                callbacks.on_duplicate(section.id)
                            st.rerun()

                with action_col3:
                    # Delete button
                    if self.config.show_delete_button:
                        if st.button("🗑️", key=f"{section_key}_del", help="Delete"):
                            if self.config.confirm_delete:
                                # Store delete request in state for confirmation
                                st.session_state[f"{section_key}_delete_confirm"] = True
                                st.rerun()
                            else:
                                if callbacks.on_delete:
                                    callbacks.on_delete(section.id)
                                st.rerun()

            # Content area
            if state["editing_section"] == section.id:
                # Edit mode
                new_content = st.text_area(
                    "Content",
                    value=section.content,
                    height=150,
                    key=f"{section_key}_edit_content"
                )

                # Edit controls
                edit_col1, edit_col2, edit_col3 = st.columns([1, 1, 2])

                with edit_col1:
                    if st.button("✅ Save Changes", key=f"{section_key}_save2"):
                        new_title = st.session_state.get(f"{section_key}_edit_title", section.title)
                        if callbacks.on_update:
                            callbacks.on_update(section.id, new_title, new_content)
                        state["editing_section"] = None
                        st.rerun()

                with edit_col2:
                    if st.button("❌ Cancel Edit", key=f"{section_key}_cancel"):
                        state["editing_section"] = None
                        st.rerun()

                with edit_col3:
                    # Show character count
                    char_count = len(new_content) if new_content else 0
                    max_chars = self.config.max_content_length
                    color = "red" if char_count > max_chars else "green"
                    st.markdown(f"<span style='color: {color}'>Characters: {char_count}/{max_chars}</span>",
                              unsafe_allow_html=True)
            else:
                # View mode
                if section.content:
                    with st.expander(f"Content ({len(section.content)} chars)", expanded=False):
                        st.text(section.content)
                else:
                    st.info("No content")

            # Delete confirmation dialog
            delete_key = f"{section_key}_delete_confirm"
            if st.session_state.get(delete_key, False):
                st.warning(f"Delete section '{section.title}'?")

                conf_col1, conf_col2, conf_col3 = st.columns([1, 1, 2])

                with conf_col1:
                    if st.button("🗑️ Yes, Delete", key=f"{section_key}_confirm_del"):
                        if callbacks.on_delete:
                            callbacks.on_delete(section.id)
                        st.session_state[delete_key] = False
                        st.rerun()

                with conf_col2:
                    if st.button("❌ Cancel", key=f"{section_key}_cancel_del"):
                        st.session_state[delete_key] = False
                        st.rerun()

            # Section metadata (if available)
            if section.metadata or section.created_at:
                with st.expander("📋 Metadata", expanded=False):
                    info_col1, info_col2 = st.columns(2)

                    with info_col1:
                        st.write(f"**ID:** `{section.id[:8]}...`")
                        st.write(f"**Order:** {section.order}")
                        st.write(f"**Type:** {section.section_type}")

                    with info_col2:
                        if section.created_at:
                            st.write(f"**Created:** {section.created_at.strftime('%Y-%m-%d %H:%M')}")
                        if section.updated_at:
                            st.write(f"**Updated:** {section.updated_at.strftime('%Y-%m-%d %H:%M')}")

            st.markdown("---")

    def render_compact(self,
                      sections: List[PromptSection],
                      callbacks: SectionCRUDCallbacks,
                      widget_key: str = "compact_crud") -> None:
        """
        Render compact version for smaller spaces.

        Args:
            sections: List of sections
            callbacks: Operation callbacks
            widget_key: Unique widget key
        """
        st.markdown(f"**📝 {len(sections)} Sections**")

        for i, section in enumerate(sections):
            col1, col2, col3 = st.columns([4, 1, 1])

            with col1:
                st.markdown(f"{i+1}. **{section.title}** ({len(section.content)} chars)")

            with col2:
                if st.button("✏️", key=f"{widget_key}_edit_{section.id}", help="Edit"):
                    # Trigger edit callback or navigate to full editor
                    pass

            with col3:
                if st.button("🗑️", key=f"{widget_key}_del_{section.id}", help="Delete"):
                    if callbacks.on_delete:
                        callbacks.on_delete(section.id)
                    st.rerun()