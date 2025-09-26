"""Fallback audio widget when WebRTC is not available."""

import streamlit as st
import base64
import tempfile
import os
from typing import Optional


class FallbackAudioWidget:
    """Simple HTML5 audio player as fallback for WebRTC."""

    @staticmethod
    def display_info():
        """Display information about fallback audio mode."""
        st.success(
            """🎵 **HTML5 Audio aktywne**

✅ **Gotowe do słuchania!** Audio będzie odtwarzane automatycznie:
- Wygenerowane audio pojawi się pod każdą odpowiedzią
- Wbudowany player HTML5 - działa w każdej przeglądarce
- **Nie wymaga mikrofonu** - tylko słuchasz!
- Możliwość pobrania audio na dysk
        """
        )

    @staticmethod
    def play_audio_data(audio_data: bytes, voice_id: str = "unknown") -> None:
        """
        Play audio data using HTML5 audio player.

        Args:
            audio_data: Raw audio data (MP3 or WAV)
            voice_id: Voice identifier for display
        """
        if not audio_data:
            st.warning("Brak danych audio do odtworzenia")
            return

        try:
            # Encode audio data to base64 for HTML5 player
            audio_b64 = base64.b64encode(audio_data).decode("utf-8")

            # Create HTML5 audio player
            audio_html = f"""
            <div style="margin: 10px 0;">
                <p><strong>🎵 Wygenerowane audio (Voice: {voice_id})</strong></p>
                <audio controls style="width: 100%;">
                    <source src="data:audio/mpeg;base64,{audio_b64}" type="audio/mpeg">
                    Twoja przeglądarka nie obsługuje elementu audio.
                </audio>
            </div>
            """

            # Display the HTML5 player
            st.markdown(audio_html, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Błąd odtwarzania audio: {str(e)}")

    @staticmethod
    def save_and_play_temp_audio(audio_data: bytes, voice_id: str = "unknown") -> None:
        """
        Save audio to temporary file and provide download link.

        Args:
            audio_data: Raw audio data
            voice_id: Voice identifier for filename
        """
        if not audio_data:
            return

        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name

            # Provide download link
            with open(tmp_path, "rb") as audio_file:
                st.download_button(
                    label="⬇️ Pobierz audio",
                    data=audio_file.read(),
                    file_name=f"tts_response_{voice_id}.mp3",
                    mime="audio/mpeg",
                    help="Pobierz wygenerowane audio na dysk",
                )

            # Try to play inline
            FallbackAudioWidget.play_audio_data(audio_data, voice_id)

            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except Exception:
                pass  # Ignore cleanup errors

        except Exception as e:
            st.error(f"❌ Błąd zapisywania audio: {str(e)}")

    @staticmethod
    def show_browser_compatibility():
        """Show browser compatibility information for audio."""
        with st.expander("📱 Kompatybilność przeglądarek", expanded=False):
            st.markdown(
                """
            **WebRTC (najlepsze doświadczenie):**
            - ✅ Chrome 60+ (zalecane)
            - ✅ Edge 79+
            - ⚠️ Firefox 60+ (ograniczone)
            - ❌ Safari (bardzo ograniczone)

            **HTML5 Audio (tryb alternatywny):**
            - ✅ Wszystkie nowoczesne przeglądarki
            - ✅ Urządzenia mobilne
            - ⚠️ Wymaga ręcznego odtwarzania

            **Rozwiązywanie problemów:**
            1. Sprawdź czy masz najnowszą wersję przeglądarki
            2. Wyczyść cache przeglądarki
            3. Wyłącz rozszerzenia blokujące
            4. Sprawdź ustawienia audio systemu
            """
            )
