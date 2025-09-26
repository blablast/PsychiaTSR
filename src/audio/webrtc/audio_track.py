"""WebRTC audio track implementation for TTS streaming."""

import asyncio
import av
from aiortc import MediaStreamTrack
from av.audio.frame import AudioFrame

from ..interfaces.audio_buffer_interface import IAudioBuffer
from ..interfaces.audio_track_interface import IAudioTrack

WEBRTC_SAMPLE_RATE = 48000
FRAME_MS = 20  # 20ms frame duration


class ElevenLabsAudioTrack(MediaStreamTrack, IAudioTrack):
    """WebRTC audio track for streaming TTS audio."""

    kind = "audio"

    def __init__(self, pcm_buffer: IAudioBuffer):
        """
        Initialize audio track.

        Args:
            pcm_buffer: PCM buffer to read audio data from
        """
        super().__init__()
        self.buffer = pcm_buffer
        self.samples_per_frame = int(WEBRTC_SAMPLE_RATE * FRAME_MS / 1000)
        self._stopped = False

    async def recv(self) -> AudioFrame:
        """Receive next audio frame for WebRTC transmission."""
        if self._stopped or self.buffer.is_closed:
            # Return silence if stopped or buffer is closed
            samples = self._create_silence_frame()
        else:
            # Get audio samples from buffer
            samples = self.buffer.get(self.samples_per_frame, timeout=0.02)

        # Create audio frame for WebRTC
        frame = self._create_audio_frame(samples)

        # Maintain proper timing (20ms per frame)
        await asyncio.sleep(FRAME_MS / 1000.0)

        return frame

    def _create_silence_frame(self) -> "AudioFrame":
        """Create a frame filled with silence."""
        import numpy as np

        silence = np.zeros((self.samples_per_frame, 1), dtype=np.int16)
        frame = av.AudioFrame.from_ndarray(silence, format="s16", layout="mono")
        frame.sample_rate = WEBRTC_SAMPLE_RATE
        return frame

    def _create_audio_frame(self, samples) -> AudioFrame:
        """
        Create AudioFrame from PCM samples.

        Args:
            samples: PCM samples as numpy array

        Returns:
            AudioFrame ready for WebRTC transmission
        """
        import numpy as np

        # Ensure we have the right shape (samples, channels)
        if samples.ndim == 1:
            samples = samples.reshape(-1, 1)

        # Ensure we have exactly the right number of samples
        if samples.shape[0] != self.samples_per_frame:
            # Pad or truncate to exact frame size
            if samples.shape[0] < self.samples_per_frame:
                # Pad with zeros
                padding = np.zeros((self.samples_per_frame - samples.shape[0], 1), dtype=np.int16)
                samples = np.vstack([samples, padding])
            else:
                # Truncate to frame size
                samples = samples[: self.samples_per_frame]

        # Create AudioFrame
        frame = av.AudioFrame.from_ndarray(samples, format="s16", layout="mono")
        frame.sample_rate = WEBRTC_SAMPLE_RATE
        return frame

    def stop(self) -> None:
        """Stop the audio track."""
        self._stopped = True
        super().stop()
