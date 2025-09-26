"""Interface for TTS routing and processing."""

from abc import ABC, abstractmethod


class ITTSRouter(ABC):
    """Interface for text-to-speech routing and processing."""

    @abstractmethod
    def feed(self, text_piece: str) -> None:
        """Feed a piece of text to be converted to speech."""
        pass

    @abstractmethod
    def flush_and_close(self) -> None:
        """Flush remaining text and close the router."""
        pass

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """Check if the router is actively processing."""
        pass
