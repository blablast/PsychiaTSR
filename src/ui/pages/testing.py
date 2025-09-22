"""Testing page for automated conversation sequences"""

import streamlit as st
import time
import json
from datetime import datetime
from pathlib import Path
from src.core.workflow import send_supervisor_request, initialize_agents
from src.core.session import create_new_session, get_configured_models
from src.ui.technical_log_display import add_technical_log, display_technical_log


def load_test_scenarios():
    """Load test scenarios from JSON file"""
    test_file = Path("config/json/tests/test_scenarios.json")
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("test_scenarios", [])
    except Exception as e:
        st.error(f"Błąd ładowania testów: {str(e)}")
        return []


def save_test_result(test_id, test_name, responses, results, models_used):
    """Save test results to data/tests directory"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_id}_{timestamp}.json"

    test_result = {
        "test_id": test_id,
        "test_name": test_name,
        "timestamp": datetime.now().isoformat(),
        "models_used": models_used,
        "input_responses": responses,
        "results": results
    }

    result_file = Path("data/tests") / filename
    try:
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        return str(result_file)
    except Exception as e:
        st.error(f"Błąd zapisywania wyników testu: {str(e)}")
        return None


def testing_page():
    """Testing page with automated conversation sequences"""
    st.title("🧪 Testowanie Automatyczne")
    
    st.info("Ta strona pozwala na automatyczne testowanie sekwencji odpowiedzi użytkownika")
    
    # Test configuration
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Wybór testu")

        # Load available test scenarios
        test_scenarios = load_test_scenarios()

        if test_scenarios:
            # Create options for selectbox
            test_options = [("custom", "📝 Własny test")]
            for scenario in test_scenarios:
                tags_str = " | ".join(scenario.get("tags", []))
                option_label = f"🧪 {scenario['name']} ({tags_str})"
                test_options.append((scenario["id"], option_label))

            selected_test = st.selectbox(
                "Wybierz test do wykonania:",
                options=[opt[0] for opt in test_options],
                format_func=lambda x: next(opt[1] for opt in test_options if opt[0] == x),
                key="selected_test"
            )

            # Load responses based on selection
            if selected_test == "custom":
                st.subheader("Własna sekwencja odpowiedzi")
                test_responses = st.text_area(
                    "Wpisz odpowiedzi użytkownika (każda w nowej linii):",
                    height=200,
                    placeholder="Ciężko mi\nNie wiem co robić\nChcę się lepiej czuć\nMożemy spróbować\nTo może działać",
                    key="test_responses"
                )
                responses_list = [r.strip() for r in test_responses.split('\n') if r.strip()]
                test_name = "Własny test"
            else:
                # Load selected test scenario
                scenario = next((s for s in test_scenarios if s["id"] == selected_test), None)
                if scenario:
                    test_name = scenario["name"]
                    test_description = scenario["description"]
                    responses_list = scenario["responses"]

                    st.info(f"**{test_name}**")
                    st.write(test_description)

                    # Show tags
                    if scenario.get("tags"):
                        tag_badges = " ".join([f"`{tag}`" for tag in scenario["tags"]])
                        st.write(f"**Tagi:** {tag_badges}")
        else:
            st.warning("Nie można załadować testów. Używając trybu własnego.")
            test_responses = st.text_area(
                "Wpisz odpowiedzi użytkownika (każda w nowej linii):",
                height=200,
                key="test_responses"
            )
            responses_list = [r.strip() for r in test_responses.split('\n') if r.strip()]
            test_name = "Własny test"
            selected_test = "custom"

        if responses_list:
            st.success(f"✅ Gotowe {len(responses_list)} odpowiedzi do przetestowania")

            # Preview responses
            with st.expander("👀 Podgląd odpowiedzi"):
                for i, response in enumerate(responses_list, 1):
                    st.write(f"{i}. {response}")

    with col2:
        st.subheader("Ustawienia testu")

        # Model selection for testing
        st.write("**🤖 Modele do testowania**")

        # Get configured models
        from config import Config
        try:
            configured_models = get_configured_models()
            test_therapist_model = configured_models['therapist_model']
            test_supervisor_model = configured_models['supervisor_model']
        except:
            test_therapist_model = Config.DEFAULT_THERAPIST_MODEL
            test_supervisor_model = Config.DEFAULT_SUPERVISOR_MODEL

        # Display current configured models
        st.info(f"🤖 **Skonfigurowane modele:**\n- Terapeuta: {test_therapist_model}\n- Nadzorca: {test_supervisor_model}")

        # Note: Model selection removed since we now use configured models from config.json

        st.divider()


        st.divider()

        # Delay between responses
        delay = st.slider(
            "Opóźnienie między odpowiedziami (sekundy):",
            min_value=0.5,
            max_value=5.0,
            value=2.0,
            step=0.5,
            key="test_delay"
        )

        # Option to create new session
        create_session = st.checkbox(
            "Utwórz nową sesję przed testem",
            value=True,
            key="create_test_session"
        )

        # Clear logs option
        clear_logs = st.checkbox(
            "Wyczyść logi przed testem",
            value=True,
            key="clear_test_logs"
        )

        # Clear conversation history option
        clear_history = st.checkbox(
            "Wyczyść historię konwersacji",
            value=True,
            key="clear_conversation_history",
            help="Wyłącz tylko dla testów kontynuacji rozmowy"
        )
    
    # Test execution
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Uruchom test", type="primary", disabled=not responses_list):
            # Store test parameters in session state and trigger test
            st.session_state.test_to_run = {
                "test_id": selected_test,
                "test_name": test_name,
                "responses": responses_list,
                "delay": delay,
                "create_session": create_session,
                "clear_logs": clear_logs,
                "clear_history": clear_history,
                "therapist_model": test_therapist_model,
                "supervisor_model": test_supervisor_model,
            }
            st.rerun()
    
    with col2:
        if st.button("⏹️ Zatrzymaj test"):
            if "test_running" in st.session_state:
                st.session_state.test_running = False
                st.warning("Test zatrzymany")
    
    with col3:
        if st.button("🧹 Wyczyść logi"):
            st.session_state.technical_log = []
            st.success("Logi wyczyszczone")

    # Single column for all test execution content below buttons
    st.markdown("---")

    # Execute test in main column if test was triggered
    if "test_to_run" in st.session_state and not st.session_state.get("test_running", False):
        test_params = st.session_state.test_to_run
        del st.session_state.test_to_run  # Clear the trigger
        run_automated_test(test_params)

    # Test status
    if "test_running" in st.session_state and st.session_state.test_running:
        progress = st.session_state.get("test_progress", 0)
        total = st.session_state.get("test_total", 1)
        st.progress(progress / total, text=f"Wykonywanie testu: {progress}/{total}")

    # Export test results
    st.markdown("---")
    st.subheader("📊 Eksport wyników testu")
    
    if st.session_state.technical_log:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Eksportuj logi do JSON"):
                export_test_logs()
        
        with col2:
            if st.button("📋 Skopiuj logi"):
                copy_logs_to_clipboard()
        
        # Show test summary
        show_test_summary()


def run_automated_test(test_params):
    """Run automated test with given parameters"""

    # Extract parameters
    test_id = test_params["test_id"]
    test_name = test_params["test_name"]
    responses_list = test_params["responses"]
    delay = test_params["delay"]
    create_session = test_params["create_session"]
    clear_logs = test_params["clear_logs"]
    clear_history = test_params["clear_history"]
    therapist_model = test_params["therapist_model"]
    supervisor_model = test_params["supervisor_model"]

    # Initialize test state
    st.session_state.test_running = True
    st.session_state.test_progress = 0
    st.session_state.test_total = len(responses_list)

    # Store models info for logging
    models_used = {
        "therapist": therapist_model,
        "supervisor": supervisor_model,
    }
    
    # Clear logs if requested
    if clear_logs:
        st.session_state.technical_log = []
        add_technical_log("info", "🧪 Test rozpoczęty - logi wyczyszczone")
    
    # Clear conversation history if requested (default for clean tests)
    if clear_history:
        st.session_state.messages = []
        from src.core.stages import StageManager
        from config import Config
        stage_manager = StageManager(Config.STAGES_DIR)
        first_stage = stage_manager.get_first_stage()
        st.session_state.current_stage = first_stage.stage_id if first_stage else "opening"
        add_technical_log("info", "🧹 Historia konwersacji wyczyszczona - test zaczyna od czystego stanu")
    
    # Initialize agents if not already done
    if not st.session_state.therapist_agent or not st.session_state.supervisor_agent:
        with st.spinner("Inicjalizacja agentów..."):
            if not initialize_agents():
                st.error("Nie można zainicjalizować agentów. Test anulowany.")
                st.session_state.test_running = False
                return
            add_technical_log("info", "🤖 Agenci zainicjalizowani dla testu")
    
    # Create new session if requested
    if create_session:
        create_new_session()
        add_technical_log("info", f"🆕 Nowa sesja testowa: {st.session_state.session_id}")
    
    # Log test start with models info
    add_technical_log("info", f"🧪 Test '{test_name}' rozpoczęty - {len(responses_list)} odpowiedzi")
    add_technical_log("info", f"🤖 Modele: THR={therapist_model}, SUP={supervisor_model}")
    
    # Show progress
    progress_container = st.empty()
    status_container = st.empty()

    # Create live log container
    st.markdown("### 🔴 Live Logs")
    log_container = st.container()

    # Execute responses
    for i, response in enumerate(responses_list):
        if not st.session_state.get("test_running", False):
            break
        
        st.session_state.test_progress = i + 1
        
        # Update progress
        progress_container.progress(
            (i + 1) / len(responses_list), 
            text=f"Przetwarzanie odpowiedzi {i + 1}/{len(responses_list)}: {response[:50]}..."
        )
        
        status_container.info(f"Wysyłanie: {response}")
        
        # Log test step
        add_technical_log("info", f"🧪 Test krok {i+1}: {response}")
        
        # Send response
        try:
            send_supervisor_request(response)

            # Update live logs after each step
            with log_container:
                display_technical_log()

            time.sleep(delay)
        except Exception as e:
            add_technical_log("error", f"🧪 Błąd testu w kroku {i+1}: {str(e)}")
            st.error(f"Błąd w kroku {i+1}: {str(e)}")
            break
    
    # Test completed
    st.session_state.test_running = False
    progress_container.success("✅ Test zakończony!")
    status_container.success(f"Przetestowano {st.session_state.test_progress} odpowiedzi")
    
    add_technical_log("info", f"🧪 Test zakończony - przetestowano {st.session_state.test_progress} odpowiedzi")

    # Save test results
    test_results = {
        "session_info": {
            "session_id": st.session_state.get("session_id", "unknown"),
            "current_stage": st.session_state.get("current_stage", "unknown"),
            "total_messages": len(st.session_state.get("messages", []))
        },
        "conversation_history": st.session_state.get("messages", []),
        "technical_logs": st.session_state.get("technical_log", []),
        "test_summary": {
            "total_logs": len(st.session_state.get("technical_log", [])),
            "stage_transitions": len([log for log in st.session_state.get("technical_log", [])
                                      if log.get("event_type") == "stage_transition"]),
            "errors": len([log for log in st.session_state.get("technical_log", [])
                           if log.get("event_type") == "error"])
        }
    }

    saved_file = save_test_result(test_id, test_name, responses_list, test_results, models_used)
    if saved_file:
        add_technical_log("info", f"💾 Wyniki zapisane: {saved_file}")
        st.success(f"✅ Wyniki testu zapisane: `{saved_file}`")

    # Auto-display test results
    st.markdown("---")
    st.subheader("📊 Wyniki testu")
    display_test_results()



def display_test_results():
    """Display full test results with JSON logs"""
    
    # Prepare complete test data
    test_results = {
        "test_completed_at": datetime.now().isoformat(),
        "session_info": {
            "session_id": st.session_state.get("session_id", "unknown"),
            "current_stage": st.session_state.get("current_stage", "unknown"),
            "total_messages": len(st.session_state.get("messages", []))
        },
        "conversation_history": st.session_state.get("messages", []),
        "technical_logs": st.session_state.get("technical_log", []),
        "test_summary": {
            "total_logs": len(st.session_state.get("technical_log", [])),
            "stage_transitions": len([log for log in st.session_state.get("technical_log", [])
                                      if log.get("event_type") == "stage_transition"]),
            "errors": len([log for log in st.session_state.get("technical_log", [])
                           if log.get("event_type") == "error"])
        }
    }
    
    # Show summary metrics first
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Wiadomości", test_results["session_info"]["total_messages"])
    with col2:
        st.metric("Logi techniczne", test_results["test_summary"]["total_logs"])
    with col3:
        st.metric("Przejścia etapów", test_results["test_summary"]["stage_transitions"])
    with col4:
        st.metric("Błędy", test_results["test_summary"]["errors"], delta_color="inverse")
    
    # Display full JSON results
    st.subheader("📋 Pełna historia testu (JSON)")
    st.json(test_results)
    
    # Download button for results
    json_str = json.dumps(test_results, ensure_ascii=False, indent=2)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"psychia_test_results_{timestamp}.json"
    
    st.download_button(
        label="💾 Pobierz wyniki testu",
        data=json_str,
        file_name=filename,
        mime="application/json",
        key="download_test_results"
    )


def export_test_logs():
    """Export test logs to JSON format"""
    logs_data = {
        "test_timestamp": datetime.now().isoformat(),
        "session_id": st.session_state.get("session_id", "unknown"),
        "current_stage": st.session_state.get("current_stage", "unknown"),
        "total_logs": len(st.session_state.technical_log),
        "logs": st.session_state.technical_log
    }
    
    # Create download
    json_str = json.dumps(logs_data, ensure_ascii=False, indent=2)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"psychia_test_logs_{timestamp}.json"
    
    st.download_button(
        label="⬇️ Pobierz JSON",
        data=json_str,
        file_name=filename,
        mime="application/json"
    )
    
    st.success(f"Logi przygotowane do pobrania: {filename}")


def copy_logs_to_clipboard():
    """Show logs in copyable format"""
    logs_text = ""
    for log in st.session_state.technical_log:
        timestamp = log["timestamp"]
        event_type = log["event_type"]
        data = log["data"]
        response_time = log.get("response_time_ms", "")
        time_info = f" ({response_time}ms)" if response_time else ""
        
        logs_text += f"{timestamp} [{event_type}]{time_info}: {data}\n"
    
    st.text_area(
        "Logi do skopiowania:",
        value=logs_text,
        height=300,
        key="copyable_logs"
    )


def show_test_summary():
    """Show summary of test results"""
    if not st.session_state.technical_log:
        return
    
    # Count different event types
    event_counts = {}
    total_response_time = 0
    response_count = 0
    stage_transitions = 0
    
    for log in st.session_state.technical_log:
        event_type = log["event_type"]
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        if log.get("response_time_ms"):
            total_response_time += log["response_time_ms"]
            response_count += 1
        
        if event_type == "stage_transition":
            stage_transitions += 1
    
    # Display summary
    st.subheader("📈 Podsumowanie testu")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Wszystkie logi", len(st.session_state.technical_log))
    
    with col2:
        avg_response_time = total_response_time / response_count if response_count > 0 else 0
        st.metric("Śr. czas odpowiedzi", f"{avg_response_time:.0f}ms")
    
    with col3:
        st.metric("Przejścia etapów", stage_transitions)
    
    with col4:
        errors = event_counts.get("error", 0)
        st.metric("Błędy", errors, delta_color="inverse")
    
    # Event type breakdown
    if event_counts:
        st.write("**Rozkład typów wydarzeń:**")
        for event_type, count in sorted(event_counts.items()):
            st.write(f"- {event_type}: {count}")