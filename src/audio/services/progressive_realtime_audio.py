"""Progressive real-time audio service with single continuous player."""

import streamlit as st
import base64
import time
from typing import Iterator, Optional
import io

from ..providers.elevenlabs_provider import ElevenLabsTTSProvider


class ProgressiveRealtimeAudioService:
    """Service that builds audio progressively as text streams."""

    def __init__(self, tts_config: dict, audio_container=None):
        """Initialize with TTS configuration."""
        self.tts_config = tts_config
        self.tts_provider = ElevenLabsTTSProvider(
            api_key=tts_config.get("api_key"), voice_id=tts_config.get("voice_id")
        )
        self.audio_container = audio_container
        self.audio_placeholder = None

        # Text accumulation
        self.full_text = ""
        self.last_generated_length = 0
        self.pending_text = ""

        # Audio generation thresholds
        self.min_segment_length = 150  # Generate audio for segments of 150+ chars
        self.sentence_endings = [".", "!", "?", ":", ";"]

        # Audio segments
        self.audio_segments = []
        self.segment_count = 0

    def is_available(self) -> bool:
        """Check if TTS is available."""
        return self.tts_provider.is_available()

    def initialize_audio_display(self):
        """Initialize audio display area."""
        if self.audio_container:
            with self.audio_container:
                self.audio_placeholder = st.empty()
                with self.audio_placeholder.container():
                    st.success("🎵 **Progressive Audio streaming** - naturalny przepływ audio")
                    st.caption("Audio będzie generowane dla całych zdań i automatycznie odtwarzane")
        else:
            self.audio_placeholder = st.empty()
            with self.audio_placeholder.container():
                st.success("🎵 **Progressive Audio streaming** - naturalny przepływ audio")

    def process_text_chunk(self, chunk: str):
        """Process text chunk and generate audio for complete sentences."""
        if not self.is_available() or not chunk:
            return

        # Add to full text and pending text
        self.full_text += chunk
        self.pending_text += chunk

        # Check if we have a complete sentence or enough text
        should_generate = self._should_generate_audio(chunk)

        if should_generate and self.pending_text.strip():
            self._generate_progressive_audio(self.pending_text.strip())
            self.last_generated_length = len(self.full_text)
            self.pending_text = ""

    def _should_generate_audio(self, chunk: str) -> bool:
        """Determine if we should generate audio now."""
        # Check for natural sentence endings
        has_sentence_ending = any(chunk.endswith(ending) for ending in self.sentence_endings)

        # Check text length
        text_ready = len(self.pending_text.strip()) >= self.min_segment_length

        # Generate on sentence ending + minimum length, or when text gets too long
        return (has_sentence_ending and text_ready) or len(self.pending_text.strip()) >= 300

    def _generate_progressive_audio(self, text: str):
        """Generate audio for text segment and add to progressive player."""
        try:
            # Generate audio
            audio_data = self.tts_provider.text_to_speech(text)
            if not audio_data:
                return

            self.segment_count += 1
            self.audio_segments.append(
                {"text": text, "audio_data": audio_data, "segment_id": self.segment_count}
            )

            # Update the display with new segment
            self._update_progressive_display()

            # Log success
            from src.ui.technical_log_display import add_technical_log

            add_technical_log(
                "progressive_audio", f"🎵 Generated segment {self.segment_count}: {len(text)} chars"
            )

        except Exception as e:
            from src.ui.technical_log_display import add_technical_log

            add_technical_log("audio_error", f"❌ Progressive audio error: {str(e)}")

    def _update_progressive_display(self):
        """Update the progressive audio display."""
        if not self.audio_placeholder:
            return

        with self.audio_placeholder.container():
            st.success(f"🎵 **Audio Streaming** - {self.segment_count} segmentów wygenerowanych")

            # Show only the last few segments to avoid UI bloat
            recent_segments = self.audio_segments[-3:]  # Last 3 segments

            for segment in recent_segments:
                segment_id = segment["segment_id"]
                text = segment["text"]
                audio_data = segment["audio_data"]

                # Create compact display for each segment
                st.markdown(
                    f"**Segment {segment_id}:** *{text[:80]}{'...' if len(text) > 80 else ''}*"
                )
                st.audio(
                    audio_data, format="audio/mp3", autoplay=(segment_id == self.segment_count)
                )

            if len(self.audio_segments) > 3:
                st.caption(f"+ {len(self.audio_segments) - 3} wcześniejszych segmentów")

    def finalize_audio(self):
        """Generate audio for any remaining text."""
        if self.pending_text.strip() and self.is_available():
            self._generate_progressive_audio(self.pending_text.strip())
            self.pending_text = ""

        # Show final status
        self._show_final_status()

    def _show_final_status(self):
        """Show completion status."""
        if self.audio_placeholder:
            with self.audio_placeholder.container():
                st.success(
                    f"🎵 **Audio kompletne** - {self.segment_count} segmentów wygenerowanych"
                )
                st.info(
                    "💡 Wszystkie segmenty audio zostały automatycznie odtworzone. Pełne nagranie dostępne za przyciskiem 🔊"
                )

                # Optionally show all segments in collapsed form
                with st.expander(
                    f"📋 Zobacz wszystkie {self.segment_count} segmentów", expanded=False
                ):
                    for i, segment in enumerate(self.audio_segments, 1):
                        st.markdown(f"**{i}.** {segment['text']}")


class ProgressiveTextWrapper:
    """Wrapper for progressive audio processing."""

    def __init__(
        self,
        text_iterator: Iterator[str],
        audio_service: Optional[ProgressiveRealtimeAudioService] = None,
    ):
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


def create_progressive_audio_wrapper(
    text_iterator: Iterator[str], tts_config: Optional[dict] = None, audio_container=None
) -> Iterator[str]:
    """
    Create a progressive audio wrapper that builds audio naturally.

    Args:
        text_iterator: Original text iterator
        tts_config: TTS configuration
        audio_container: Streamlit container for audio

    Returns:
        Wrapped iterator with progressive audio
    """
    audio_service = None

    if (
        tts_config
        and st.session_state.get("audio_enabled", False)
        and st.session_state.get("fallback_mode", True)
    ):

        try:
            audio_service = ProgressiveRealtimeAudioService(tts_config, audio_container)
            if audio_service.is_available():
                from src.ui.technical_log_display import add_technical_log

                add_technical_log("progressive_audio", "🎵 Progressive audio service initialized")
            else:
                audio_service = None
        except Exception as e:
            from src.ui.technical_log_display import add_technical_log

            add_technical_log("audio_error", f"❌ Progressive audio init error: {str(e)}")
            audio_service = None

    return ProgressiveTextWrapper(text_iterator, audio_service)
