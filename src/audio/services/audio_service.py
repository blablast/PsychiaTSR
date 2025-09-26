"""Main audio service for PsychiaTSR integration."""

from typing import Optional, Dict, Any
import os

from ..core.pcm_buffer import PcmBuffer
from ..providers.elevenlabs_provider import ElevenLabsTTSProvider
from ..webrtc.streaming_manager import AudioStreamingManager
from ..webrtc.audio_track import ElevenLabsAudioTrack
from .tts_router_service import TTSRouterService


class AudioService:
    """Main service for audio functionality integration."""

    def __init__(self):
        """Initialize the audio service."""
        self.streaming_manager = AudioStreamingManager()

    def create_pcm_buffer(self, max_ms: int = 6000) -> PcmBuffer:
        """
        Create a new PCM buffer for audio streaming.

        Args:
            max_ms: Maximum buffer size in milliseconds

        Returns:
            New PCM buffer instance
        """
        return PcmBuffer(max_ms=max_ms)

    def create_tts_router(
        self, config: Dict[str, Any], pcm_buffer: PcmBuffer
    ) -> Optional[TTSRouterService]:
        """
        Create TTS router from configuration.

        Args:
            config: Configuration dictionary with 'api_key' and 'voice_id'
            pcm_buffer: PCM buffer for audio output

        Returns:
            TTS router service or None if configuration is invalid
        """
        try:
            api_key = config.get("api_key")
            voice_id = config.get("voice_id", "JBFqnCBsd6RMkjVDRZzb")

            if not api_key:
                return None

            # Create TTS provider
            tts_provider = ElevenLabsTTSProvider(api_key=api_key, voice_id=voice_id)

            if not tts_provider.is_available():
                return None

            # Create and return router service
            return TTSRouterService(tts_provider, pcm_buffer)

        except Exception as e:
            print(f"Failed to create TTS router: {e}")
            return None

    def create_audio_track(self, pcm_buffer: PcmBuffer) -> ElevenLabsAudioTrack:
        """
        Create WebRTC audio track for streaming.

        Args:
            pcm_buffer: PCM buffer to stream from

        Returns:
            WebRTC audio track
        """
        return self.streaming_manager.create_audio_track(pcm_buffer)

    def get_webrtc_config(self) -> Dict[str, Any]:
        """Get WebRTC configuration for streamlit-webrtc."""
        return self.streaming_manager.get_webrtc_config()

    def is_audio_enabled(self, session_state) -> bool:
        """
        Check if audio is enabled in session state.

        Args:
            session_state: Streamlit session state

        Returns:
            True if audio is enabled and configured
        """
        return (
            getattr(session_state, "audio_enabled", False)
            and hasattr(session_state, "_tts_cfg")
            and bool(session_state._tts_cfg)
        )

    def cleanup(self) -> None:
        """Clean up audio resources."""
        self.streaming_manager.cleanup()

    @staticmethod
    def get_default_voice_id() -> str:
        """Get default ElevenLabs voice ID."""
        return "lxYfHSkYm1EzQzGhdbfc"

    @staticmethod
    def get_api_key_from_env() -> str:
        """Get ElevenLabs API key from environment."""
        return os.getenv("ELEVENLABS_API_KEY", "")
