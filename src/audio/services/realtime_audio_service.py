"""Realtime audio service for integrating streaming TTS with text streaming."""

import asyncio
import threading
from typing import AsyncIterator, Iterator, Optional
import queue
import streamlit as st

from ..providers.elevenlabs_streaming_provider import (
    ElevenLabsStreamingProvider,
    StreamingAudioManager,
)


class RealtimeAudioService:
    """Service for handling real-time audio streaming during text streaming."""

    def __init__(self, tts_config: dict):
        """
        Initialize realtime audio service.

        Args:
            tts_config: Configuration with api_key and voice_id
        """
        self.tts_config = tts_config
        self.streaming_provider = ElevenLabsStreamingProvider(
            api_key=tts_config.get("api_key"), voice_id=tts_config.get("voice_id")
        )
        self.audio_manager = StreamingAudioManager()
        self._active_tasks = []

    def is_available(self) -> bool:
        """Check if realtime audio is available."""
        return self.streaming_provider.is_available()

    def start_streaming_audio(self, text_stream: Iterator[str]) -> str:
        """
        Start streaming audio generation from text stream.

        Args:
            text_stream: Iterator of text chunks from therapist response

        Returns:
            Queue ID for tracking this audio stream
        """
        if not self.is_available():
            return ""

        # Clear previous queue
        self.audio_manager.clear_queue()

        # Start background task for streaming
        self._start_background_streaming(text_stream)

        return self.audio_manager.get_audio_queue_id()

    def render_audio_player(self):
        """Render the JavaScript audio player component."""
        # Create placeholder for dynamic updates
        if "audio_player_placeholder" not in st.session_state:
            st.session_state.audio_player_placeholder = st.empty()

        # Render player with current queue data
        with st.session_state.audio_player_placeholder.container():
            self.audio_manager.render_streaming_audio_player()

    def _start_background_streaming(self, text_stream: Iterator[str]):
        """Start background thread for audio streaming."""

        def background_task():
            try:
                # Create async text stream from sync iterator
                async def async_text_stream():
                    for chunk in text_stream:
                        yield chunk
                        await asyncio.sleep(0.01)  # Small delay for responsiveness

                # Run the streaming in event loop
                asyncio.run(self._process_streaming_audio(async_text_stream()))

            except Exception as e:
                print(f"Background streaming error: {e}")

        # Start background thread
        thread = threading.Thread(target=background_task, daemon=True)
        thread.start()
        self._active_tasks.append(thread)

    async def _process_streaming_audio(self, text_stream: AsyncIterator[str]):
        """Process streaming audio generation."""
        try:
            chunk_count = 0
            async for audio_chunk in self.streaming_provider.stream_text_to_speech(text_stream):
                if audio_chunk:
                    chunk_id = self.audio_manager.add_audio_chunk(audio_chunk)
                    chunk_count += 1

                    # Force Streamlit rerun to update session state
                    if chunk_count % 3 == 0:  # Every 3rd chunk to avoid too many reruns
                        self._trigger_streamlit_rerun()

        except Exception as e:
            print(f"Streaming audio processing error: {e}")

    def _trigger_streamlit_rerun(self):
        """Trigger a Streamlit rerun to update session state."""
        try:
            # Update the audio player placeholder with new queue data
            if "audio_player_placeholder" in st.session_state:
                with st.session_state.audio_player_placeholder.container():
                    self.audio_manager.render_streaming_audio_player()
        except Exception:
            # Silent fail - rerun might not be available in all contexts
            pass

    def cleanup(self):
        """Clean up active streaming tasks."""
        self.audio_manager.clear_queue()
        self._active_tasks.clear()


class StreamingTextWrapper:
    """Wrapper for text streaming that also feeds to audio streaming."""

    def __init__(
        self, text_iterator: Iterator[str], audio_service: Optional[RealtimeAudioService] = None
    ):
        """
        Initialize wrapper.

        Args:
            text_iterator: Original text iterator
            audio_service: Optional audio service for streaming
        """
        self.text_iterator = text_iterator
        self.audio_service = audio_service
        self._text_buffer = queue.Queue()
        self._audio_started = False

    def __iter__(self):
        return self

    def __next__(self):
        try:
            # Get next text chunk
            chunk = next(self.text_iterator)

            # Start audio streaming on first chunk
            if not self._audio_started and self.audio_service and self.audio_service.is_available():
                self._start_audio_streaming()
                self._audio_started = True

            # Add chunk to audio buffer
            if self._audio_started:
                self._text_buffer.put(chunk)

            return chunk

        except StopIteration:
            # Signal end of text stream to audio
            if self._audio_started:
                self._text_buffer.put(None)  # End marker
            raise

    def _start_audio_streaming(self):
        """Start audio streaming with buffered text."""

        def text_generator():
            while True:
                try:
                    chunk = self._text_buffer.get(timeout=0.1)
                    if chunk is None:  # End marker
                        break
                    yield chunk
                except queue.Empty:
                    continue

        # Start streaming audio
        self.audio_service.start_streaming_audio(text_generator())


def create_streaming_text_with_audio(
    text_iterator: Iterator[str], tts_config: Optional[dict] = None
) -> Iterator[str]:
    """
    Create a text iterator that also streams audio in real-time.

    Args:
        text_iterator: Original text iterator from therapist response
        tts_config: TTS configuration (api_key, voice_id)

    Returns:
        Text iterator that also triggers audio streaming
    """
    audio_service = None

    # Create audio service if config provided and audio enabled
    if (
        tts_config
        and st.session_state.get("audio_enabled", False)
        and st.session_state.get("fallback_mode", True)
    ):

        try:
            audio_service = RealtimeAudioService(tts_config)

            # Render the audio player component
            audio_service.render_audio_player()

        except Exception as e:
            print(f"Failed to create audio service: {e}")
            audio_service = None

    # Return wrapped iterator
    return StreamingTextWrapper(text_iterator, audio_service)
