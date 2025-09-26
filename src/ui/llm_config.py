"""LLM Provider Configuration UI Component."""

import streamlit as st
from typing import Dict, Any
from src.llm import ModelDiscovery


class LLMConfigUI:
    """UI component for LLM provider configuration."""

    def __init__(self):
        self._ensure_session_state()

    def display_provider_config(self) -> Dict[str, Any]:
        """Display LLM provider configuration interfaces."""
        st.subheader("🤖 Modele LLM")

        with st.expander("🔑 API Keys (wymagane dla modeli)", expanded=True):
            self._display_api_keys_config()

        return self._display_model_selection()

    @staticmethod
    def _display_api_keys_config():
        """Display API keys configuration."""
        import os

        st.markdown("**Konfiguracja kluczy API**")

        # Initialize variables
        openai_key = ""
        google_key = ""

        # OpenAI API Key
        env_openai_key = os.getenv("OPENAI_API_KEY", "")
        if env_openai_key:
            st.success("✅ OpenAI API Key wczytany ze zmiennych środowiskowych")
            st.session_state.openai_api_key = env_openai_key
            openai_key = env_openai_key
        else:
            openai_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value=st.session_state.get("openai_api_key", ""),
                placeholder="Wklej klucz API OpenAI...",
                help="Klucz API OpenAI dla dostępu do modeli GPT (lub ustaw OPENAI_API_KEY w .env)",
            )
            if openai_key != st.session_state.get("openai_api_key", ""):
                st.session_state.openai_api_key = openai_key

        # Google API Key
        env_google_key = os.getenv("GOOGLE_API_KEY", "")
        if env_google_key:
            st.success("✅ Google API Key wczytany ze zmiennych środowiskowych")
            st.session_state.google_api_key = env_google_key
            google_key = env_google_key
        else:
            google_key = st.text_input(
                "Google API Key",
                type="password",
                value=st.session_state.get("google_api_key", ""),
                placeholder="Wklej klucz API Google...",
                help="Klucz API Google dla dostępu do modeli Gemini (lub ustaw GOOGLE_API_KEY w .env)",
            )
            if google_key != st.session_state.get("google_api_key", ""):
                st.session_state.google_api_key = google_key

        # Check if keys changed
        old_openai_key = st.session_state.get("_last_openai_key", "")
        old_google_key = st.session_state.get("_last_google_key", "")

        key_changed = (openai_key != old_openai_key) or (google_key != old_google_key)

        # Update environment variables if keys changed
        if openai_key:
            import os

            os.environ["OPENAI_API_KEY"] = openai_key

        if google_key:
            import os

            os.environ["GOOGLE_API_KEY"] = google_key

        # Store current keys for comparison
        st.session_state._last_openai_key = openai_key
        st.session_state._last_google_key = google_key

        # Refresh models if API keys changed
        if key_changed and "available_models" in st.session_state:
            st.session_state.available_models = None

    def _display_model_selection(self) -> Dict[str, Any]:
        """Display model selection interfaces."""
        if st.button("🔄 Odśwież listę modeli"):
            st.session_state.available_models = None
            st.rerun()

        # Get available models
        available_models = self._get_available_models()

        # Debug information in collapsible section
        with st.expander("🔍 Debug: Dostępne modele", expanded=False):
            st.write("**Modele według dostawców:**")
            for provider, models in available_models.items():
                available_count = sum(1 for m in models if m["available"])
                total_count = len(models)
                if available_count == total_count:
                    st.write(f"- {provider}: {total_count} modeli ✅")
                else:
                    st.write(
                        f"- {provider}: {available_count}/{total_count} modeli dostępnych (pozostałe wymagają klucza API)"
                    )

            # Show API key status
            st.write("**Status kluczy API:**")
            import os

            openai_key = st.session_state.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
            google_key = st.session_state.get("google_api_key") or os.getenv("GOOGLE_API_KEY")

            st.write(f"- OpenAI: {'✅ Ustawiony' if openai_key else '❌ Brak klucza'}")
            st.write(f"- Google: {'✅ Ustawiony' if google_key else '❌ Brak klucza'}")

        # Format models for selection
        all_options = self._format_model_options(available_models)

        if not all_options:
            st.error("❌ Brak dostępnych modeli. Sprawdź:")
            st.write("1. Czy klucze API są wprowadzone")
            st.write("2. Czy masz połączenie z internetem")
            return {}

        st.success(f"✅ Znaleziono {len(all_options)} dostępnych modeli")

        # Therapist model selection
        st.markdown("### 🩺 Model Terapeuty")
        therapist_selected = st.selectbox(
            "Wybierz model terapeuty",
            options=list(all_options.keys()),
            index=self._get_default_index(all_options, "therapist"),
            key="therapist_model_select",
        )

        # Display therapist model info immediately
        if therapist_selected and therapist_selected in all_options:
            self._display_model_info(all_options[therapist_selected])

        st.divider()

        # Supervisor model selection
        st.markdown("### 👥 Model Nadzorcy")
        supervisor_selected = st.selectbox(
            "Wybierz model nadzorcy",
            options=list(all_options.keys()),
            index=self._get_default_index(all_options, "supervisor"),
            key="supervisor_model_select",
        )

        # Display supervisor model info immediately
        if supervisor_selected and supervisor_selected in all_options:
            self._display_model_info(all_options[supervisor_selected])

        st.divider()

        # Agent parameters moved to dedicated settings page

        return {
            "therapist_model": all_options.get(therapist_selected),
            "supervisor_model": all_options.get(supervisor_selected),
        }

    @staticmethod
    def _get_available_models() -> Dict[str, list]:
        """Get available models with caching."""
        if "available_models" not in st.session_state or st.session_state.available_models is None:
            # Get real model availability, but use mixed approach for speed
            try:
                # Use dynamic model discovery with caching
                static_models = ModelDiscovery.get_all_available_models()

                st.session_state.available_models = {
                    "openai": static_models.get("openai", []),
                    "gemini": static_models.get("gemini", []),
                }
            except Exception:
                # Fallback to static list if real check fails
                st.session_state.available_models = ModelDiscovery.get_all_available_models()

        return st.session_state.available_models

    @staticmethod
    def _format_model_options(available_models: Dict[str, list]) -> Dict[str, Dict[str, Any]]:
        """Format models for select box options."""
        options = {}

        for provider, models in available_models.items():
            for model in models:
                # Show all models, but indicate availability status
                if model["available"]:
                    display_name = f"[{provider.upper()}] {model['name']}"
                else:
                    display_name = f"[{provider.upper()}] {model['name']} (needs API key)"

                options[display_name] = {
                    "provider": provider,
                    "model_id": model["id"],
                    "name": model["name"],
                    "info": model,
                }

        return options

    @staticmethod
    def _get_default_index(options: Dict[str, Dict[str, Any]], role: str) -> int:
        """Get default index for model selection based on Config defaults."""
        # Get current defaults from Config (which may be updated by user preferences)
        from config import Config

        config = Config.get_instance()
        agent_defaults = config.get_agent_defaults()
        target_provider = None
        target_model = None

        if role == "therapist":
            target_provider = agent_defaults["therapist"]["provider"]
            target_model = agent_defaults["therapist"]["model"]
        elif role == "supervisor":
            target_provider = agent_defaults["supervisor"]["provider"]
            target_model = agent_defaults["supervisor"]["model"]

        if not target_model or not target_provider:
            return 0

        # Find exact match first (provider + model)
        for i, (display_name, model_info) in enumerate(options.items()):
            if model_info["provider"] == target_provider and model_info["model_id"] == target_model:
                return i

        # If no exact match, try recommendations as fallback
        recommendations = ModelDiscovery.get_recommended_models()

        if role == "therapist" and recommendations["therapist"]:
            provider, model = recommendations["therapist"].split(":", 1)
            for i, (display_name, model_info) in enumerate(options.items()):
                if model_info["provider"] == provider and model_info["model_id"] == model:
                    return i

        elif role == "supervisor" and recommendations["supervisor"]:
            provider, model = recommendations["supervisor"].split(":", 1)
            for i, (display_name, model_info) in enumerate(options.items()):
                if model_info["provider"] == provider and model_info["model_id"] == model:
                    return i

        return 0

    @staticmethod
    def _display_model_info(model_info: Dict[str, Any]):
        """Display model information."""
        info = model_info["info"]

        # Compact info display
        status = "✅ Gotowy" if info["available"] else "⚠️ Wymaga klucza API"
        provider_icon = {"openai": "🌐", "gemini": "🧠"}.get(model_info["provider"], "🔧")

        st.markdown(f"**{provider_icon} {model_info['provider'].upper()}** | {status}")

        # Additional details in smaller text
        details = []
        if "context_length" in info:
            details.append(f"Kontekst: {info['context_length']:,}")
        if "size" in info and info["size"]:
            size_gb = (
                info["size"] / (1024**3) if info["size"] > 1024**3 else info["size"] / (1024**2)
            )
            unit = "GB" if info["size"] > 1024**3 else "MB"
            details.append(f"Rozmiar: {size_gb:.1f} {unit}")

        if details:
            st.caption(" | ".join(details))

    @staticmethod
    def _display_agent_parameters():
        """Display individual agent parameter controls."""
        st.markdown("### ⚙️ Parametry Agentów")

        with st.expander("🔧 Konfiguracja parametrów per agent", expanded=False):
            from config import Config

            # Create two columns for therapist and supervisor
            col1, col2 = st.columns(2)

            # Get current parameters from config
            therapist_params = Config.get_agent_parameters("therapist")
            supervisor_params = Config.get_agent_parameters("supervisor")

            with col1:
                st.markdown("**🩺 Terapeuta**")

                therapist_temp = st.slider(
                    "Temperatura",
                    min_value=0.0,
                    max_value=2.0,
                    value=float(therapist_params["temperature"]),
                    step=0.1,
                    key="therapist_temperature",
                    help="Kontroluje kreatywność odpowiedzi (0.0 = deterministyczny, 2.0 = bardzo kreatywny)",
                )

                therapist_max_tokens = st.slider(
                    "Max tokeny",
                    min_value=50,
                    max_value=1000,
                    value=int(therapist_params["max_tokens"]),
                    step=25,
                    key="therapist_max_tokens",
                    help="Maksymalna długość odpowiedzi",
                )

                therapist_top_p = st.slider(
                    "Top P",
                    min_value=0.1,
                    max_value=1.0,
                    value=float(therapist_params["top_p"]),
                    step=0.05,
                    key="therapist_top_p",
                    help="Kontroluje różnorodność odpowiedzi poprzez nucleus sampling",
                )

            with col2:
                st.markdown("**👥 Nadzorca**")

                supervisor_temp = st.slider(
                    "Temperatura",
                    min_value=0.0,
                    max_value=2.0,
                    value=float(supervisor_params["temperature"]),
                    step=0.1,
                    key="supervisor_temperature",
                    help="Kontroluje kreatywność decyzji nadzorcy",
                )

                supervisor_max_tokens = st.slider(
                    "Max tokeny",
                    min_value=50,
                    max_value=500,
                    value=int(supervisor_params["max_tokens"]),
                    step=25,
                    key="supervisor_max_tokens",
                    help="Maksymalna długość odpowiedzi nadzorcy",
                )

                supervisor_top_p = st.slider(
                    "Top P",
                    min_value=0.1,
                    max_value=1.0,
                    value=float(supervisor_params["top_p"]),
                    step=0.05,
                    key="supervisor_top_p",
                    help="Kontroluje różnorodność decyzji nadzorcy",
                )

            # Save parameters button
            if st.button("💾 Zapisz parametry agentów", use_container_width=True):
                # Update session state
                st.session_state.therapist_parameters = {
                    "temperature": therapist_temp,
                    "max_tokens": therapist_max_tokens,
                    "top_p": therapist_top_p,
                }

                st.session_state.supervisor_parameters = {
                    "temperature": supervisor_temp,
                    "max_tokens": supervisor_max_tokens,
                    "top_p": supervisor_top_p,
                }

                # Save to config file
                if LLMConfigUI._save_agent_parameters(
                    therapist_params={
                        "temperature": therapist_temp,
                        "max_tokens": therapist_max_tokens,
                        "top_p": therapist_top_p,
                    },
                    supervisor_params={
                        "temperature": supervisor_temp,
                        "max_tokens": supervisor_max_tokens,
                        "top_p": supervisor_top_p,
                    },
                ):
                    st.success("✅ Parametry agentów zostały zapisane!")
                    st.rerun()
                else:
                    st.error("❌ Błąd podczas zapisywania parametrów")

    @staticmethod
    def _save_agent_parameters(therapist_params: dict, supervisor_params: dict) -> bool:
        """Save agent parameters to config file."""
        try:
            import json
            from pathlib import Path
            from config import Config

            # Load current config
            config = Config.get_instance()
            config_file = config.CONFIG_FILE
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            else:
                config_data = {}

            # Ensure agents structure exists
            if "agents" not in config_data:
                config_data["agents"] = {}

            # Update therapist parameters
            if "therapist" not in config_data["agents"]:
                config_data["agents"]["therapist"] = {"provider": "openai", "model": "gpt-4o-mini"}
            config_data["agents"]["therapist"]["parameters"] = therapist_params

            # Update supervisor parameters
            if "supervisor" not in config_data["agents"]:
                config_data["agents"]["supervisor"] = {
                    "provider": "gemini",
                    "model": "gemini-1.5-flash",
                }
            config_data["agents"]["supervisor"]["parameters"] = supervisor_params

            # Save updated config
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            st.error(f"Błąd zapisywania parametrów: {str(e)}")
            return False

    @staticmethod
    def _ensure_session_state():
        """Ensure required session state variables exist."""
        if "available_models" not in st.session_state:
            st.session_state.available_models = None
        if "openai_api_key" not in st.session_state:
            st.session_state.openai_api_key = ""
        if "google_api_key" not in st.session_state:
            st.session_state.google_api_key = ""


def display_llm_config() -> Dict[str, Any]:
    """Display LLM configuration UI."""
    config_ui = LLMConfigUI()
    return config_ui.display_provider_config()
