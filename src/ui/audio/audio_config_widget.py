"""Audio configuration widget for Streamlit UI."""

import streamlit as st
from typing import Optional, Dict, Any

from ...audio.services.audio_service import AudioService


class AudioConfigWidget:
    """Widget for configuring audio/TTS settings."""

    def __init__(self, audio_service: AudioService):
        """
        Initialize audio config widget.

        Args:
            audio_service: Audio service instance
        """
        self.audio_service = audio_service

    def render_config_section(self) -> Optional[Dict[str, Any]]:
        """
        Render audio configuration section in UI.

        Returns:
            Configuration dictionary if valid, None otherwise
        """
        with st.expander("🔊 Głos (WebRTC TTS / ElevenLabs)", expanded=False):
            # API Key input - secure handling
            env_api_key = self.audio_service.get_api_key_from_env()
            has_env_key = bool(env_api_key)

            if has_env_key:
                st.info(f"✅ Klucz API ElevenLabs został wczytany z zmiennych środowiskowych")
                # Use environment key but don't show it
                api_key = env_api_key
            else:
                api_key = st.text_input(
                    "ELEVENLABS_API_KEY",
                    type="password",
                    placeholder="Wklej swój klucz API z ElevenLabs...",
                    help="Klucz API z ElevenLabs (lub ustaw zmienną środowiskową ELEVENLABS_API_KEY)",
                )

            # Voice ID input
            default_voice_id = self.audio_service.get_default_voice_id()
            voice_id = st.text_input(
                "ElevenLabs Voice ID",
                value=default_voice_id,
                help="ID głosu z ElevenLabs (domyślny: Sarah)",
            )

            # Voice configuration info
            if api_key:
                st.success("✓ Klucz API skonfigurowany")
            else:
                st.warning("⚠️ Brak klucza API - audio nie będzie działać")

            # Test TTS button and diagnostics
            col1, col2 = st.columns(2)

            with col1:
                if api_key and voice_id:
                    if st.button("🎵 Test głosu", help="Przetestuj konfigurację TTS"):
                        self._test_voice_config(api_key, voice_id)

            with col2:
                if st.button("🔧 Diagnostyka", help="Sprawdź konfigurację WebRTC"):
                    self._show_webrtc_diagnostics()

        # Return config if valid
        if api_key and voice_id:
            return {"api_key": api_key, "voice_id": voice_id}

        return None

    def _test_voice_config(self, api_key: str, voice_id: str) -> None:
        """
        Test voice configuration.

        Args:
            api_key: ElevenLabs API key
            voice_id: Voice ID to test
        """
        try:
            from ...audio.providers.elevenlabs_provider import ElevenLabsTTSProvider

            # Create temporary provider for testing
            provider = ElevenLabsTTSProvider(api_key=api_key, voice_id=voice_id)

            if provider.is_available():
                st.success("✓ Konfiguracja głosu jest poprawna!")
            else:
                st.error("❌ Nie można połączyć się z ElevenLabs API")

        except Exception as e:
            st.error(f"❌ Błąd testowania konfiguracji: {str(e)}")

    def _show_webrtc_diagnostics(self) -> None:
        """Show WebRTC diagnostics information."""
        st.markdown("**🔧 Diagnostyka WebRTC**")

        try:
            # Check if streamlit-webrtc is available
            import streamlit_webrtc

            st.success(f"✓ streamlit-webrtc zainstalowane (v{streamlit_webrtc.__version__})")

            # Check if aiortc is available
            import aiortc

            st.success("✓ aiortc dostępne")

            # Check if av is available
            import av

            st.success("✓ PyAV dostępne")

            # Show browser info
            st.info(
                """**Informacje o przeglądarce:**
• Sprawdź konsolę przeglądarki (F12) pod kątem błędów WebRTC
• Upewnij się, że przeglądarka ma dostęp do urządzeń audio
• Chrome: Przejdź do chrome://webrtc-internals/ dla szczegółów
• Firefox: about:webrtc dla diagnostyki
            """
            )

            # Check session state
            if hasattr(st.session_state, "pcm_buffer"):
                st.success("✓ PCM buffer utworzony")
            else:
                st.warning("⚠️ Brak PCM buffer - zostanie utworzony przy użyciu")

        except ImportError as e:
            missing_lib = str(e).split("'")[1] if "'" in str(e) else "unknown"
            st.error(f"❌ Brak biblioteki: {missing_lib}")
            st.info("Zainstaluj wymagane biblioteki: `pip install streamlit-webrtc aiortc av`")

        except Exception as e:
            st.error(f"❌ Błąd diagnostyki: {str(e)}")

    @staticmethod
    def save_config_to_session(config: Dict[str, Any]) -> None:
        """
        Save audio configuration to session state.

        Args:
            config: Configuration dictionary to save
        """
        st.session_state["_tts_cfg"] = config

    @staticmethod
    def get_config_from_session() -> Optional[Dict[str, Any]]:
        """
        Get audio configuration from session state.

        Returns:
            Configuration dictionary or None if not set
        """
        return st.session_state.get("_tts_cfg")
