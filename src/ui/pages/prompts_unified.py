"""
Unified Prompts Management Page - Single page with popup editing.

This replaces the complex multi-mode prompts page with a clean, intuitive interface
where all prompts are visible at once with clear action buttons for editing and preview.

Key Features:
- Single page layout with all prompts visible
- Modal popup editing with full CRUD functionality
- st.markdown preview system
- Reuses existing business logic (PromptSectionService)
- Better UX with no mode switching required
"""

import streamlit as st
from typing import Dict, Any, List, Optional
import time

from ...core.prompts.services.prompt_section_service import PromptSectionService
from ...core.prompts.domain.prompt_section import PromptSection
from ...core.prompts.domain.prompt_template import PromptTemplate




def prompts_unified_page():
    """New unified prompts management page with dialog editing."""
    st.title("📝 Prompts Management")
    st.markdown("Manage all system and stage prompts in one place")

    # Initialize service
    service = PromptSectionService("config")

    try:
        # Get all available prompts
        prompt_ids = service.repository.list_prompt_ids()

        if not prompt_ids:
            st.warning("No prompts found in configuration")
            return

        # Main content area
        render_prompt_list(service, prompt_ids)


        # Footer with quick actions
        render_footer_actions(service, prompt_ids)

    except Exception as e:
        st.error(f"Failed to load prompts page: {e}")
        if st.button("🔄 Retry"):
            st.rerun()


def render_prompt_list(service: PromptSectionService, prompt_ids: List[str]):
    """Render clean list of all prompts with action buttons."""

    # Categorize prompts - system prompts take precedence over stage prompts
    system_prompts = [pid for pid in prompt_ids if "system" in pid.lower()]
    stage_prompts = [pid for pid in prompt_ids if "stage" in pid.lower() and "system" not in pid.lower()]

    # Add any remaining prompts that don't fit either category to stage prompts
    remaining_prompts = [pid for pid in prompt_ids if pid not in system_prompts and pid not in stage_prompts]
    if remaining_prompts:
        stage_prompts.extend(remaining_prompts)

    # System Prompts Section
    st.markdown("## 🏠 System Prompts")
    if system_prompts:
        st.caption(f"Found {len(system_prompts)} system prompts: {', '.join(system_prompts)}")
        for index, prompt_id in enumerate(system_prompts):
            render_prompt_card(service, prompt_id, "system", index)
    else:
        st.info("No system prompts found")

    st.markdown("---")

    # Stage Prompts Section
    st.markdown("## 🎯 Stage Prompts")
    if stage_prompts:
        st.caption(f"Found {len(stage_prompts)} stage prompts: {', '.join(stage_prompts)}")
        for index, prompt_id in enumerate(stage_prompts):
            render_prompt_card(service, prompt_id, "stage", index)
    else:
        st.info("No stage prompts found")


def render_prompt_card(service: PromptSectionService, prompt_id: str, prompt_type: str, card_index: int):
    """Render individual prompt card with action buttons."""

    # Get prompt info for display
    try:
        template_result = service.get_template(prompt_id)

        if template_result.success and template_result.template:
            template = template_result.template
            sections_count = len(template.sections)

            # Calculate basic stats
            total_content = " ".join([s.content for s in template.sections])
            word_count = len(total_content.split())
            char_count = len(total_content)

        else:
            sections_count = 0
            word_count = 0
            char_count = 0

    except Exception:
        sections_count = 0
        word_count = 0
        char_count = 0

    # Create unique key base using both prompt_id and card_index
    key_base = f"{prompt_type}_{card_index}_{prompt_id}".replace(" ", "_").replace(".", "_")

    # Render card
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([4, 1, 1, 1, 1])

        with col1:
            icon = "🩺" if "therapist" in prompt_id.lower() else "👥" if "supervisor" in prompt_id.lower() else "🎯"
            st.markdown(f"### {icon} {prompt_id}")

            # Stats row
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            with stats_col1:
                st.caption(f"📋 Sections: {sections_count}")
            with stats_col2:
                st.caption(f"📝 Words: {word_count}")
            with stats_col3:
                st.caption(f"📊 Chars: {char_count}")

        with col2:
            if st.button("✏️ Edit", key=f"edit_{key_base}", help=f"Edit {prompt_id}"):
                clear_all_dialogs()  # Clear any existing dialogs
                st.session_state[f"show_edit_dialog_{prompt_id}"] = True

        with col3:
            if st.button("👀 Preview", key=f"preview_{key_base}", help=f"Preview {prompt_id}"):
                clear_all_dialogs()  # Clear any existing dialogs
                st.session_state[f"show_preview_dialog_{prompt_id}"] = True

        with col4:
            if st.button("📊 Stats", key=f"stats_{key_base}", help=f"Show statistics for {prompt_id}"):
                show_prompt_stats(service, prompt_id)

        with col5:
            with st.popover("⚙️", help="More options"):
                st.markdown(f"**{prompt_id}**")
                if st.button("🔄 Reload", key=f"reload_{key_base}"):
                    st.success("Reloaded!")
                    time.sleep(0.5)
                    st.rerun()

                if st.button("🧪 Test", key=f"test_{key_base}"):
                    st.info("Test functionality coming soon!")

    st.markdown("---")

    # Render dialogs for this prompt
    render_prompt_dialogs(service, prompt_id)


