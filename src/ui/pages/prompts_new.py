"""
LEGACY: Old Prompt editing page - kept for backward compatibility.
New unified prompts page is available at prompts_unified.py

This version uses complex multi-mode interface with tabs (Browse & Select, Section Editor, Legacy Editor).
The new unified version provides better UX with modal editing.
"""

import streamlit as st
from typing import Dict, Any, List, Optional

from ..components.prompt_section_editor import PromptSectionEditor
from ...core.prompts.services.prompt_section_service import PromptSectionService
from ..services.prompt_ui_service import PromptUIService


def prompts_management_page():
    """Main prompt management page with new CRUD functionality."""
    st.title("📝 Advanced Prompt Editor")
    st.markdown("Complete prompt management with section-level CRUD operations")

    # Initialize services
    section_service = PromptSectionService("config")
    ui_service = PromptUIService()  # Keep for compatibility

    # Page mode selection
    mode = st.selectbox(
        "Editor Mode",
        ["📋 Browse & Select", "✏️ Section Editor", "🔧 Legacy Editor"],
        help="Choose editing mode"
    )

    if mode == "📋 Browse & Select":
        _display_prompt_browser(section_service)
    elif mode == "✏️ Section Editor":
        _display_section_editor(section_service)
    elif mode == "🔧 Legacy Editor":
        _display_legacy_editor(ui_service)


def _display_prompt_browser(service: PromptSectionService) -> None:
    """Display prompt browser and selection interface."""
    st.subheader("📋 Browse Prompts")

    # Get available prompts
    try:
        prompt_ids = service.repository.list_prompt_ids()

        if not prompt_ids:
            st.warning("No prompts found in configuration")
            return

        st.success(f"Found {len(prompt_ids)} prompts")

        # Group by type
        system_prompts = [pid for pid in prompt_ids if "system" in pid]
        stage_prompts = [pid for pid in prompt_ids if "stage" in pid or "supervisor" in pid]

        # Display in columns
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🏠 System Prompts")

            for prompt_id in system_prompts:
                if st.button(f"📝 {prompt_id}", key=f"edit_system_{prompt_id}", use_container_width=True):
                    st.session_state.selected_prompt_id = prompt_id
                    st.session_state.editor_mode = "Section Editor"
                    st.rerun()

        with col2:
            st.markdown("### 🎯 Stage Prompts")

            for prompt_id in stage_prompts:
                if st.button(f"📝 {prompt_id}", key=f"edit_stage_{prompt_id}", use_container_width=True):
                    st.session_state.selected_prompt_id = prompt_id
                    st.session_state.editor_mode = "Section Editor"
                    st.rerun()

        # Quick stats
        st.markdown("---")
        st.markdown("### 📊 Quick Statistics")

        selected_prompt = st.selectbox(
            "View stats for:",
            ["Select prompt..."] + prompt_ids,
            key="stats_prompt_select"
        )

        if selected_prompt and selected_prompt != "Select prompt...":
            _display_quick_stats(service, selected_prompt)

    except Exception as e:
        st.error(f"Failed to load prompts: {e}")


def _display_section_editor(service: PromptSectionService) -> None:
    """Display the new section-based editor."""
    st.subheader("✏️ Section Editor")

    # Get selected prompt or let user select
    selected_prompt = st.session_state.get("selected_prompt_id")

    if not selected_prompt:
        # Prompt selection
        try:
            prompt_ids = service.repository.list_prompt_ids()

            if not prompt_ids:
                st.warning("No prompts available for editing")
                return

            selected_prompt = st.selectbox(
                "Select prompt to edit:",
                prompt_ids,
                key="section_editor_prompt_select"
            )

        except Exception as e:
            st.error(f"Failed to load prompts: {e}")
            return

    if selected_prompt:
        # Get prompt info
        try:
            template_result = service.get_template(selected_prompt)

            if template_result.success and template_result.template:
                template = template_result.template

                # Show prompt info
                info_col1, info_col2, info_col3 = st.columns(3)

                with info_col1:
                    st.info(f"**Agent:** {template.agent_type}")

                with info_col2:
                    st.info(f"**Type:** {template.prompt_type}")

                with info_col3:
                    st.info(f"**Sections:** {len(template.sections)}")

                # Navigation
                nav_col1, nav_col2 = st.columns([1, 3])

                with nav_col1:
                    if st.button("← Back to Browser"):
                        if "selected_prompt_id" in st.session_state:
                            del st.session_state.selected_prompt_id
                        st.rerun()

                st.markdown("---")

                # Main section editor
                editor = PromptSectionEditor("config")
                editor.render_full_editor(selected_prompt, f"editor_{selected_prompt}")

            else:
                st.error(f"Failed to load template: {template_result.error}")

        except Exception as e:
            st.error(f"Error loading template: {e}")


def _display_legacy_editor(ui_service: PromptUIService) -> None:
    """Display legacy editor for backward compatibility."""
    st.subheader("🔧 Legacy Editor")
    st.info("This is the original editor. New features are available in Section Editor mode.")

    # Create tabs for different prompt types (original layout)
    tab1, tab2, tab3 = st.tabs(["🏠 System", "🎯 Etapy", "🔍 Podgląd"])

    with tab1:
        _display_legacy_system_prompts(ui_service)

    with tab2:
        _display_legacy_stage_prompts(ui_service)

    with tab3:
        _display_legacy_preview(ui_service)


