"""WebRTC widget for audio streaming."""

import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from typing import Optional

from ...audio.services.audio_service import AudioService
from ...audio.core.pcm_buffer import PcmBuffer


class WebRTCWidget:
    """Widget for WebRTC audio streaming integration."""

    def __init__(self, audio_service: AudioService):
        """
        Initialize WebRTC widget.

        Args:
            audio_service: Audio service instance
        """
        self.audio_service = audio_service

    def render_webrtc_streamer(self, pcm_buffer: PcmBuffer) -> None:
        """
        Render WebRTC streamer component.

        Args:
            pcm_buffer: PCM buffer for audio streaming
        """
        # Create audio track
        audio_track = self.audio_service.create_audio_track(pcm_buffer)

        # Get WebRTC configuration
        webrtc_config = self.audio_service.get_webrtc_config()

        # Render WebRTC streamer with error handling
        try:
            # Configure WebRTC parameters
            webrtc_params = {
                "key": "psychia-tts-audio",
                "mode": WebRtcMode.SENDONLY,
                "rtc_configuration": webrtc_config["rtc_configuration"],
                "sendback_audio": webrtc_config["sendback_audio"],
                "source_audio_track": audio_track,
            }

            # Add media_stream_constraints (now always present)
            webrtc_params["media_stream_constraints"] = webrtc_config["media_stream_constraints"]

            # Add additional parameters for better device detection
            if "audio_frame_callback" in webrtc_config:
                webrtc_params["audio_frame_callback"] = webrtc_config["audio_frame_callback"]

            # Try to render WebRTC streamer
            webrtc_ctx = webrtc_streamer(**webrtc_params)

            # Check WebRTC state and provide better error messages
            if webrtc_ctx and hasattr(webrtc_ctx, 'state'):
                if webrtc_ctx.state.playing:
                    st.success("🎵 WebRTC audio streaming aktywne")
                elif webrtc_ctx.state.signalling:
                    st.info("🔄 Łączenie z WebRTC...")
                else:
                    st.warning("⚠️ WebRTC nieaktywne - sprawdź uprawnienia przeglądarki")

        except Exception as e:
            error_msg = str(e).lower()
            if "device" in error_msg or "permission" in error_msg:
                st.error("❌ Brak dostępu do urządzenia audio")
                st.info("""💡 **Rozwiązania problemu z urządzeniem audio:**

**1. Uprawnienia przeglądarki:**
- Kliknij ikonę kłódki w pasku adresu
- Zezwól na dostęp do mikrofonu/głośników
- Odśwież stronę (F5)

**2. Ustawienia systemu:**
- Windows: Sprawdź Ustawienia > Prywatność > Mikrofon
- Upewnij się, że przeglądarki mają dostęp do audio

**3. Przeglądarki:**
- Chrome: chrome://settings/content/microphone
- Edge: edge://settings/content/microphone
- Firefox: about:preferences#privacy

**4. Sprzęt:**
- Sprawdź czy słuchawki/głośniki są podłączone
- Przetestuj inne aplikacje audio
                """)
            elif "webrtc" in error_msg or "stream" in error_msg:
                st.error("❌ Błąd WebRTC streaming")
                st.info("""💡 **Rozwiązania problemu WebRTC:**

- Odśwież stronę (F5)
- Spróbuj innej przeglądarki (Chrome zalecana)
- Wyłącz blokery reklam na tej stronie
- Sprawdź połączenie internetowe
                """)
            else:
                st.error(f"❌ Błąd WebRTC: {str(e)}")
                st.info("💡 Spróbuj odświeżyć stronę lub wyłączyć/włączyć audio w ustawieniach")

            # Don't re-raise - let app continue without audio

    def ensure_pcm_buffer(self) -> PcmBuffer:
        """
        Ensure PCM buffer exists in session state.

        Returns:
            PCM buffer from session state
        """
        if "pcm_buffer" not in st.session_state:
            st.session_state.pcm_buffer = self.audio_service.create_pcm_buffer()

        return st.session_state.pcm_buffer

    def render_audio_status(self) -> None:
        """Render audio streaming status information."""
        if self.audio_service.streaming_manager.is_streaming:
            st.success("🎵 Audio streaming aktywne")
        else:
            st.info("🔇 Audio streaming nieaktywne")

    def cleanup_on_audio_disable(self) -> None:
        """Clean up audio resources when audio is disabled."""
        # Close PCM buffer if it exists
        if "pcm_buffer" in st.session_state:
            pcm_buffer = st.session_state.pcm_buffer
            if hasattr(pcm_buffer, 'close'):
                pcm_buffer.close()
            del st.session_state.pcm_buffer

        # Clean up streaming manager
        self.audio_service.cleanup()