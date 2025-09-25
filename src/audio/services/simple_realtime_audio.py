"""Simplified real-time audio service for chunk-by-chunk TTS."""

import streamlit as st
import base64
import uuid
import time
from typing import Iterator, Optional

from ..providers.elevenlabs_provider import ElevenLabsTTSProvider


class SimpleRealtimeAudioService:
    """Simplified service for real-time audio generation and playback."""

    def __init__(self, tts_config: dict, audio_container=None):
        """Initialize with TTS configuration."""
        self.tts_config = tts_config
        self.tts_provider = ElevenLabsTTSProvider(
            api_key=tts_config.get("api_key"),
            voice_id=tts_config.get("voice_id")
        )
        self.audio_container = audio_container  # Global container for audio
        self.audio_placeholder = None
        self.chunk_buffer = ""
        self.sentence_buffer = ""
        self.chunk_count = 0
        self.audio_count = 0
        self.min_sentence_length = 100  # Minimum characters for complete sentences
        self.max_buffer_length = 400   # Maximum buffer before forced generation

    def is_available(self) -> bool:
        """Check if TTS is available."""
        return self.tts_provider.is_available()

    def initialize_audio_display(self):
        """Initialize audio display area."""
        # Use global audio container if provided
        if self.audio_container:
            with self.audio_container:
                self.audio_placeholder = st.empty()
                with self.audio_placeholder.container():
                    st.info("🎵 **Realtime Audio aktywne** - odpowiedź będzie odtwarzana podczas pisania!")
                    st.caption("Audio fragmenty będą automatycznie odtwarzane z autoplay. Po zakończeniu dostępny będzie pełny plik 🔊")
        else:
            # Fallback to creating own placeholder
            self.audio_placeholder = st.empty()
            with self.audio_placeholder.container():
                st.info("🎵 **Realtime Audio aktywne** - odpowiedź będzie odtwarzana podczas pisania!")
                st.caption("Audio fragmenty będą automatycznie odtwarzane z autoplay. Po zakończeniu dostępny będzie pełny plik 🔊")

    def process_text_chunk(self, chunk: str):
        """Process a text chunk and potentially generate audio for natural segments."""
        if not self.is_available() or not chunk:
            return

        # Add chunk to buffers
        self.chunk_buffer += chunk
        self.sentence_buffer += chunk
        self.chunk_count += 1

        # Check for natural sentence endings
        has_sentence_end = any(chunk.endswith(marker) for marker in ['.', '!', '?', ':', ';'])
        has_pause_marker = any(chunk.endswith(marker) for marker in [',', ' - ', '...'])

        # Generate conditions (more conservative for better flow)
        buffer_ready = len(self.sentence_buffer.strip()) >= self.min_sentence_length
        force_generation = len(self.sentence_buffer.strip()) >= self.max_buffer_length
        natural_break = has_sentence_end and buffer_ready
        pause_break = has_pause_marker and buffer_ready and self.chunk_count > 15

        should_generate = natural_break or force_generation or pause_break

        if should_generate and self.sentence_buffer.strip():
            self._generate_and_play_streaming_audio(self.sentence_buffer.strip())
            self.sentence_buffer = ""
            self.chunk_count = 0
            self.audio_count += 1

    def finalize_audio(self):
        """Generate audio for any remaining text and persist the final audio state."""
        if self.sentence_buffer.strip() and self.is_available():
            self._generate_and_play_streaming_audio(self.sentence_buffer.strip())
            self.sentence_buffer = ""

        # Keep audio display visible after streaming ends
        self._show_final_audio_status()

    def _show_final_audio_status(self):
        """Show final status that audio is complete and persistent."""
        if self.audio_placeholder:
            with self.audio_placeholder.container():
                st.success("🎵 **Audio zakończone** - wszystkie fragmenty wygenerowane")
                st.info("💡 Audio fragmenty zostały odtworzone automatycznie. Pełne nagranie będzie dostępne za przyciskiem 🔊 obok wiadomości.")

    def _generate_and_play_streaming_audio(self, text: str):
        """Generate and display streaming audio with HTML5 progressive loading."""
        try:
            # Generate audio
            audio_data = self.tts_provider.text_to_speech(text)
            if not audio_data:
                return

            # Display in dedicated audio area with better HTML5 streaming
            if self.audio_placeholder:
                with self.audio_placeholder.container():
                    # Create expandable section for each audio segment
                    with st.expander(f"🎵 Segment {self.audio_count + 1}: {text[:60]}{'...' if len(text) > 60 else ''}", expanded=True):
                        # Use HTML5 streaming with preload and autoplay
                        st.audio(
                            audio_data,
                            format='audio/mp3',
                            start_time=0,
                            autoplay=True
                        )

                        # Show text for reference
                        st.caption(f"**Tekst:** {text}")

                    # Log success
                    from src.ui.technical_log_display import add_technical_log
                    add_technical_log("realtime_audio", f"🎵 Segment {self.audio_count + 1}: {len(text)} znaków, {len(audio_data)} bajtów")

        except Exception as e:
            from src.ui.technical_log_display import add_technical_log
            add_technical_log("audio_error", f"❌ Błąd realtime audio: {str(e)}")

    def _generate_and_play_audio(self, text: str):
        """Generate and immediately display audio for text."""
        try:
            # Generate audio
            audio_data = self.tts_provider.text_to_speech(text)
            if not audio_data:
                return

            # Create unique key for this audio
            audio_key = f"realtime_audio_{int(time.time() * 1000)}"

            # Display audio player
            if self.audio_placeholder:
                with self.audio_placeholder.container():
                    st.success(f"🎵 **Odtwarzam:** {text[:50]}{'...' if len(text) > 50 else ''}")
                    st.audio(audio_data, format='audio/mp3', start_time=0, autoplay=True)

                    # Log success
                    from src.ui.technical_log_display import add_technical_log
                    add_technical_log("realtime_audio", f"🎵 Wygenerowano audio: {len(text)} znaków, {len(audio_data)} bajtów")

        except Exception as e:
            from src.ui.technical_log_display import add_technical_log
            add_technical_log("audio_error", f"❌ Błąd realtime audio: {str(e)}")


