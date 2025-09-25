"""Sentence splitting for TTS processing."""

from typing import List


class SentenceSplitter:
    """Splits streaming text into complete sentences for TTS processing."""

    def __init__(self):
        """Initialize the sentence splitter."""
        self.buffer = ""
        self.sentence_enders = ".?!…"

    def feed(self, text_piece: str) -> List[str]:
        """
        Feed a piece of text and get complete sentences.

        Args:
            text_piece: New text to process

        Returns:
            List of complete sentences ready for TTS
        """
        self.buffer += text_piece
        sentences = []
        last_sentence_end = 0

        for i, char in enumerate(self.buffer):
            if char in self.sentence_enders:
                # Look ahead for whitespace after sentence ender
                j = i + 1
                while j < len(self.buffer) and self.buffer[j].isspace():
                    j += 1

                # Extract complete sentence including trailing whitespace
                sentence = self.buffer[last_sentence_end:j].strip()
                if sentence:
                    sentences.append(sentence)

                last_sentence_end = j

        # Keep unprocessed text in buffer
        if sentences:
            self.buffer = self.buffer[last_sentence_end:]

        return sentences

    def flush(self) -> List[str]:
        """
        Get any remaining text as final sentence.

        Returns:
            List containing remaining text as final sentence (if any)
        """
        if self.buffer.strip():
            final_sentence = self.buffer.strip()
            self.buffer = ""
            return [final_sentence]
        return []