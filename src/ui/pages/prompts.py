"""
Prompt editing page - Clean UI using service facade pattern.
All business logic delegated to PromptUIService facade.
"""

import streamlit as st
import json
from ..services.prompt_ui_service import PromptUIService


def prompts_management_page():
    """Display prompt management interfaces using service facade."""
    st.title("📝 Edycja Promptów")

    # Initialize UI service facade
    ui_service = PromptUIService()

    # Create tabs for different prompt types
    tab1, tab2, tab3 = st.tabs(["🏠 System", "🎯 Etapy", "🔍 Podgląd"])

    with tab1:
        _display_system_prompts_editor(ui_service)

    with tab2:
        _display_stage_prompts_editor(ui_service)

    with tab3:
        _display_prompt_preview(ui_service)


def _display_system_prompts_editor(ui_service: PromptUIService):
    """Display system prompts editor in 2 columns - therapist and supervisor side by side."""
    st.subheader("🏠 Zaawansowany Edytor Promptów Systemowych")

    # Create two columns for therapist and supervisor
    col_therapist, col_supervisor = st.columns(2)

    # THERAPIST COLUMN
    with col_therapist:
        st.markdown("### 🩺 TERAPEUTA")

        # Load therapist data
        therapist_data = ui_service.load_system_prompt_for_editing("therapist")

        # Display editor form for therapist
        with st.form("therapist_system_form"):
            st.markdown("🛠️ **Edytor dla: THERAPIST**")

            # Render dynamic sections for therapist
            updated_therapist_data = ui_service.render_dynamic_sections_form(therapist_data, "system_therapist")

            # Form buttons for therapist
            tcol1, tcol2, tcol3 = st.columns([1, 1, 1])

            with tcol1:
                save_therapist = st.form_submit_button("💾 Zapisz", use_container_width=True)

            with tcol2:
                preview_therapist = st.form_submit_button("👀 JSON", use_container_width=True)

            with tcol3:
                generate_therapist = st.form_submit_button("🚀 Prompt", use_container_width=True)

        # Handle therapist form submissions
        if save_therapist:
            ui_service.save_system_prompt_from_ui("therapist", updated_therapist_data)

        if preview_therapist:
            with st.expander("JSON - Terapeuta", expanded=True):
                st.json(updated_therapist_data)

        if generate_therapist:
            generated_prompt = ui_service.generate_prompt_for_preview(updated_therapist_data, "system")
            with st.expander("Prompt - Terapeuta", expanded=True):
                st.code(generated_prompt, language="text")
                ui_service.show_prompt_statistics(generated_prompt)

    # SUPERVISOR COLUMN
    with col_supervisor:
        st.markdown("### 👥 SUPERVISOR")

        # Load supervisor data
        supervisor_data = ui_service.load_system_prompt_for_editing("supervisor")

        # Display editor form for supervisor
        with st.form("supervisor_system_form"):
            st.markdown("🛠️ **Edytor dla: SUPERVISOR**")

            # Render dynamic sections for supervisor
            updated_supervisor_data = ui_service.render_dynamic_sections_form(supervisor_data, "system_supervisor")

            # Form buttons for supervisor
            scol1, scol2, scol3 = st.columns([1, 1, 1])

            with scol1:
                save_supervisor = st.form_submit_button("💾 Zapisz", use_container_width=True)

            with scol2:
                preview_supervisor = st.form_submit_button("👀 JSON", use_container_width=True)

            with scol3:
                generate_supervisor = st.form_submit_button("🚀 Prompt", use_container_width=True)

        # Handle supervisor form submissions
        if save_supervisor:
            ui_service.save_system_prompt_from_ui("supervisor", updated_supervisor_data)

        if preview_supervisor:
            with st.expander("JSON - Supervisor", expanded=True):
                st.json(updated_supervisor_data)

        if generate_supervisor:
            generated_prompt = ui_service.generate_prompt_for_preview(updated_supervisor_data, "system")
            with st.expander("Prompt - Supervisor", expanded=True):
                st.code(generated_prompt, language="text")
                ui_service.show_prompt_statistics(generated_prompt)


