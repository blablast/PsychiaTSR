"""
Advanced model testing page with prompt memory verification and chat interfaces.
"""

import traceback
from datetime import datetime

import streamlit as st

from config import Config
from ...llm import OpenAIProvider, GeminiProvider
from ...llm.model_discovery import ModelDiscovery


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_openai_models():
    """Get OpenAI models from ModelDiscovery cache (now dynamic!)."""
    # First try ModelDiscovery cache
    models_from_cache = get_models_from_discovery("openai")
    if models_from_cache and len(models_from_cache) > 4:  # We expect more than fallback models
        return models_from_cache

    # If cache fails, try direct API as fallback
    try:
        import openai
        config = Config.get_instance()
        client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        models = client.models.list()

        # Filter for chat models (exclude embeddings, whisper, etc.)
        chat_models = []
        for model in models.data:
            model_id = model.id
            # Include GPT models and other chat models, exclude specific types
            if (any(keyword in model_id.lower() for keyword in ['gpt', 'chatgpt']) and
                not any(exclude in model_id.lower() for exclude in ['embedding', 'whisper', 'tts', 'davinci-002', 'babbage-002'])):
                chat_models.append(model_id)

        # Sort models: put popular ones first, then alphabetically
        priority_models = ['gpt-4o-mini', 'gpt-4o', 'gpt-4', 'gpt-3.5-turbo']
        sorted_models = []

        # Add priority models first (if available)
        for priority in priority_models:
            if priority in chat_models:
                sorted_models.append(priority)
                chat_models.remove(priority)

        # Add remaining models alphabetically
        sorted_models.extend(sorted(chat_models))

        return sorted_models

    except Exception as e:
        error_msg = f"Błąd pobierania modeli OpenAI: {str(e)}"
        st.error(error_msg)

        # Check if it's an API key error
        if "401" in str(e) or "invalid_api_key" in str(e):
            st.warning("⚠️ **Problem z kluczem API OpenAI:**")
            st.info("""
            **Rozwiązania:**
            1. **Zrestartuj aplikację Streamlit** (może używać starego klucza)
               ```bash
               # Zatrzymaj: Ctrl+C w terminalu
               # Uruchom ponownie: streamlit run app.py
               ```
            2. Sprawdź klucz na [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
            3. Upewnij się, że klucz ma uprawnienia do modeli chat
            4. Sprawdź czy nie przekroczyłeś limitów API
            5. Użyj przycisku "🔧 Debug API" poniżej do diagnozy
            """)
        else:
            st.info("Używana jest zapasowa lista modeli. Sprawdź połączenie internetowe.")

        # Fallback to hardcoded list
        return ["gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo"]


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_models_from_discovery(provider: str):
    """Get models using ModelDiscovery with JSON cache."""
    try:
        # Get cached models (loads from JSON if available)
        all_models = ModelDiscovery.get_models_from_cache()

        if provider.lower() == "openai":
            openai_models = all_models.get("openai", [])
            # Extract just model names and sort by popularity
            model_names = [model.get("id", model.get("name", "")) for model in openai_models if model.get("id") or model.get("name")]

            # Priority sorting
            priority_models = ['gpt-4o-mini', 'gpt-4o', 'gpt-4', 'gpt-3.5-turbo']
            sorted_models = []

            for priority in priority_models:
                if priority in model_names:
                    sorted_models.append(priority)
                    model_names.remove(priority)

            sorted_models.extend(sorted(model_names))
            return sorted_models if sorted_models else ["gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo"]

        elif provider.lower() == "gemini":
            gemini_models = all_models.get("gemini", [])
            model_names = [model.get("name", model.get("id", "")) for model in gemini_models if model.get("name") or model.get("id")]
            return model_names if model_names else ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]

    except Exception as e:
        st.info(f"💾 ModelDiscovery cache: {str(e)}... używam zapasowej listy")
        # Fallback to static lists
        if provider.lower() == "openai":
            return ["gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo"]
        else:
            return ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]

    return []


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_gemini_models():
    """Get Gemini models from ModelDiscovery cache (now dynamic!)."""
    return get_models_from_discovery("gemini")