class RealtimeTextWrapper:
    """Wrapper for text iterator that generates audio in real-time."""

    def __init__(self, text_iterator: Iterator[str], audio_service: Optional[SimpleRealtimeAudioService] = None):
        self.text_iterator = text_iterator
        self.audio_service = audio_service
        self._initialized = False

    def __iter__(self):
        return self

    def __next__(self):
        try:
            # Initialize audio on first chunk
            if not self._initialized and self.audio_service:
                self.audio_service.initialize_audio_display()
                self._initialized = True

            # Get next chunk
            chunk = next(self.text_iterator)

            # Process chunk for audio
            if self.audio_service:
                self.audio_service.process_text_chunk(chunk)

            return chunk

        except StopIteration:
            # Finalize any remaining audio
            if self.audio_service:
                self.audio_service.finalize_audio()
            raise


def create_realtime_audio_wrapper(
    text_iterator: Iterator[str],
    tts_config: Optional[dict] = None,
    audio_container=None
) -> Iterator[str]:
    """
    Create a text iterator wrapper that generates audio in real-time.

    Args:
        text_iterator: Original text iterator
        tts_config: TTS configuration
        audio_container: Streamlit container for audio display

    Returns:
        Wrapped iterator that generates audio for chunks
    """
    audio_service = None

    # Only create audio service if enabled and configured
    if (tts_config and
        st.session_state.get("audio_enabled", False) and
        st.session_state.get("fallback_mode", True)):

        try:
            audio_service = SimpleRealtimeAudioService(tts_config, audio_container)
            if audio_service.is_available():
                from src.ui.technical_log_display import add_technical_log
                add_technical_log("realtime_audio", "🎵 Realtime audio service zainicjalizowany")
            else:
                audio_service = None
        except Exception as e:
            from src.ui.technical_log_display import add_technical_log
            add_technical_log("audio_error", f"❌ Błąd inicjalizacji realtime audio: {str(e)}")
            audio_service = None

    return RealtimeTextWrapper(text_iterator, audio_service)