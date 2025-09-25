"""PCM buffer implementation for audio streaming."""

import time
import queue
import threading
from dataclasses import dataclass
from typing import Optional
import numpy as np

from ..interfaces.audio_buffer_interface import IAudioBuffer

WEBRTC_SAMPLE_RATE = 48000


@dataclass
class PcmChunk:
    """Container for PCM audio samples."""
    samples: np.ndarray  # (n,), int16 mono 48kHz


class PcmBuffer(IAudioBuffer):
    """PCM buffer for WebRTC audio streaming (producer->consumer)."""

    def __init__(self, max_ms: int = 6000):
        """
        Initialize PCM buffer.

        Args:
            max_ms: Maximum buffer size in milliseconds
        """
        import collections
        self.q: queue.Queue[PcmChunk] = queue.Queue()
        self._closed = False
        self.max_samples = int(WEBRTC_SAMPLE_RATE * max_ms / 1000)
        self.total_samples = 0
        self.lock = threading.Lock()

    def put(self, samples: np.ndarray) -> None:
        """Add PCM samples to the buffer."""
        if samples.size == 0 or self._closed:
            return

        with self.lock:
            self.total_samples += samples.size

            # Remove old samples if buffer is full
            while self.total_samples > self.max_samples and not self.q.empty():
                try:
                    old = self.q.get_nowait()
                    self.total_samples -= old.samples.size
                except queue.Empty:
                    break

        self.q.put(PcmChunk(samples))

    def get(self, num_samples: int, timeout: float = 0.02) -> np.ndarray:
        """Get PCM samples from the buffer."""
        if self._closed:
            return np.zeros(num_samples, dtype=np.int16)

        out = np.empty((0,), dtype=np.int16)
        deadline = time.time() + timeout

        while out.size < num_samples and time.time() < deadline and not self._closed:
            try:
                remaining_time = deadline - time.time()
                if remaining_time <= 0:
                    break

                chunk = self.q.get(timeout=remaining_time)
                need = num_samples - out.size

                if chunk.samples.size <= need:
                    out = np.concatenate([out, chunk.samples])
                else:
                    # Use only what we need, put the rest back
                    out = np.concatenate([out, chunk.samples[:need]])
                    rest = chunk.samples[need:]
                    # Put unused samples back at the front
                    self.q.queue.appendleft(PcmChunk(rest))

            except queue.Empty:
                break

        # Pad with silence if we don't have enough samples
        if out.size < num_samples:
            pad = np.zeros((num_samples - out.size,), dtype=np.int16)
            out = np.concatenate([out, pad])

        return out

    def close(self) -> None:
        """Close the buffer and clean up resources."""
        self._closed = True

        # Clear the queue
        while not self.q.empty():
            try:
                self.q.get_nowait()
            except queue.Empty:
                break

    @property
    def is_closed(self) -> bool:
        """Check if buffer is closed."""
        return self._closed