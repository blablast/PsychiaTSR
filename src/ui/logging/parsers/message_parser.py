"""Message parser - eliminates parsing redundancy across different message types."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ParsedMessage:
    """Unified parsed message structure."""

    message_type: str  # 'enhanced_prompt', 'standard', 'json'
    header: str
    full_content: Optional[str] = None
    compact_info: Optional[str] = None
    raw_data: str = ""


class MessageParser:
    """Unified message parser - eliminates duplicate parsing logic."""

    # Enhanced prompt patterns - configuration driven
    ENHANCED_PROMPT_PATTERNS = [
        "📝 SUPERVISOR PROMPT -",
        "📝 THERAPIST PROMPT -",
        "📝 SYSTEM PROMPT -",
        "📝 STAGE PROMPT -",
    ]

    def parse(self, data: str) -> ParsedMessage:
        """
        Parse message data into unified structure.

        Single method replaces multiple parsing implementations.
        """
        if self._is_enhanced_prompt(data):
            return self._parse_enhanced_prompt(data)
        elif self._is_json_only(data):
            return self._parse_json(data)
        else:
            return self._parse_standard(data)

    def _is_enhanced_prompt(self, data: str) -> bool:
        """Check if data is enhanced prompt format."""
        return any(pattern in data for pattern in self.ENHANCED_PROMPT_PATTERNS)

    def _is_json_only(self, data: str) -> bool:
        """Check if data is pure JSON."""
        data = data.strip()
        return data.startswith("{") and data.endswith("}")

    def _parse_enhanced_prompt(self, data: str) -> ParsedMessage:
        """Parse enhanced prompt format (📝 PROMPT - ...)."""
        lines = data.split("\n")
        header_line = lines[0] if lines else data

        # Extract prompt type for compact info
        prompt_type = "PROMPT"
        for pattern in self.ENHANCED_PROMPT_PATTERNS:
            if pattern in header_line:
                # Extract type: "📝 SUPERVISOR PROMPT -" -> "SUPERVISOR"
                prompt_type = pattern.replace("📝 ", "").replace(" -", "").replace(" PROMPT", "")
                break

        # Extract full content
        full_content = ""
        in_full_content = False

        for line in lines[1:]:  # Skip header line
            if line.startswith("Full content:"):
                full_content = line.replace("Full content:", "").strip()
                in_full_content = True
            elif in_full_content:
                full_content += "\n" + line

        # Create compact info
        content_length = len(full_content) if full_content else 0
        compact_info = (
            f"{prompt_type} • {content_length} chars" if content_length > 0 else prompt_type
        )

        return ParsedMessage(
            message_type="enhanced_prompt",
            header=header_line,
            full_content=full_content,
            compact_info=compact_info,
            raw_data=data,
        )

    def _parse_json(self, data: str) -> ParsedMessage:
        """Parse pure JSON data."""
        return ParsedMessage(
            message_type="json", header="JSON Data", full_content=data, raw_data=data
        )

    def _parse_standard(self, data: str) -> ParsedMessage:
        """Parse standard message format."""
        lines = data.split("\n", 1)
        header = lines[0] if lines else data
        content = lines[1] if len(lines) > 1 else ""

        return ParsedMessage(
            message_type="standard",
            header=header,
            full_content=content if content.strip() else None,
            raw_data=data,
        )
