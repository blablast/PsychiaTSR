"""PromptSection Value Object representing a single section of a prompt."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import uuid
from datetime import datetime


@dataclass(frozen=True)
class PromptSection:
    """
    Value Object representing a single section of a prompt.

    Features:
    - Immutable (frozen=True)
    - Self-validating
    - Rich behavior methods
    """

    id: str
    title: str
    content: str
    order: int
    section_type: str = "standard"  # standard, conditional, dynamic
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate invariants after construction."""
        self._validate()

    def _validate(self):
        """Validate section invariants."""
        if not self.title or not self.title.strip():
            raise ValueError("Section title cannot be empty")

        if not self.content or not self.content.strip():
            raise ValueError("Section content cannot be empty")

        if self.order < 0:
            raise ValueError("Section order must be non-negative")

        if len(self.title) > 100:
            raise ValueError("Section title too long (max 100 chars)")

        if len(self.content) > 5000:
            raise ValueError("Section content too long (max 5000 chars)")

    @classmethod
    def create_new(
        cls, title: str, content: str, order: int, section_type: str = "standard"
    ) -> "PromptSection":
        """
        Create a new section with generated ID and timestamps.

        Args:
            title: Section title
            content: Section content
            order: Display order
            section_type: Type of section

        Returns:
            New PromptSection instance
        """
        now = datetime.now()

        return cls(
            id=str(uuid.uuid4()),
            title=title.strip(),
            content=content.strip(),
            order=order,
            section_type=section_type,
            metadata={},
            created_at=now,
            updated_at=now,
        )

    def update_content(self, new_title: str = None, new_content: str = None) -> "PromptSection":
        """
        Create updated version of section (immutable).

        Args:
            new_title: New title (optional)
            new_content: New content (optional)

        Returns:
            New PromptSection with updated content
        """
        return PromptSection(
            id=self.id,
            title=new_title.strip() if new_title else self.title,
            content=new_content.strip() if new_content else self.content,
            order=self.order,
            section_type=self.section_type,
            metadata=self.metadata,
            created_at=self.created_at,
            updated_at=datetime.now(),
        )

    def change_order(self, new_order: int) -> "PromptSection":
        """
        Create section with new order (immutable).

        Args:
            new_order: New display order

        Returns:
            New PromptSection with updated order
        """
        return PromptSection(
            id=self.id,
            title=self.title,
            content=self.content,
            order=new_order,
            section_type=self.section_type,
            metadata=self.metadata,
            created_at=self.created_at,
            updated_at=datetime.now(),
        )

    def is_empty(self) -> bool:
        """Check if section has meaningful content."""
        return not (self.title.strip() and self.content.strip())

    def get_word_count(self) -> int:
        """Get approximate word count of content."""
        return len(self.content.split())

    def get_char_count(self) -> int:
        """Get character count of content."""
        return len(self.content)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "order": self.order,
            "section_type": self.section_type,
            "metadata": self.metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptSection":
        """Create from dictionary (for deserialization)."""
        created_at = None
        updated_at = None

        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            order=data["order"],
            section_type=data.get("section_type", "standard"),
            metadata=data.get("metadata"),
            created_at=created_at,
            updated_at=updated_at,
        )

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"PromptSection(id='{self.id[:8]}...', title='{self.title}', order={self.order})"
