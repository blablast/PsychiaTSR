"""Audio streaming manager for WebRTC integration."""

from typing import Optional, Dict, Any

from ..interfaces.audio_buffer_interface import IAudioBuffer
from .audio_track import ElevenLabsAudioTrack


class AudioStreamingManager:
    """Manages WebRTC audio streaming configuration and lifecycle."""

    def __init__(self):
        """Initialize the streaming manager."""
        self._active_track: Optional[ElevenLabsAudioTrack] = None
        self._buffer: Optional[IAudioBuffer] = None

    def create_audio_track(self, pcm_buffer: IAudioBuffer) -> ElevenLabsAudioTrack:
        """
        Create a new audio track for WebRTC streaming.

        Args:
            pcm_buffer: PCM buffer to stream from

        Returns:
            WebRTC audio track
        """
        # Stop any existing track
        self.stop_current_track()

        # Create new track
        self._active_track = ElevenLabsAudioTrack(pcm_buffer)
        self._buffer = pcm_buffer

        return self._active_track

    def stop_current_track(self) -> None:
        """Stop the currently active audio track."""
        if self._active_track:
            self._active_track.stop()
            self._active_track = None

        if self._buffer:
            self._buffer.close()
            self._buffer = None

    def get_webrtc_config(self) -> Dict[str, Any]:
        """
        Get WebRTC configuration for streamlit-webrtc.

        Returns:
            Configuration dictionary for webrtc_streamer
        """
        return {
            "mode": "RECVONLY",  # Changed to RECVONLY - we only want to play audio
            # No media constraints needed for RECVONLY - we don't access user's mic
            "media_stream_constraints": None,
            "rtc_configuration": {
                "iceServers": [
                    {"urls": ["stun:stun.l.google.com:19302"]},
                    {"urls": ["stun:stun1.l.google.com:19302"]},
                ]
            },
            "sendback_audio": False,  # We're only receiving/playing, not sending
            "audio_frame_callback": None,  # We'll handle audio differently
        }

    @property
    def is_streaming(self) -> bool:
        """Check if audio streaming is currently active."""
        return self._active_track is not None and not self._active_track._stopped

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_current_track()