def model_test_page():
    """Advanced model testing interfaces with prompt memory verification."""

    st.title("🧪 Advanced Model Testing")
    st.markdown("Kompleksowe testowanie modeli AI z weryfikacją pamięci promptów")

    # Test mode selection
    test_mode = st.radio(
        "Tryb testowania:",
        ["💬 Chat Mode", "🧠 Memory Test Mode"],
        horizontal=True
    )

    if test_mode == "🧠 Memory Test Mode":
        memory_test_interface()
    else:
        chat_test_interface()

def chat_test_interface():
    """Simple chat testing interfaces."""
    st.subheader("💬 Chat Mode")
    st.markdown("Prosty test czatu z wybranym modelem")

    # Model selection
    col1, col2 = st.columns([3, 1])

    with col1:
        # Provider selection
        provider = st.selectbox(
            "Provider:",
            ["OpenAI", "Gemini"],
            key="test_provider"
        )

        # Model selection based on provider
        if provider == "OpenAI":
            with st.spinner("Pobieranie listy modeli OpenAI..."):
                model_options = get_openai_models()
        else:  # Gemini
            model_options = get_gemini_models()

        # Model selection with refresh button
        col_model, col_refresh = st.columns([4, 1])
        with col_model:
            model = st.selectbox(
                f"Model ({len(model_options)} dostępnych):",
                model_options,
                key="test_model"
            )
        with col_refresh:
            st.write("")  # Space for alignment
            if st.button("🔄", help="Odśwież listę modeli", key="refresh_models"):
                if provider == "OpenAI":
                    get_openai_models.clear()  # Clear cache
                    st.success("Lista modeli odświeżona!")
                    st.rerun()
                else:
                    # Also refresh Gemini models cache
                    get_gemini_models.clear()
                    get_models_from_discovery.clear()
                    st.success("Cache modeli Gemini odświeżony!")

        # Show cache info and debug options
        if provider == "OpenAI":
            col_info, col_debug = st.columns([3, 1])
            with col_info:
                st.caption("ℹ️ Modele z ModelDiscovery cache (JSON) + API fallback")
            with col_debug:
                if st.button("🔧 Debug API", help="Sprawdź status klucza API"):
                    with st.expander("🔍 Debug OpenAI API", expanded=True):
                        try:
                            import openai
                            config = Config.get_instance()
                            client = openai.OpenAI(api_key=config.OPENAI_API_KEY)

                            # Test basic connection
                            from openai.types.chat import ChatCompletionUserMessageParam
                            response = client.chat.completions.create(
                                model='gpt-3.5-turbo',
                                messages=[ChatCompletionUserMessageParam(role='user', content='test')],
                                max_tokens=5
                            )
                            st.success("✅ Klucz API działa poprawnie!")
                            st.info(f"Test response: {response.choices[0].message.content}")

                            # Try to get models
                            models = client.models.list()
                            st.success(f"✅ Dostęp do listy modeli: {len(models.data)} modeli")

                        except Exception as debug_e:
                            st.error(f"❌ Problem z API: {debug_e}")
                            if "401" in str(debug_e):
                                st.warning("Klucz API jest nieprawidłowy lub nieaktywny")
                            elif "429" in str(debug_e):
                                st.warning("Przekroczono limity API")
                            else:
                                st.warning("Nieznany błąd API")

    with col2:
        # Settings
        use_streaming = st.checkbox("Streaming", value=True)
        show_debug = st.checkbox("Debug info", value=True)

    # Model info
    with st.expander("ℹ️ Informacje o modelach", expanded=False):
        if provider == "OpenAI":
            st.info(f"**Dostępne modele OpenAI:** {len(model_options)}")
            st.write("**Najpopularniejsze:**")
            popular = ['gpt-4o-mini', 'gpt-4o', 'gpt-4', 'gpt-3.5-turbo']
            for pop_model in popular:
                if pop_model in model_options:
                    st.write(f"• `{pop_model}`")

            if len(model_options) > 4:
                with st.expander("Pokaż wszystkie modele"):
                    for model_name in model_options:
                        st.write(f"• `{model_name}`")
        else:
            st.info("**Modele Gemini** są teraz pobierane z ModelDiscovery cache (dynamicznie!)")
            for model_name in model_options:
                st.write(f"• `{model_name}`")

    # Chat parameters
    with st.expander("⚙️ Parametry"):
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        max_tokens = st.slider("Max tokens", 50, 2000, 500, 50)

        system_prompt = st.text_area(
            "System prompt (opcjonalny):",
            placeholder="Jesteś pomocnym asystentem...",
            height=100
        )

    # Initialize chat history
    if "test_messages" not in st.session_state:
        st.session_state.test_messages = []

    if "test_errors" not in st.session_state:
        st.session_state.test_errors = []

    # Clear buttons
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🗑️ Wyczyść chat"):
            st.session_state.test_messages = []
            st.rerun()

    with col2:
        if st.button("🗑️ Wyczyść błędy"):
            st.session_state.test_errors = []
            st.rerun()

    # Session stats
    if st.session_state.test_messages:
        with st.expander("📊 Statystyki sesji", expanded=False):
            total_messages = len(st.session_state.test_messages)
            user_messages = len([m for m in st.session_state.test_messages if m["role"] == "user"])
            assistant_messages = len([m for m in st.session_state.test_messages if m["role"] == "assistant"])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Wszystkie wiadomości", total_messages)
            with col2:
                st.metric("Użytkownik", user_messages)
            with col3:
                st.metric("Asystent", assistant_messages)

    # Error display
    if st.session_state.test_errors:
        with st.expander(f"❌ Błędy ({len(st.session_state.test_errors)})", expanded=show_debug):
            for i, error in enumerate(reversed(st.session_state.test_errors[-10:])):
                st.error(f"**{error['timestamp']}**\n```\n{error['error']}\n```")

    # Quick prompts
    with st.expander("⚡ Szybkie prompty", expanded=False):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("👋 Powitanie", use_container_width=True):
                test_prompt = "Cześć! Jak się masz?"
                st.session_state.test_input = test_prompt

        with col2:
            if st.button("🧠 Kreatywność", use_container_width=True):
                test_prompt = "Napisz krótką historię o kocie, który odkrywa, że potrafi latać."
                st.session_state.test_input = test_prompt

        with col3:
            if st.button("💼 Biznes", use_container_width=True):
                test_prompt = "Jakie są kluczowe elementy dobrego planu biznesowego?"
                st.session_state.test_input = test_prompt

        with col4:
            if st.button("🔧 Kod", use_container_width=True):
                test_prompt = "Napisz funkcję Python, która sprawdza czy liczba jest pierwsza."
                st.session_state.test_input = test_prompt

    # Chat display
    st.markdown("### 💬 Chat")

    # Display chat history
    for message in st.session_state.test_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if show_debug and "debug" in message:
                with st.expander("🔍 Debug info"):
                    st.json(message["debug"])

    # Handle quick prompts
    if "test_input" in st.session_state and st.session_state.test_input:
        prompt = st.session_state.test_input
        st.session_state.test_input = ""  # Clear after use
    else:
        prompt = None

    # Chat input
    if not prompt:
        prompt = st.chat_input("Wpisz wiadomość...")

    if prompt:
        # Add user message
        st.session_state.test_messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })

        # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        # Generate response
        with st.chat_message("assistant"):
            try:
                response_container = st.empty()
                debug_info = {}

                # Create provider
                config = Config.get_instance()
                if provider == "OpenAI":
                    llm_provider = OpenAIProvider(model, api_key=config.OPENAI_API_KEY)
                else:
                    llm_provider = GeminiProvider(model, api_key=config.GOOGLE_API_KEY)

                debug_info["provider"] = provider
                debug_info["model"] = model
                debug_info["temperature"] = temperature
                debug_info["max_tokens"] = max_tokens
                debug_info["streaming"] = use_streaming

                # Set system prompt if provided
                if system_prompt.strip():
                    llm_provider.set_system_prompt(system_prompt.strip())
                    debug_info["system_prompt"] = True

                # Generate response
                start_time = datetime.now()

                if use_streaming and hasattr(llm_provider, 'generate_stream'):
                    # Streaming response
                    full_response = ""
                    for chunk in llm_provider.generate_stream(
                        prompt=prompt,
                        system_prompt=None,  # Already set above
                        temperature=temperature,
                        max_tokens=max_tokens
                    ):
                        full_response += chunk
                        response_container.write(full_response + "▊")

                    # Final response without cursor
                    response_container.write(full_response)
                    response = full_response

                else:
                    # Non-streaming response
                    with st.spinner(f"Generuję odpowiedź ({provider} {model})..."):
                        response = llm_provider.generate_sync(
                            prompt=prompt,
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                    response_container.write(response)

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                debug_info.update({
                    "response_length": len(response),
                    "duration_seconds": round(duration, 2),
                    "tokens_per_second": round(len(response.split()) / duration, 1) if duration > 0 else 0,
                    "success": True
                })

                # Add assistant message
                assistant_message = {
                    "role": "assistant",
                    "content": response,
                    "timestamp": end_time.isoformat(),
                    "debug": debug_info
                }
                st.session_state.test_messages.append(assistant_message)

                if show_debug:
                    with st.expander("🔍 Debug info"):
                        st.json(debug_info)

            except Exception as e:
                error_msg = f"Błąd {provider} {model}: {str(e)}"
                st.error(error_msg)

                # Log detailed error
                error_details = {
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "provider": provider,
                    "model": model,
                    "error": traceback.format_exc(),
                    "prompt": prompt
                }
                st.session_state.test_errors.append(error_details)

                # Add error message to chat
                st.session_state.test_messages.append({
                    "role": "assistant",
                    "content": f"❌ {error_msg}",
                    "timestamp": datetime.now().isoformat(),
                    "debug": {"error": True, "error_msg": str(e)}
                })

        # Refresh to show new messages
        st.rerun()


def memory_test_interface():
    """Advanced interfaces for testing prompt memory capabilities."""
    st.subheader("🧠 Memory Test Mode")
    st.markdown("Testowanie pamięci promptów systemowych i etapowych")

    # Test configuration
    with st.expander("⚙️ Konfiguracja testu", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            # Provider and model selection
            provider = st.selectbox(
                "Provider:",
                ["OpenAI", "Gemini"],
                key="memory_test_provider"
            )

            if provider == "OpenAI":
                with st.spinner("Pobieranie listy modeli OpenAI..."):
                    model_options = get_openai_models()
            else:
                model_options = get_gemini_models()

            model = st.selectbox(
                f"Model ({len(model_options)} dostępnych):",
                model_options,
                key="memory_test_model"
            )

        with col2:
            # Test parameters
            temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.1, key="memory_temp")
            max_tokens = st.slider("Max tokens", 50, 500, 200, 50, key="memory_tokens")

    # Test scenario configuration
    with st.expander("📝 Scenariusz testowy", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            system_prompt = st.text_area(
                "System Prompt (globalne ustawienia):",
                value="Jesteś profesjonalnym terapeutą. Zawsze odpowiadaj w języku polskim. Pamiętaj swoje ustawienia systemowe przez całą rozmowę.",
                height=120,
                key="memory_system_prompt"
            )

        with col2:
            stage_prompt = st.text_area(
                "Stage Prompt (etap 1 - powitanie):",
                value="ETAP 1: POWITANIE\nTwoim zadaniem jest ciepłe powitanie klienta i nawiązanie kontaktu. Przedstaw się jako terapeuta i zapytaj jak się klient czuje.",
                height=120,
                key="memory_stage_prompt"
            )

    # Test execution
    st.subheader("🚀 Wykonanie testu")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶️ Uruchom test", type="primary", use_container_width=True):
            with st.spinner("Uruchamianie testu..."):
                run_memory_test(provider, model, system_prompt, stage_prompt, temperature, max_tokens)
            st.rerun()

    with col2:
        if st.button("🗑️ Wyczyść wyniki", use_container_width=True):
            if "memory_test_results" in st.session_state:
                del st.session_state["memory_test_results"]
            st.rerun()

    with col3:
        if st.button("📊 Analiza wyników", use_container_width=True):
            if "memory_test_results" in st.session_state:
                analyze_memory_test_results()
            else:
                st.warning("Brak wyników do analizy. Uruchom najpierw test.")

    # Display test results
    if "memory_test_results" in st.session_state:
        display_memory_test_results()


def run_memory_test(provider: str, model: str, system_prompt: str, stage_prompt: str, temperature: float, max_tokens: int):
    """Execute memory test scenario using MemoryTestRunner."""
    try:
        # Import the refactored test runner
        from .memory_test_runner import MemoryTestRunner

        # Create and run test
        test_runner = MemoryTestRunner(
            provider=provider,
            model=model,
            system_prompt=system_prompt,
            stage_prompt=stage_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

        test_results = test_runner.run_test()

        # Store results in session state
        st.session_state["memory_test_results"] = test_results

    except Exception as e:
        st.error(f"❌ Błąd podczas testu: {str(e)}")
        st.exception(e)


def display_memory_test_results():
    """Display memory test results in organized format."""
    results = st.session_state["memory_test_results"]

    st.subheader("📊 Wyniki testu")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Model", f"{results['provider']} {results['model']}")

    with col2:
        memory_support = "✅ Tak" if results['supports_memory'] else "❌ Nie"
        st.metric("Pamięć konwersacji", memory_support)

    with col3:
        successful_steps = sum(1 for step in results['steps'] if step.get('success', False))
        st.metric("Udane kroki", f"{successful_steps}/{len(results['steps'])}")

    with col4:
        if 'total_duration_seconds' in results:
            duration_str = results['total_duration_seconds']
            try:
                duration = float(duration_str)
                if duration < 10:
                    duration_text = f"{duration:.3f}s"
                else:
                    duration_text = f"{duration:.1f}s"
                st.metric("Czas trwania", duration_text)
            except (ValueError, TypeError):
                st.metric("Czas trwania", f"{duration_str}s")
        else:
            test_time = datetime.fromisoformat(results['timestamp']).strftime("%H:%M:%S")
            st.metric("Czas rozpoczęcia", test_time)

    # Detailed step results
    st.subheader("📝 Szczegółowe wyniki")

    step_names = {
        1: "🔧 System Prompt",
        2: "🎯 Stage Prompt",
        3: "💬 Test Message",
        4: "🔍 Historia konwersacji",
        5: "🎯 Świadomość etapu"
    }

    for step in results['steps']:
        step_num = step['step']
        step_name = step_names.get(step_num, f"Krok {step_num}")

        with st.expander(f"{step_name} - {'✅ Sukces' if step.get('success') else '❌ Błąd'}", expanded=step.get('success', False)):
            col1, col2 = st.columns([1, 2])

            with col1:
                st.write("**Status:**", "✅ Sukces" if step.get('success') else "❌ Błąd")
                if 'method' in step:
                    st.write("**Metoda:**", step['method'])
                if 'duration_seconds' in step:
                    st.write("**Czas:**", f"{step['duration_seconds']}s")

            with col2:
                if 'message' in step:
                    st.write("**Wiadomość:**")
                    st.code(step['message'], language='text')

                if 'response' in step:
                    st.write("**Odpowiedź:**")
                    st.write(step['response'])

                if 'error' in step:
                    st.write("**Błąd:**")
                    st.code(step['error'], language='text')


def analyze_memory_test_results():
    """Analyze and provide insights about memory test results."""
    if "memory_test_results" not in st.session_state:
        st.warning("Brak wyników do analizy")
        return

    results = st.session_state["memory_test_results"]

    with st.expander("🔬 Analiza wyników", expanded=True):
        st.subheader("📈 Analiza możliwości modelu")

        # Memory support analysis
        if results['supports_memory']:
            st.success("✅ **Model wspiera pamięć konwersacji**")
            st.write("Model może zapamiętywać wcześniejsze wiadomości w sesji, co pozwala na:")
            st.write("- Ustawienie system prompt raz na początku")
            st.write("- Dodawanie stage promptów jako wiadomości konwersacji")
            st.write("- Kontynuowanie rozmowy z zachowaniem kontekstu")
        else:
            st.warning("⚠️ **Model nie wspiera pamięci konwersacji**")
            st.write("Model nie zachowuje historii między wiadomościami, co oznacza:")
            st.write("- System prompt musi być wysyłany z każdą wiadomością")
            st.write("- Stage prompty muszą być dołączane do każdego zapytania")
            st.write("- Mniejsza efektywność i większe zużycie tokenów")

        # Step analysis
        st.subheader("🔍 Analiza kroków")

        for step in results['steps']:
            step_num = step['step']

            if step_num == 1:  # System prompt
                if step.get('success'):
                    st.success(f"✅ **Krok {step_num}**: System prompt został ustawiony poprawnie")
                else:
                    st.error(f"❌ **Krok {step_num}**: Nie udało się ustawić system prompt")

            elif step_num == 2:  # Stage prompt
                if step.get('success'):
                    st.success(f"✅ **Krok {step_num}**: Stage prompt został przekazany do pamięci konwersacji")
                else:
                    st.warning(f"⚠️ **Krok {step_num}**: Stage prompt nie został ustawiony w pamięci")
                    if step.get('method') == 'no_memory_support':
                        st.info("Model nie wspiera pamięci - stage prompt musi być dołączany do każdego zapytania")

            elif step_num == 3:  # Test message
                if step.get('success'):
                    st.success(f"✅ **Krok {step_num}**: Wiadomość testowa wysłana i odebrana odpowiedź")
                    if 'duration_seconds' in step:
                        duration = step['duration_seconds']
                        if duration < 2:
                            st.info(f"⚡ Szybka odpowiedź: {duration}s")
                        elif duration > 10:
                            st.warning(f"🐌 Wolna odpowiedź: {duration}s")
                else:
                    st.error(f"❌ **Krok {step_num}**: Błąd wysyłania wiadomości testowej")

            elif step_num == 4:  # Memory check
                if step.get('success'):
                    response = step.get('response', '').lower()
                    if 'kacper' in response or 'cześć' in response:
                        st.success(f"✅ **Krok {step_num}**: Model pamięta wcześniejszą konwersację")
                    else:
                        st.warning(f"⚠️ **Krok {step_num}**: Model może nie pamiętać wcześniejszej konwersacji")
                else:
                    st.error(f"❌ **Krok {step_num}**: Błąd sprawdzania pamięci konwersacji")

            elif step_num == 5:  # Stage awareness
                if step.get('success'):
                    response = step.get('response', '').lower()
                    if any(word in response for word in ['powitanie', 'etap', 'pierwsz', '1']):
                        st.success(f"✅ **Krok {step_num}**: Model ma świadomość aktualnego etapu")
                    else:
                        st.warning(f"⚠️ **Krok {step_num}**: Model może nie pamiętać stage prompt")
                else:
                    st.error(f"❌ **Krok {step_num}**: Błąd sprawdzania świadomości etapu")

        # Recommendations
        st.subheader("💡 Rekomendacje")

        if results['supports_memory']:
            successful_steps = sum(1 for step in results['steps'] if step.get('success', False))
            if successful_steps >= 4:
                st.success("🎯 **Model nadaje się do użycia w systemie terapeutycznym**")
                st.write("Model wspiera pamięć konwersacji i prawidłowo obsługuje prompty.")
            else:
                st.warning("⚠️ **Model częściowo nadaje się do użycia**")
                st.write("Model wspiera pamięć, ale ma problemy z niektórymi funkcjami.")
        else:
            st.info("📝 **Model może być używany z ograniczeniami**")
            st.write("Model nie wspiera pamięci konwersacji - wymagane są modyfikacje w implementacji.")
            st.write("Rekomendacje:")
            st.write("- Dołączaj system prompt do każdego zapytania")
            st.write("- Dołączaj aktualny stage prompt do każdego zapytania")
            st.write("- Zarządzaj historią konwersacji ręcznie")


if __name__ == "__main__":
    model_test_page()