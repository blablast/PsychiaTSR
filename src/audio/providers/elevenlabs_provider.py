"""ElevenLabs TTS provider implementation."""

import os
import threading
import queue
from typing import Union, Iterable, Optional

from elevenlabs import ElevenLabs

from .base_provider import BaseTTSProvider
from ..interfaces.audio_buffer_interface import IAudioBuffer
from ..core.audio_processing import wav_iterable_to_pcm48


class TTSWorker(threading.Thread):
    """Background worker for TTS processing."""

    def __init__(self, client: ElevenLabs, voice_id: str, pcm_buffer: IAudioBuffer):
        super().__init__(daemon=True)
        self.client = client
        self.voice_id = voice_id
        self.buffer = pcm_buffer
        self.input_queue: "queue.Queue[Optional[str]]" = queue.Queue()
        self._stop_requested = False

    def submit(self, sentence: str) -> None:
        """Submit a sentence for TTS processing."""
        if not self._stop_requested:
            self.input_queue.put(sentence)

    def stop(self) -> None:
        """Stop the TTS worker."""
        self._stop_requested = True
        self.input_queue.put(None)

    def run(self) -> None:
        """Main worker loop."""
        try:
            while not self._stop_requested:
                try:
                    item = self.input_queue.get(timeout=1.0)
                    if item is None:
                        break

                    if not item.strip():
                        continue

                    # Use ElevenLabs API for TTS with PCM format
                    audio_data = self.client.text_to_speech.convert(
                        voice_id=self.voice_id,
                        model_id="eleven_flash_v2_5",  # Fast model for real-time
                        text=item,
                        output_format="pcm_48000",  # 48kHz PCM format
                    )

                    # Process PCM data directly (no WAV header)
                    for pcm_samples in self._process_pcm_data(audio_data):
                        if not self._stop_requested and pcm_samples.size > 0:
                            self.buffer.put(pcm_samples)

                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"TTS worker error: {e}")
                    # Continue processing other items

        except Exception as e:
            print(f"TTS worker fatal error: {e}")

    def _process_pcm_data(self, audio_data):
        """Process raw PCM data from ElevenLabs."""
        import numpy as np

        # PCM data is raw bytes, convert directly to numpy array
        for chunk in self._iter_chunks(audio_data):
            if chunk:
                # Convert bytes to int16 array (16-bit PCM)
                samples = np.frombuffer(chunk, dtype=np.int16)
                if samples.size > 0:
                    yield samples

    def _iter_chunks(self, obj):
        """Iterate over chunks from bytes or iterable of bytes."""
        if isinstance(obj, (bytes, bytearray)):
            yield bytes(obj)
        else:
            for chunk in obj:
                if chunk:
                    yield chunk


class ElevenLabsTTSProvider(BaseTTSProvider):
    """ElevenLabs implementation of TTS provider."""

    def __init__(self, api_key: Optional[str] = None, voice_id: str = "JBFqnCBsd6RMkjVDRZzb"):
        """
        Initialize ElevenLabs TTS provider.

        Args:
            api_key: ElevenLabs API key (if None, uses environment variable)
            voice_id: Voice ID to use for TTS
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY", "")
        self.voice_id = voice_id
        self._client = None

    @property
    def client(self) -> ElevenLabs:
        """Get or create ElevenLabs client."""
        if self._client is None:
            if not self.api_key:
                raise RuntimeError("ELEVENLABS_API_KEY is required")
            self._client = ElevenLabs(api_key=self.api_key)
        return self._client

    def text_to_speech(
        self, text: str, output_format: str = "mp3_44100_128"
    ) -> Union[bytes, Iterable[bytes]]:
        """Convert text to speech using ElevenLabs API."""
        if not text.strip():
            return b""

        try:
            # Use MP3 format for HTML5 compatibility by default
            audio_data = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                model_id="eleven_flash_v2_5",
                text=text,
                output_format=output_format,
            )

            # If audio_data is an iterator, collect all chunks
            if hasattr(audio_data, "__iter__") and not isinstance(audio_data, (bytes, bytearray)):
                audio_chunks = []
                for chunk in audio_data:
                    if chunk:
                        audio_chunks.append(chunk)
                return b"".join(audio_chunks)

            return audio_data

        except Exception as e:
            print(f"ElevenLabs TTS error: {e}")
            return b""

    def text_to_speech_pcm(self, text: str) -> Union[bytes, Iterable[bytes]]:
        """Convert text to speech in PCM format for WebRTC streaming."""
        return self.text_to_speech(text, output_format="pcm_48000")

    def is_available(self) -> bool:
        """Check if ElevenLabs TTS is available."""
        return bool(self.api_key)

    def create_worker(self, pcm_buffer: IAudioBuffer) -> TTSWorker:
        """Create a TTS worker for background processing."""
        return TTSWorker(self.client, self.voice_id, pcm_buffer)
