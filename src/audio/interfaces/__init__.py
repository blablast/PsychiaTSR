"""Audio interfaces for dependency injection."""

from .audio_buffer_interface import IAudioBuffer
from .tts_router_interface import ITTSRouter
from .audio_track_interface import IAudioTrack

__all__ = ["IAudioBuffer", "ITTSRouter", "IAudioTrack"]
