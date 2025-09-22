"""
Prompt editing page for the new unified prompt system.
Allows editing of system prompts and stage-specific prompts.
"""

import streamlit as st
import json
from pathlib import Path
from src.core.prompts import UnifiedPromptManager
from src.core.prompts import SystemPromptManager
from src.core.prompts import StagePromptManager
from src.core.session import load_stages
from config import Config


def prompts_management_page():
    """Display prompt management interface for unified prompt system."""
    st.title("📝 Edycja Promptów")

    # Initialize managers
    unified_manager = UnifiedPromptManager(Config.PROMPT_DIR)
    system_manager = SystemPromptManager(f"{Config.PROMPT_DIR}/system")
    stage_manager = StagePromptManager(f"{Config.PROMPT_DIR}/stages")

    # Create tabs for different prompt types
    tab1, tab2, tab3 = st.tabs(["🏠 System", "🎯 Etapy", "🔍 Podgląd"])

    with tab1:
        _display_system_prompts_editor(system_manager)

    with tab2:
        _display_stage_prompts_editor(stage_manager)

    with tab3:
        _display_prompt_preview(unified_manager)


def _display_system_prompts_editor(system_manager: SystemPromptManager):
    """Display system prompts editor."""
    st.subheader("🏠 Prompty Systemowe")
    st.info("Prompty systemowe definiują podstawową rolę i zasady dla agentów. Ustawiane raz na początku sesji.")

    # Agent type selection
    agent_type = st.selectbox(
        "Wybierz typ agenta:",
        ["therapist", "supervisor"],
        format_func=lambda x: "🩺 Terapeuta" if x == "therapist" else "👥 Supervisor"
    )

    # Load current system prompt
    current_prompt = system_manager.get_prompt(agent_type)

    if current_prompt:
        st.success(f"✅ Prompt systemowy dla {agent_type} załadowany")

        # Display current content in expandable section
        with st.expander("📖 Aktualny prompt systemowy", expanded=False):
            st.text(current_prompt)

        # Edit button
        if st.button(f"✏️ Edytuj prompt systemowy ({agent_type})", use_container_width=True):
            st.session_state[f"editing_system_{agent_type}"] = True
    else:
        st.warning(f"⚠️ Brak promptu systemowego dla {agent_type}")
        if st.button(f"➕ Utwórz prompt systemowy ({agent_type})", use_container_width=True):
            st.session_state[f"editing_system_{agent_type}"] = True

    # Editor interface
    if st.session_state.get(f"editing_system_{agent_type}", False):
        _show_system_prompt_editor(system_manager, agent_type)


