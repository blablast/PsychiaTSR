"""Interface for audio buffer management."""

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class IAudioBuffer(ABC):
    """Interface for PCM audio buffer management."""

    @abstractmethod
    def put(self, samples: np.ndarray) -> None:
        """Add PCM samples to the buffer."""
        pass

    @abstractmethod
    def get(self, num_samples: int, timeout: float = 0.02) -> np.ndarray:
        """Get PCM samples from the buffer."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the buffer and clean up resources."""
        pass

    @property
    @abstractmethod
    def is_closed(self) -> bool:
        """Check if buffer is closed."""
        pass