def render_prompt_dialogs(service: PromptSectionService, prompt_id: str):
    """Render dialog boxes for edit and preview functionality."""

    # Only allow one dialog at a time across all prompts
    # Check if any dialog is currently open
    any_edit_open = any(st.session_state.get(f"show_edit_dialog_{pid}", False) for pid in get_all_prompt_ids(service))
    any_preview_open = any(st.session_state.get(f"show_preview_dialog_{pid}", False) for pid in get_all_prompt_ids(service))

    # Edit dialog for this specific prompt
    if st.session_state.get(f"show_edit_dialog_{prompt_id}") and not any_preview_open:
        @st.dialog(f"✏️ Edit {prompt_id}", width="large")
        def edit_dialog():
            render_edit_dialog_content(service, prompt_id)
        edit_dialog()

    # Preview dialog for this specific prompt
    elif st.session_state.get(f"show_preview_dialog_{prompt_id}") and not any_edit_open:
        @st.dialog(f"👀 Preview {prompt_id}", width="large")
        def preview_dialog():
            render_preview_dialog_content(service, prompt_id)
        preview_dialog()


def get_all_prompt_ids(service: PromptSectionService):
    """Get all prompt IDs for dialog conflict checking."""
    try:
        return service.repository.list_prompt_ids()
    except:
        return []


def clear_all_dialogs():
    """Clear all dialog states to prevent conflicts."""
    # Find and clear all dialog states
    keys_to_clear = []
    for key in list(st.session_state.keys()):
        if key.startswith("show_edit_dialog_") or key.startswith("show_preview_dialog_"):
            keys_to_clear.append(key)

    # Clear all dialog states
    for key in keys_to_clear:
        st.session_state[key] = False


def render_edit_dialog_content(service: PromptSectionService, prompt_id: str):
    """Render edit dialog content."""

    # Close button
    col1, col2, col3 = st.columns([1, 8, 1])
    with col1:
        if st.button("❌ Close"):
            clear_all_dialogs()
            st.rerun()

    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()

    # Load sections
    sections_result = service.get_sections(prompt_id)

    if not sections_result.success:
        st.error(f"Failed to load sections: {sections_result.error}")
        return

    sections = sections_result.sections

    # Editor tabs
    tab_edit, tab_reorder, tab_preview = st.tabs([
        "✏️ Edit Sections",
        "🔄 Reorder",
        "👀 Live Preview"
    ])

    with tab_edit:
        render_section_crud_dialog(service, prompt_id, sections)

    with tab_reorder:
        render_section_reorder_dialog(service, prompt_id, sections)

    with tab_preview:
        render_live_preview_dialog(service, prompt_id)


def render_preview_dialog_content(service: PromptSectionService, prompt_id: str):
    """Render preview dialog content."""

    # Close button
    if st.button("❌ Close"):
        clear_all_dialogs()
        st.rerun()

    # Render preview
    render_live_preview_dialog(service, prompt_id)


