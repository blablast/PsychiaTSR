"""Base class for TTS providers."""

from abc import ABC, abstractmethod
from typing import Union, Iterable


class BaseTTSProvider(ABC):
    """Base class for Text-to-Speech providers."""

    @abstractmethod
    def text_to_speech(self, text: str) -> Union[bytes, Iterable[bytes]]:
        """
        Convert text to speech audio.

        Args:
            text: Text to convert to speech

        Returns:
            Audio data as bytes or iterable of bytes
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the TTS provider is available and configured."""
        pass