def _show_system_prompt_editor(system_manager: SystemPromptManager, agent_type: str):
    """Show system prompt editor interface."""
    st.subheader(f"✏️ Edycja promptu systemowego: {agent_type}")

    # Load current data
    try:
        prompt_file = Path(f"{Config.PROMPT_DIR}/system/{agent_type}_base.json")
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # Default structure
            data = {
                "id": f"{agent_type}_system_base",
                "role": "",
                "core_principles": "",
                "general_guidelines": [],
                "created_at": "",
                "version": "1.0"
            }
    except Exception as e:
        st.error(f"Błąd ładowania danych: {e}")
        return

    # Form for editing
    with st.form(f"system_prompt_form_{agent_type}"):
        st.write("### Podstawowe informacje")

        role = st.text_area(
            "Rola agenta:",
            value=data.get("role", ""),
            height=100,
            help="Podstawowa definicja roli agenta"
        )

        core_principles = st.text_area(
            "Główne zasady:",
            value=data.get("core_principles", ""),
            height=150,
            help="Kluczowe zasady działania agenta"
        )

        # Guidelines as text (convert from list)
        guidelines_text = "\n".join(data.get("general_guidelines", []))
        guidelines = st.text_area(
            "Ogólne wytyczne (jedna na linię):",
            value=guidelines_text,
            height=200,
            help="Każda linia to osobna wytyczna"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Zapisz", use_container_width=True):
                # Update data
                data.update({
                    "role": role,
                    "core_principles": core_principles,
                    "general_guidelines": [line.strip() for line in guidelines.split('\n') if line.strip()],
                    "version": "1.0"
                })

                # Save to file
                try:
                    prompt_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(prompt_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                    st.success("✅ Prompt systemowy zapisany!")
                    st.session_state[f"editing_system_{agent_type}"] = False
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Błąd zapisu: {e}")

        with col2:
            if st.form_submit_button("❌ Anuluj", use_container_width=True):
                st.session_state[f"editing_system_{agent_type}"] = False
                st.rerun()


def _display_stage_prompts_editor(stage_manager: StagePromptManager):
    """Display stage prompts editor."""
    st.subheader("🎯 Prompty Etapowe")
    st.info("Prompty etapowe definiują cele, zasady i przykłady dla konkretnych etapów terapii.")

    # Load stages
    stages = load_stages()

    # Stage and agent selection
    col1, col2 = st.columns(2)
    with col1:
        selected_stage = st.selectbox(
            "Wybierz etap:",
            [stage["id"] for stage in stages],
            format_func=lambda x: next((f"{s['order']}. {s['name']}" for s in stages if s["id"] == x), x)
        )

    with col2:
        agent_type = st.selectbox(
            "Wybierz typ agenta:",
            ["therapist", "supervisor"],
            format_func=lambda x: "🩺 Terapeuta" if x == "therapist" else "👥 Supervisor",
            key="stage_agent_type"
        )

    # Check if prompt exists
    is_available = stage_manager.is_available(selected_stage, agent_type)

    if is_available:
        current_prompt = stage_manager.get_prompt(selected_stage, agent_type)
        st.success(f"✅ Prompt etapowy załadowany")

        # Display current content
        with st.expander("📖 Aktualny prompt etapowy", expanded=False):
            st.text(current_prompt)

        # Edit button
        if st.button(f"✏️ Edytuj prompt etapowy", use_container_width=True):
            st.session_state[f"editing_stage_{selected_stage}_{agent_type}"] = True
    else:
        st.warning(f"⚠️ Brak promptu etapowego dla {selected_stage} ({agent_type})")
        if st.button(f"➕ Utwórz prompt etapowy", use_container_width=True):
            st.session_state[f"editing_stage_{selected_stage}_{agent_type}"] = True

    # Editor interface
    if st.session_state.get(f"editing_stage_{selected_stage}_{agent_type}", False):
        _show_stage_prompt_editor(stage_manager, selected_stage, agent_type, stages)


def _show_stage_prompt_editor(stage_manager: StagePromptManager, stage_id: str, agent_type: str, stages: list):
    """Show stage prompt editor interface."""
    stage_info = next((s for s in stages if s["id"] == stage_id), {"name": stage_id})
    st.subheader(f"✏️ Edycja promptu: {stage_info['name']} ({agent_type})")

    # Load current data
    try:
        prompt_file = Path(f"{Config.PROMPT_DIR}/stages/{agent_type}/{stage_id}.json")
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # Default structure based on agent type
            if agent_type == "therapist":
                data = {
                    "id": f"{agent_type}_{stage_id}_stage",
                    "stage_goals": [],
                    "stage_specific_guidelines": [],
                    "suggested_questions": [],
                    "good_examples": [],
                    "avoid_examples": [],
                    "created_at": "",
                    "version": "1.0"
                }
            else:  # supervisor
                data = {
                    "id": f"{agent_type}_{stage_id}_stage",
                    "stage_name": stage_info.get('name', ''),
                    "stage_description": stage_info.get('description', ''),
                    "criteria": {},
                    "evaluation_rules": [],
                    "created_at": "",
                    "version": "1.0"
                }
    except Exception as e:
        st.error(f"Błąd ładowania danych: {e}")
        return

    # Form for editing
    with st.form(f"stage_prompt_form_{stage_id}_{agent_type}"):
        if agent_type == "therapist":
            _show_therapist_stage_form(data)
        else:
            _show_supervisor_stage_form(data)

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Zapisz", use_container_width=True):
                # Save to file
                try:
                    prompt_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(prompt_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                    st.success("✅ Prompt etapowy zapisany!")
                    st.session_state[f"editing_stage_{stage_id}_{agent_type}"] = False
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Błąd zapisu: {e}")

        with col2:
            if st.form_submit_button("❌ Anuluj", use_container_width=True):
                st.session_state[f"editing_stage_{stage_id}_{agent_type}"] = False
                st.rerun()


def _show_therapist_stage_form(data: dict):
    """Show form for editing therapist stage prompt."""
    st.write("### Cele etapu")
    goals_text = "\n".join(data.get("stage_goals", []))
    goals = st.text_area(
        "Cele etapu (jeden na linię):",
        value=goals_text,
        height=100,
        help="Główne cele do osiągnięcia w tym etapie"
    )
    data["stage_goals"] = [line.strip() for line in goals.split('\n') if line.strip()]

    st.write("### Wytyczne")
    guidelines_text = "\n".join(data.get("stage_specific_guidelines", []))
    guidelines = st.text_area(
        "Wytyczne specyficzne dla etapu (jedna na linię):",
        value=guidelines_text,
        height=120,
        help="Zasady specifyczne dla tego etapu"
    )
    data["stage_specific_guidelines"] = [line.strip() for line in guidelines.split('\n') if line.strip()]

    st.write("### Przykładowe pytania")
    questions_text = "\n".join(data.get("suggested_questions", []))
    questions = st.text_area(
        "Sugerowane pytania (jedno na linię):",
        value=questions_text,
        height=100,
        help="Pytania które terapeuta może zadać"
    )
    data["suggested_questions"] = [line.strip() for line in questions.split('\n') if line.strip()]

    st.write("### Przykłady")
    col1, col2 = st.columns(2)
    with col1:
        good_text = "\n".join(data.get("good_examples", []))
        good = st.text_area(
            "Dobre przykłady (jeden na linię):",
            value=good_text,
            height=100,
            help="Przykłady dobrych odpowiedzi"
        )
        data["good_examples"] = [line.strip() for line in good.split('\n') if line.strip()]

    with col2:
        avoid_text = "\n".join(data.get("avoid_examples", []))
        avoid = st.text_area(
            "Czego unikać (jeden na linię):",
            value=avoid_text,
            height=100,
            help="Przykłady złych podejść"
        )
        data["avoid_examples"] = [line.strip() for line in avoid.split('\n') if line.strip()]


def _show_supervisor_stage_form(data: dict):
    """Show form for editing supervisor stage prompt."""
    st.write("### Informacje o etapie")
    data["stage_name"] = st.text_input(
        "Nazwa etapu:",
        value=data.get("stage_name", ""),
        help="Czytelna nazwa etapu"
    )

    data["stage_description"] = st.text_area(
        "Opis etapu:",
        value=data.get("stage_description", ""),
        height=80,
        help="Krótki opis celu etapu"
    )

    st.write("### Zasady oceny")
    rules_text = "\n".join(data.get("evaluation_rules", []))
    rules = st.text_area(
        "Zasady oceny (jedna na linię):",
        value=rules_text,
        height=100,
        help="Ogólne zasady oceniania postępu w etapie"
    )
    data["evaluation_rules"] = [line.strip() for line in rules.split('\n') if line.strip()]

    st.write("### Kryteria (uproszczone)")
    st.info("💡 Dla pełnej edycji kryteriów użyj edytora JSON lub edytuj plik bezpośrednio")

    criteria_json = st.text_area(
        "Kryteria (JSON):",
        value=json.dumps(data.get("criteria", {}), ensure_ascii=False, indent=2),
        height=200,
        help="Kryteria w formacie JSON"
    )

    try:
        data["criteria"] = json.loads(criteria_json)
    except json.JSONDecodeError:
        st.error("❌ Nieprawidłowy format JSON w kryteriach")


def _display_prompt_preview(unified_manager: UnifiedPromptManager):
    """Display prompt preview interface."""
    st.subheader("🔍 Podgląd Pełnych Promptów")
    st.info("Zobacz jak wyglądają połączone prompty systemowe + etapowe")

    # Load stages
    stages = load_stages()

    # Stage and agent selection
    col1, col2 = st.columns(2)
    with col1:
        selected_stage = st.selectbox(
            "Wybierz etap:",
            [stage["id"] for stage in stages],
            format_func=lambda x: next((f"{s['order']}. {s['name']}" for s in stages if s["id"] == x), x),
            key="preview_stage"
        )

    with col2:
        agent_type = st.selectbox(
            "Wybierz typ agenta:",
            ["therapist", "supervisor"],
            format_func=lambda x: "🩺 Terapeuta" if x == "therapist" else "👥 Supervisor",
            key="preview_agent_type"
        )

    # Get and display full prompt
    if st.button("🔍 Pokaż pełny prompt", use_container_width=True):
        full_prompt = unified_manager.get_full_prompt(selected_stage, agent_type)

        if full_prompt:
            st.success("✅ Prompt pomyślnie wygenerowany")

            # Display components separately
            system_prompt = unified_manager.get_system_prompt(agent_type)
            stage_prompt = unified_manager.get_stage_prompt(selected_stage, agent_type)

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
            st.info(f"📊 **Statystyki:** {len(full_prompt)} znaków, {len(full_prompt.split())} słów")
        else:
            st.error("❌ Nie można wygenerować promptu - sprawdź czy istnieją komponenty systemowe i etapowe")