def render_section_crud_dialog(service: PromptSectionService, prompt_id: str, sections: List[PromptSection]):
    """Render section CRUD interface optimized for dialog."""

    st.markdown("### ➕ Add New Section")

    # Add new section form
    with st.form(f"add_section_dialog_{prompt_id}"):
        col1, col2 = st.columns([1, 2])

        with col1:
            new_title = st.text_input("Section Title", placeholder="Enter section title...")

        with col2:
            position_options = ["End"] + [f"After: {s.title}" for s in sections] + ["Beginning"]
            position = st.selectbox("Insert Position", position_options)

        new_content = st.text_area(
            "Content",
            height=150,
            placeholder="Enter section content...",
            help="Use markdown formatting if needed"
        )

        if st.form_submit_button("➕ Add Section", type="primary"):
            if new_title and new_content:
                try:
                    # Determine position index
                    if position == "Beginning":
                        pos_index = 0
                    elif position == "End":
                        pos_index = None
                    else:
                        # Find position after specific section
                        section_title = position.replace("After: ", "")
                        pos_index = next((i + 1 for i, s in enumerate(sections) if s.title == section_title), None)

                    result = service.create_section(prompt_id, new_title, new_content, pos_index)
                    if result.success:
                        st.success(f"✅ Section '{new_title}' created successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to create section: {result.error}")
                except Exception as e:
                    st.error(f"❌ Error creating section: {e}")
            else:
                st.error("❌ Please provide both title and content")

    # Edit existing sections
    if sections:
        st.markdown("### 📝 Current Sections")

        for i, section in enumerate(sections):
            with st.expander(f"📝 {section.title} ({i+1}/{len(sections)})", expanded=False):

                with st.form(f"edit_section_dialog_{prompt_id}_{section.id}"):
                    edited_title = st.text_input("Title", value=section.title)
                    edited_content = st.text_area("Content", value=section.content, height=200)

                    # Action buttons
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if st.form_submit_button("💾 Update", type="primary"):
                            try:
                                result = service.update_section(prompt_id, section.id, edited_title, edited_content)
                                if result.success:
                                    st.success("✅ Section updated!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Update failed: {result.error}")
                            except Exception as e:
                                st.error(f"❌ Error updating: {e}")

                    with col2:
                        if st.form_submit_button("📋 Duplicate"):
                            try:
                                result = service.duplicate_section(prompt_id, section.id)
                                if result.success:
                                    st.success("✅ Section duplicated!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Duplicate failed: {result.error}")
                            except Exception as e:
                                st.error(f"❌ Error duplicating: {e}")

                    with col3:
                        if i > 0 and st.form_submit_button("⬆️ Move Up"):
                            try:
                                # Use proper service method - move to position i-1
                                result = service.move_section(prompt_id, section.id, i - 1)
                                if result.success:
                                    st.success("✅ Section moved up!")
                                    time.sleep(0.3)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Move failed: {result.error}")
                            except Exception as e:
                                st.error(f"❌ Error moving up: {str(e)}")

                    with col4:
                        if i < len(sections) - 1 and st.form_submit_button("⬇️ Move Down"):
                            try:
                                # Use proper service method - move to position i+1
                                result = service.move_section(prompt_id, section.id, i + 1)
                                if result.success:
                                    st.success("✅ Section moved down!")
                                    time.sleep(0.3)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Move failed: {result.error}")
                            except Exception as e:
                                st.error(f"❌ Error moving down: {str(e)}")

                # Separate delete button for safety
                if st.button(f"🗑️ Delete Section", key=f"delete_dialog_{prompt_id}_{section.id}", type="secondary"):
                    if st.button(f"⚠️ Confirm Delete '{section.title}'?", key=f"confirm_delete_dialog_{prompt_id}_{section.id}"):
                        try:
                            result = service.delete_section(prompt_id, section.id)
                            if result.success:
                                st.success("✅ Section deleted!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ Delete failed: {result.error}")
                        except Exception as e:
                            st.error(f"❌ Error deleting: {e}")
    else:
        st.info("No sections found. Add your first section above!")


def render_section_reorder_dialog(service: PromptSectionService, prompt_id: str, sections: List[PromptSection]):
    """Render section reorder interface for dialog."""
    st.markdown("### 🔄 Reorder Sections")

    if not sections:
        st.info("No sections to reorder")
        return

    st.markdown("Current order:")

    for i, section in enumerate(sections):
        col1, col2, col3, col4 = st.columns([1, 4, 1, 1])

        with col1:
            st.markdown(f"**{i+1}.**")

        with col2:
            st.markdown(f"📝 {section.title}")
            st.caption(f"{len(section.content.split())} words")

        with col3:
            if i > 0:
                if st.button("⬆️", key=f"reorder_dialog_up_{prompt_id}_{section.id}_{i}", help=f"Move {section.title} up"):
                    try:
                        # Move section up by one position
                        result = service.move_section(prompt_id, section.id, i - 1)
                        if result.success:
                            st.success(f"✅ '{section.title}' moved up!")
                            time.sleep(0.3)
                            st.rerun()
                        else:
                            st.error(f"❌ Move failed: {result.error}")
                    except Exception as e:
                        st.error(f"❌ Error moving section: {str(e)}")

        with col4:
            if i < len(sections) - 1:
                if st.button("⬇️", key=f"reorder_dialog_down_{prompt_id}_{section.id}_{i}", help=f"Move {section.title} down"):
                    try:
                        # Move section down by one position
                        result = service.move_section(prompt_id, section.id, i + 1)
                        if result.success:
                            st.success(f"✅ '{section.title}' moved down!")
                            time.sleep(0.3)
                            st.rerun()
                        else:
                            st.error(f"❌ Move failed: {result.error}")
                    except Exception as e:
                        st.error(f"❌ Error moving section: {str(e)}")