def _display_stage_prompts_editor(ui_service: PromptUIService):
    """Display stage prompts editor in 2 columns - therapist and supervisor side by side."""
    st.subheader("🎯 Zaawansowany Edytor Promptów Etapowych")

    # Load stages through service
    stages = ui_service.get_available_stages_for_ui()

    if not stages:
        st.error("❌ Nie można załadować listy etapów")
        return

    # Create two columns for therapist and supervisor
    col_therapist, col_supervisor = st.columns(2)

    # THERAPIST COLUMN
    with col_therapist:
        st.markdown("### 🩺 TERAPEUTA")

        # Loop through all stages for therapist
        for stage in stages:
            stage_id = stage["id"]
            stage_name = stage.get("display_name", stage_id)

            # Check availability for status display
            is_available, status_message = ui_service.check_stage_prompt_availability(stage_id, "therapist")
            status_emoji = "✅" if is_available else "ℹ️"

            # Each stage in its own expander
            with st.expander(f"{status_emoji} **Etap {stage.get('order', '?')}: {stage.get('name', stage_id)}**", expanded=False):
                # Show status
                if is_available:
                    st.success(f"✅ {status_message}")
                else:
                    st.info(f"ℹ️ {status_message}")

                # Load data through service
                prompt_data = ui_service.load_stage_prompt_for_editing(stage_id, "therapist")

                # Display editor form for this stage
                with st.form(f"therapist_stage_{stage_id}_form"):
                    st.markdown(f"🛠️ **Edytor - Etap {stage_id} (THERAPIST)**")

                    # Render dynamic sections
                    updated_data = ui_service.render_dynamic_sections_form(prompt_data, f"stage_therapist_{stage_id}")

                    # Form buttons
                    tcol1, tcol2, tcol3 = st.columns([1, 1, 1])

                    with tcol1:
                        save_therapist = st.form_submit_button("💾 Zapisz", use_container_width=True)

                    with tcol2:
                        preview_therapist = st.form_submit_button("👀 JSON", use_container_width=True)

                    with tcol3:
                        generate_therapist = st.form_submit_button("🚀 Prompt", use_container_width=True)

                # Handle form submissions
                if save_therapist:
                    ui_service.save_stage_prompt_from_ui(stage_id, "therapist", updated_data)

                if preview_therapist:
                    with st.expander(f"JSON - Terapeuta Etap {stage_id}", expanded=True):
                        st.json(updated_data)

                if generate_therapist:
                    generated_prompt = ui_service.generate_prompt_for_preview(updated_data, "stage")
                    with st.expander(f"Prompt - Terapeuta Etap {stage_id}", expanded=True):
                        st.code(generated_prompt, language="text")
                        ui_service.show_prompt_statistics(generated_prompt)

    # SUPERVISOR COLUMN
    with col_supervisor:
        st.markdown("### 👥 SUPERVISOR")

        # Loop through all stages for supervisor
        for stage in stages:
            stage_id = stage["id"]
            stage_name = stage.get("display_name", stage_id)

            # Check availability for status display
            is_available, status_message = ui_service.check_stage_prompt_availability(stage_id, "supervisor")
            status_emoji = "✅" if is_available else "ℹ️"

            # Each stage in its own expander
            with st.expander(f"{status_emoji} **Etap {stage.get('order', '?')}: {stage.get('name', stage_id)}**", expanded=False):
                # Show status
                if is_available:
                    st.success(f"✅ {status_message}")
                else:
                    st.info(f"ℹ️ {status_message}")

                # Load data through service
                prompt_data = ui_service.load_stage_prompt_for_editing(stage_id, "supervisor")

                # Display editor form for this stage
                with st.form(f"supervisor_stage_{stage_id}_form"):
                    st.markdown(f"🛠️ **Edytor - Etap {stage_id} (SUPERVISOR)**")

                    # Render dynamic sections
                    updated_data = ui_service.render_dynamic_sections_form(prompt_data, f"stage_supervisor_{stage_id}")

                    # Form buttons
                    scol1, scol2, scol3 = st.columns([1, 1, 1])

                    with scol1:
                        save_supervisor = st.form_submit_button("💾 Zapisz", use_container_width=True)

                    with scol2:
                        preview_supervisor = st.form_submit_button("👀 JSON", use_container_width=True)

                    with scol3:
                        generate_supervisor = st.form_submit_button("🚀 Prompt", use_container_width=True)

                # Handle form submissions
                if save_supervisor:
                    ui_service.save_stage_prompt_from_ui(stage_id, "supervisor", updated_data)

                if preview_supervisor:
                    with st.expander(f"JSON - Supervisor Etap {stage_id}", expanded=True):
                        st.json(updated_data)

                if generate_supervisor:
                    generated_prompt = ui_service.generate_prompt_for_preview(updated_data, "stage")
                    with st.expander(f"Prompt - Supervisor Etap {stage_id}", expanded=True):
                        st.code(generated_prompt, language="text")
                        ui_service.show_prompt_statistics(generated_prompt)


def _display_prompt_preview(ui_service: PromptUIService):
    """Display prompt preview using UI service facade."""
    st.subheader("🔍 Podgląd Pełnych Promptów")
    st.info("Zobacz jak wyglądają połączone prompty systemowe + etapowe")

    # Load stages through service
    stages = ui_service.get_available_stages_for_ui()

    if not stages:
        st.error("❌ Nie można załadować listy etapów")
        return

    # Stage and agent selection
    col1, col2 = st.columns(2)
    with col1:
        selected_stage = st.selectbox(
            "Wybierz etap:",
            [stage["id"] for stage in stages],
            format_func=lambda x: next((stage["display_name"] for stage in stages if stage["id"] == x), x),
            key="preview_stage"
        )

    with col2:
        agent_type = st.selectbox(
            "Wybierz typ agenta:",
            ["therapist", "supervisor"],
            format_func=lambda x: "🩺 Terapeuta" if x == "therapist" else "👥 Supervisor",
            key="preview_agent_type"
        )

    # Generate preview
    if st.button("🔍 Pokaż pełny prompt", use_container_width=True):
        try:
            # Load both system and stage prompts
            system_data = ui_service.load_system_prompt_for_editing(agent_type)
            stage_data = ui_service.load_stage_prompt_for_editing(selected_stage, agent_type)

            # Generate individual prompts
            system_prompt = ui_service.generate_prompt_for_preview(system_data, "system")
            stage_prompt = ui_service.generate_prompt_for_preview(stage_data, "stage")

            # Combine prompts
            full_prompt = f"{system_prompt}\n\n{'-' * 50}\n\n{stage_prompt}"

            st.success("✅ Prompt pomyślnie wygenerowany")

            # Display components separately
            col1, col2 = st.columns(2)
            with col1:
                with st.expander("🏠 Prompt systemowy", expanded=False):
                    st.text(system_prompt if system_prompt else "Brak promptu systemowego")

            with col2:
                with st.expander("🎯 Prompt etapowy", expanded=False):
                    st.text(stage_prompt if stage_prompt else "Brak promptu etapowego")

            # Display full combined prompt
            with st.expander("🔗 Pełny połączony prompt", expanded=True):
                st.text(full_prompt)

            # Show statistics
            ui_service.show_prompt_statistics(full_prompt)

        except Exception as e:
            st.error(f"❌ Błąd generowania podglądu: {e}")