def _display_legacy_system_prompts(ui_service: PromptUIService) -> None:
    """Display legacy system prompts editor."""
    st.markdown("### 🏠 System Prompts (Legacy)")

    # Create two columns for therapist and supervisor
    col_therapist, col_supervisor = st.columns(2)

    # THERAPIST COLUMN
    with col_therapist:
        st.markdown("#### 🩺 TERAPEUTA")

        # Load therapist data
        therapist_data = ui_service.load_system_prompt_for_editing("therapist")

        if therapist_data:
            # Display simple form for therapist
            with st.form("therapist_legacy_form"):
                st.markdown("**Legacy Editor for: THERAPIST**")

                # Show sections count
                sections_count = len(therapist_data.get("configuration", {}).get("sections", {}))
                st.info(f"📋 {sections_count} sections detected")

                # Recommendation to use new editor
                st.warning("⚡ **Recommendation:** Use Section Editor mode for advanced editing features")

                # Simple JSON editor
                json_data = st.text_area(
                    "JSON Data (Advanced)",
                    value=str(therapist_data)[:500] + "...",
                    height=200,
                    disabled=True,
                    help="Use Section Editor for proper editing"
                )

                # Form buttons
                if st.form_submit_button("Switch to Section Editor"):
                    # Find therapist system prompt ID
                    try:
                        service = PromptSectionService("config")
                        prompt_ids = service.repository.list_prompt_ids()
                        therapist_prompts = [pid for pid in prompt_ids if "therapist" in pid and "system" in pid]

                        if therapist_prompts:
                            st.session_state.selected_prompt_id = therapist_prompts[0]
                            st.session_state.editor_mode = "Section Editor"
                            st.rerun()
                        else:
                            st.error("No therapist system prompt found")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # SUPERVISOR COLUMN
    with col_supervisor:
        st.markdown("#### 👥 SUPERVISOR")

        # Load supervisor data
        supervisor_data = ui_service.load_system_prompt_for_editing("supervisor")

        if supervisor_data:
            with st.form("supervisor_legacy_form"):
                st.markdown("**Legacy Editor for: SUPERVISOR**")

                # Show sections count
                sections_count = len(supervisor_data.get("configuration", {}).get("sections", {}))
                st.info(f"📋 {sections_count} sections detected")

                # Recommendation
                st.warning("⚡ **Recommendation:** Use Section Editor mode for advanced editing features")

                # Simple JSON editor
                json_data = st.text_area(
                    "JSON Data (Advanced)",
                    value=str(supervisor_data)[:500] + "...",
                    height=200,
                    disabled=True,
                    help="Use Section Editor for proper editing"
                )

                if st.form_submit_button("Switch to Section Editor"):
                    try:
                        service = PromptSectionService("config")
                        prompt_ids = service.repository.list_prompt_ids()
                        supervisor_prompts = [pid for pid in prompt_ids if "supervisor" in pid and "system" in pid]

                        if supervisor_prompts:
                            st.session_state.selected_prompt_id = supervisor_prompts[0]
                            st.session_state.editor_mode = "Section Editor"
                            st.rerun()
                        else:
                            st.error("No supervisor system prompt found")
                    except Exception as e:
                        st.error(f"Error: {e}")


def _display_legacy_stage_prompts(ui_service: PromptUIService) -> None:
    """Display legacy stage prompts editor."""
    st.markdown("### 🎯 Stage Prompts (Legacy)")
    st.info("Stage prompts editing available in Section Editor mode with full CRUD functionality")

    if st.button("Switch to Section Editor for Stage Prompts"):
        st.session_state.editor_mode = "Section Editor"
        st.rerun()


def _display_legacy_preview(ui_service: PromptUIService) -> None:
    """Display legacy preview."""
    st.markdown("### 🔍 Preview (Legacy)")
    st.info("Enhanced preview with statistics available in Section Editor mode")

    if st.button("Switch to Section Editor for Advanced Preview"):
        st.session_state.editor_mode = "Section Editor"
        st.rerun()


def _display_quick_stats(service: PromptSectionService, prompt_id: str) -> None:
    """Display quick statistics for a prompt."""
    try:
        stats_result = service.get_statistics(prompt_id)

        if stats_result.success:
            stats = stats_result.statistics

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Sections", stats.get("section_count", 0))

            with col2:
                st.metric("Words", stats.get("total_words", 0))

            with col3:
                st.metric("Characters", stats.get("total_characters", 0))

            with col4:
                empty_count = stats.get("empty_sections", 0)
                st.metric("Empty Sections", empty_count, delta=None if empty_count == 0 else "⚠️")

        else:
            st.error(f"Failed to load statistics: {stats_result.error}")

    except Exception as e:
        st.error(f"Error loading statistics: {e}")


def prompts_page():
    """Alias for backward compatibility."""
    prompts_management_page()


# Quick demo function for testing
def demo_section_editor():
    """Demo function to test section editor independently."""
    st.title("🧪 Section Editor Demo")

    service = PromptSectionService("config")

    try:
        prompt_ids = service.repository.list_prompt_ids()

        if prompt_ids:
            selected = st.selectbox("Select prompt for demo:", prompt_ids)

            if selected:
                editor = PromptSectionEditor("config")
                editor.render_full_editor(selected, "demo_editor")
        else:
            st.warning("No prompts found for demo")

    except Exception as e:
        st.error(f"Demo error: {e}")


if __name__ == "__main__":
    # For standalone testing
    demo_section_editor()