def render_live_preview_dialog(service: PromptSectionService, prompt_id: str):
    """Render live preview using st.markdown for dialog."""
    st.markdown("### 👀 Live Preview")

    try:
        # Get template
        template_result = service.get_template(prompt_id)
        if not template_result.success:
            st.error(f"Failed to load template: {template_result.error}")
            return

        template = template_result.template

        # Format sections for preview
        preview_content = format_prompt_for_preview(template)

        if not preview_content.strip():
            st.warning("No content to preview")
            return

        st.info("💡 This shows how the prompt will appear when used by the AI agent")

        # Preview container with custom styling
        with st.container():
            st.markdown(preview_content)

        # Statistics
        st.markdown("### 📊 Preview Statistics")
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)

        with stats_col1:
            word_count = len(preview_content.split())
            st.metric("Word Count", word_count)

        with stats_col2:
            char_count = len(preview_content)
            st.metric("Characters", char_count)

        with stats_col3:
            section_count = len(template.sections)
            st.metric("Sections", section_count)

        with stats_col4:
            avg_words_per_section = word_count // section_count if section_count > 0 else 0
            st.metric("Avg Words/Section", avg_words_per_section)

    except Exception as e:
        st.error(f"Error generating preview: {e}")






def format_prompt_for_preview(template: PromptTemplate) -> str:
    """Format template sections for markdown preview."""
    if not template.sections:
        return "*No sections found*"

    formatted_parts = []

    for i, section in enumerate(template.sections, 1):
        # Add section number and title
        formatted_parts.append(f"## {i}. {section.title}")

        # Add section content with proper formatting
        if section.content.strip():
            # Convert newlines to HTML breaks for better formatting
            # content = section.content.replace('\n', '<br>')
            formatted_parts.append(section.content)
        else:
            formatted_parts.append("*[Empty section]*")

        # Add separator except for last section
        if i < len(template.sections):
            formatted_parts.append("---")

    return "\n\n".join(formatted_parts)


def show_prompt_stats(service: PromptSectionService, prompt_id: str):
    """Show detailed statistics for a prompt."""
    try:
        stats_result = service.get_statistics(prompt_id)

        if stats_result.success:
            stats = stats_result.statistics

            with st.popover("📊 Detailed Statistics", use_container_width=True):
                st.markdown(f"**Statistics for: {prompt_id}**")

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Total Sections", stats.get("section_count", 0))
                    st.metric("Total Words", stats.get("total_words", 0))
                    st.metric("Total Characters", stats.get("total_characters", 0))

                with col2:
                    empty_sections = stats.get("empty_sections", 0)
                    st.metric("Empty Sections", empty_sections)
                    avg_words = stats.get("average_words_per_section", 0)
                    st.metric("Avg Words/Section", f"{avg_words:.1f}")
                    longest_section = stats.get("longest_section_words", 0)
                    st.metric("Longest Section", f"{longest_section} words")

        else:
            st.error(f"Failed to load statistics: {stats_result.error}")

    except Exception as e:
        st.error(f"Error loading statistics: {e}")


def render_footer_actions(service: PromptSectionService, prompt_ids: List[str]):
    """Render footer with quick actions."""
    st.markdown("---")
    st.markdown("### 🛠️ Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 Refresh All", type="secondary"):
            st.success("All prompts refreshed!")
            time.sleep(0.5)
            st.rerun()

    with col2:
        if st.button("📊 Global Stats", type="secondary"):
            show_global_statistics(service, prompt_ids)

    with col3:
        if st.button("🧪 Test All", type="secondary"):
            st.info("Global testing functionality coming soon!")

    with col4:
        if st.button("⚙️ Settings", type="secondary"):
            st.info("Prompts settings coming soon!")


def show_global_statistics(service: PromptSectionService, prompt_ids: List[str]):
    """Show global statistics across all prompts."""
    try:
        with st.popover("📊 Global Statistics", use_container_width=True):
            st.markdown("**Overall Prompt Statistics**")

            total_sections = 0
            total_words = 0
            total_chars = 0
            total_empty = 0

            for prompt_id in prompt_ids:
                try:
                    stats_result = service.get_statistics(prompt_id)
                    if stats_result.success:
                        stats = stats_result.statistics
                        total_sections += stats.get("section_count", 0)
                        total_words += stats.get("total_words", 0)
                        total_chars += stats.get("total_characters", 0)
                        total_empty += stats.get("empty_sections", 0)
                except Exception:
                    continue

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Total Prompts", len(prompt_ids))
                st.metric("Total Sections", total_sections)
                st.metric("Total Words", total_words)

            with col2:
                st.metric("Total Characters", total_chars)
                st.metric("Empty Sections", total_empty)
                avg_sections = total_sections / len(prompt_ids) if prompt_ids else 0
                st.metric("Avg Sections/Prompt", f"{avg_sections:.1f}")

    except Exception as e:
        st.error(f"Error calculating global statistics: {e}")


# Backward compatibility alias
def prompts_management_page():
    """Alias for backward compatibility."""
    prompts_unified_page()


if __name__ == "__main__":
    # For standalone testing
    prompts_unified_page()