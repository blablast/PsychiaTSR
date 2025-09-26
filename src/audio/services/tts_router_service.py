"""TTS Router service implementation."""

from typing import Optional

from ..interfaces.tts_router_interface import ITTSRouter
from ..interfaces.audio_buffer_interface import IAudioBuffer
from ..providers.elevenlabs_provider import ElevenLabsTTSProvider, TTSWorker
from ..core.sentence_splitter import SentenceSplitter


class TTSRouterService(ITTSRouter):
    """
    TTS Router service that converts streaming text to speech.

    Handles sentence splitting and routes complete sentences to TTS provider.
    """

    def __init__(self, tts_provider: ElevenLabsTTSProvider, pcm_buffer: IAudioBuffer):
        """
        Initialize TTS router.

        Args:
            tts_provider: TTS provider for speech synthesis
            pcm_buffer: Buffer to store generated audio
        """
        self.tts_provider = tts_provider
        self.pcm_buffer = pcm_buffer
        self.sentence_splitter = SentenceSplitter()
        self.tts_worker: Optional[TTSWorker] = None
        self._is_active = False

    def start(self) -> None:
        """Start the TTS processing."""
        if not self._is_active and self.tts_provider.is_available():
            self.tts_worker = self.tts_provider.create_worker(self.pcm_buffer)
            self.tts_worker.start()
            self._is_active = True

    def feed(self, text_piece: str) -> None:
        """Feed a piece of text to be converted to speech."""
        if not self._is_active:
            self.start()

        if not self.tts_worker:
            return

        # Split text into complete sentences
        sentences = self.sentence_splitter.feed(text_piece)

        # Submit complete sentences for TTS processing
        for sentence in sentences:
            if sentence.strip():
                self.tts_worker.submit(sentence)

    def flush_and_close(self) -> None:
        """Flush remaining text and close the router."""
        if not self.tts_worker:
            return

        # Process any remaining text as final sentence
        final_sentences = self.sentence_splitter.flush()
        for sentence in final_sentences:
            if sentence.strip():
                self.tts_worker.submit(sentence)

        # Stop the worker
        self.tts_worker.stop()
        self.tts_worker.join(timeout=5.0)  # Wait up to 5 seconds

        self._is_active = False
        self.tts_worker = None

    @property
    def is_active(self) -> bool:
        """Check if the router is actively processing."""
        return self._is_active and self.tts_worker is not None
