"""Interface for audio track implementations."""

from abc import ABC, abstractmethod
from typing import Any


class IAudioTrack(ABC):
    """Interface for audio track implementations (WebRTC)."""

    @abstractmethod
    async def recv(self) -> Any:
        """Receive next audio frame."""
        pass

    @property
    @abstractmethod
    def kind(self) -> str:
        """Track kind (should be 'audio')."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the audio track."""
        pass
