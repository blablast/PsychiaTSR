"""Section Reorder Widget - Drag & Drop functionality with clean separation."""

import streamlit as st
from typing import List, Callable, Optional, Dict, Any
from dataclasses import dataclass

from ...core.prompts.domain.prompt_section import PromptSection


@dataclass
class ReorderConfig:
    """Configuration for section reordering widget."""

    show_preview: bool = True
    show_positions: bool = True
    compact_mode: bool = False
    max_title_display: int = 50


class SectionReorderWidget:
    """
    Pure UI widget for section reordering with drag-and-drop simulation.

    Since Streamlit doesn't have native drag-and-drop, we implement
    intuitive up/down controls and list manipulation.

    Maintains strict UI/BL separation:
    - Pure UI logic (Streamlit components, state)
    - No business logic (delegates via callbacks)
    - Receives data as parameters, returns actions via callbacks
    """

    def __init__(self, config: ReorderConfig = None):
        """Initialize reorder widget."""
        self.config = config or ReorderConfig()

    def render(self,
               sections: List[PromptSection],
               on_reorder: Callable[[List[str]], Any],
               widget_key: str = "reorder_widget") -> None:
        """
        Render the section reordering interface.

        Args:
            sections: Current sections in order
            on_reorder: Callback when order changes - receives list of section IDs
            widget_key: Unique widget key
        """
        if not sections:
            st.info("No sections to reorder")
            return

        # Initialize reorder state
        state_key = f"{widget_key}_order_state"
        if state_key not in st.session_state:
            st.session_state[state_key] = {
                "current_order": [s.id for s in sections],
                "has_changes": False
            }

        state = st.session_state[state_key]

        # Header
        st.subheader("🔄 Reorder Sections")

        if self.config.show_preview:
            self._render_preview_info(sections, state)

        # Main reorder interface
        self._render_reorder_list(sections, state, widget_key, on_reorder)

        # Control buttons
        self._render_control_buttons(sections, state, widget_key, on_reorder)

    def _render_preview_info(self, sections: List[PromptSection], state: Dict[str, Any]) -> None:
        """Render preview information."""
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Sections", len(sections))

        with col2:
            changes = "Yes" if state["has_changes"] else "No"
            st.metric("Has Changes", changes)

        with col3:
            if state["has_changes"]:
                st.warning("⚠️ Unsaved changes")
            else:
                st.success("✅ No changes")

    def _render_reorder_list(self,
                           sections: List[PromptSection],
                           state: Dict[str, Any],
                           widget_key: str,
                           on_reorder: Callable[[List[str]], Any]) -> None:
        """Render the main reordering list."""

        st.markdown("**Drag sections to reorder:**")

        # Create sections lookup
        sections_dict = {s.id: s for s in sections}

        # Render sections in current order
        current_order = state["current_order"]

        for i, section_id in enumerate(current_order):
            if section_id not in sections_dict:
                continue  # Skip missing sections

            section = sections_dict[section_id]
            self._render_reorderable_item(
                section, i, len(current_order), state, widget_key
            )

    def _render_reorderable_item(self,
                               section: PromptSection,
                               position: int,
                               total_count: int,
                               state: Dict[str, Any],
                               widget_key: str) -> None:
        """Render individual reorderable section item."""

        item_key = f"{widget_key}_item_{section.id}"

        # Container for the item
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([0.5, 3, 1, 1, 0.5])

            # Position indicator
            with col1:
                if self.config.show_positions:
                    st.markdown(f"**{position + 1}**")

            # Section info
            with col2:
                title_display = section.title
                if len(title_display) > self.config.max_title_display:
                    title_display = title_display[:self.config.max_title_display] + "..."

                if self.config.compact_mode:
                    st.markdown(f"**{title_display}**")
                else:
                    st.markdown(f"**{title_display}**")
                    st.caption(f"Content: {len(section.content)} chars | Type: {section.section_type}")

            # Move up button
            with col3:
                can_move_up = position > 0
                if can_move_up:
                    if st.button("⬆️", key=f"{item_key}_up", help="Move up"):
                        self._move_section(state, section.id, position, position - 1)
                        st.rerun()
                else:
                    st.markdown("⬆️")  # Disabled placeholder

            # Move down button
            with col4:
                can_move_down = position < total_count - 1
                if can_move_down:
                    if st.button("⬇️", key=f"{item_key}_down", help="Move down"):
                        self._move_section(state, section.id, position, position + 1)
                        st.rerun()
                else:
                    st.markdown("⬇️")  # Disabled placeholder

            # Drag handle (visual only)
            with col5:
                st.markdown("⋮⋮")

    def _render_control_buttons(self,
                              sections: List[PromptSection],
                              state: Dict[str, Any],
                              widget_key: str,
                              on_reorder: Callable[[List[str]], Any]) -> None:
        """Render control buttons for reordering operations."""

        st.markdown("---")

        col1, col2, col3, col4, col5 = st.columns(5)

        # Apply changes
        with col1:
            if st.button("✅ Apply Order",
                        key=f"{widget_key}_apply",
                        disabled=not state["has_changes"]):
                if on_reorder:
                    on_reorder(state["current_order"])
                state["has_changes"] = False
                st.success("Order applied successfully!")
                st.rerun()

        # Reset changes
        with col2:
            if st.button("🔄 Reset",
                        key=f"{widget_key}_reset",
                        disabled=not state["has_changes"]):
                state["current_order"] = [s.id for s in sections]
                state["has_changes"] = False
                st.info("Order reset to original")
                st.rerun()

        # Quick operations
        with col3:
            if st.button("🔀 Reverse All", key=f"{widget_key}_reverse"):
                state["current_order"] = list(reversed(state["current_order"]))
                state["has_changes"] = True
                st.rerun()

        with col4:
            if st.button("🎲 Shuffle", key=f"{widget_key}_shuffle"):
                import random
                state["current_order"] = state["current_order"].copy()
                random.shuffle(state["current_order"])
                state["has_changes"] = True
                st.rerun()

        with col5:
            # Show reorder by position input
            if st.button("📝 Manual Order", key=f"{widget_key}_manual"):
                st.session_state[f"{widget_key}_show_manual"] = True
                st.rerun()

        # Manual reorder input (if enabled)
        if st.session_state.get(f"{widget_key}_show_manual", False):
            self._render_manual_reorder(sections, state, widget_key)

    def _render_manual_reorder(self,
                             sections: List[PromptSection],
                             state: Dict[str, Any],
                             widget_key: str) -> None:
        """Render manual position input interface."""

        st.markdown("---")
        st.markdown("**Manual Reordering**")

        # Create sections lookup
        sections_dict = {s.id: s for s in sections}

        with st.form(f"{widget_key}_manual_form"):
            st.markdown("Enter new positions (1-based):")

            new_positions = {}

            for i, section_id in enumerate(state["current_order"]):
                if section_id not in sections_dict:
                    continue

                section = sections_dict[section_id]
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(section.title)

                with col2:
                    pos = st.number_input(
                        "Pos",
                        min_value=1,
                        max_value=len(sections),
                        value=i + 1,
                        key=f"{widget_key}_pos_{section_id}",
                        label_visibility="collapsed"
                    )
                    new_positions[section_id] = pos - 1  # Convert to 0-based

            col1, col2 = st.columns(2)

            with col1:
                if st.form_submit_button("✅ Apply Manual Order"):
                    # Sort sections by new position
                    sorted_sections = sorted(new_positions.items(), key=lambda x: x[1])
                    state["current_order"] = [section_id for section_id, _ in sorted_sections]
                    state["has_changes"] = True
                    st.session_state[f"{widget_key}_show_manual"] = False
                    st.rerun()

            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state[f"{widget_key}_show_manual"] = False
                    st.rerun()

    def _move_section(self, state: Dict[str, Any], section_id: str, from_pos: int, to_pos: int) -> None:
        """Move section from one position to another."""
        current_order = state["current_order"].copy()

        # Remove from current position
        section_id_moved = current_order.pop(from_pos)

        # Insert at new position
        current_order.insert(to_pos, section_id_moved)

        # Update state
        state["current_order"] = current_order
        state["has_changes"] = True

    def render_compact_reorder(self,
                             sections: List[PromptSection],
                             on_reorder: Callable[[List[str]], Any],
                             widget_key: str = "compact_reorder") -> None:
        """
        Render compact version for smaller spaces.

        Args:
            sections: Sections to reorder
            on_reorder: Callback for order changes
            widget_key: Unique widget key
        """
        if not sections:
            return

        st.markdown("**🔄 Quick Reorder**")

        # Simple up/down for each section
        for i, section in enumerate(sections):
            col1, col2, col3, col4 = st.columns([2, 0.5, 0.5, 1])

            with col1:
                st.write(f"{i+1}. {section.title[:30]}...")

            with col2:
                if i > 0 and st.button("⬆️", key=f"{widget_key}_up_{section.id}"):
                    # Create new order with this section moved up
                    new_order = [s.id for s in sections]
                    new_order[i], new_order[i-1] = new_order[i-1], new_order[i]
                    on_reorder(new_order)
                    st.rerun()

            with col3:
                if i < len(sections) - 1 and st.button("⬇️", key=f"{widget_key}_down_{section.id}"):
                    # Create new order with this section moved down
                    new_order = [s.id for s in sections]
                    new_order[i], new_order[i+1] = new_order[i+1], new_order[i]
                    on_reorder(new_order)
                    st.rerun()