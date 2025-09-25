"""Command objects for section operations."""

from dataclasses import dataclass
from typing import List, Optional, Any, Dict
from datetime import datetime


@dataclass(frozen=True)
class CreateSectionCommand:
    """Command to create a new prompt section."""

    prompt_id: str
    title: str
    content: str
    position: Optional[int] = None  # None = add at end
    section_type: str = "standard"
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate command parameters."""
        if not self.title.strip():
            raise ValueError("Title cannot be empty")
        if not self.content.strip():
            raise ValueError("Content cannot be empty")
        if self.position is not None and self.position < 0:
            raise ValueError("Position must be non-negative")


@dataclass(frozen=True)
class UpdateSectionCommand:
    """Command to update existing prompt section."""

    prompt_id: str
    section_id: str
    title: Optional[str] = None
    content: Optional[str] = None
    section_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate command parameters."""
        if self.title is not None and not self.title.strip():
            raise ValueError("Title cannot be empty")
        if self.content is not None and not self.content.strip():
            raise ValueError("Content cannot be empty")

        # Must have at least one field to update
        if not any([self.title, self.content, self.section_type, self.metadata]):
            raise ValueError("At least one field must be provided for update")


@dataclass(frozen=True)
class DeleteSectionCommand:
    """Command to delete a prompt section."""

    prompt_id: str
    section_id: str


@dataclass(frozen=True)
class ReorderSectionsCommand:
    """Command to reorder sections in a prompt."""

    prompt_id: str
    section_ids: List[str]  # New order of section IDs

    def __post_init__(self):
        """Validate command parameters."""
        if not self.section_ids:
            raise ValueError("Section IDs list cannot be empty")

        if len(self.section_ids) != len(set(self.section_ids)):
            raise ValueError("Duplicate section IDs in reorder command")


@dataclass(frozen=True)
class MoveSectionCommand:
    """Command to move a section to a new position."""

    prompt_id: str
    section_id: str
    new_position: int

    def __post_init__(self):
        """Validate command parameters."""
        if self.new_position < 0:
            raise ValueError("New position must be non-negative")


@dataclass(frozen=True)
class DuplicateSectionCommand:
    """Command to duplicate an existing section."""

    prompt_id: str
    section_id: str
    new_title: Optional[str] = None  # If None, will append "(Copy)" to original
    position: Optional[int] = None   # If None, will add after original


# Command Result objects for responses

@dataclass(frozen=True)
class CommandResult:
    """Base result for command operations."""

    success: bool
    message: str
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            object.__setattr__(self, 'timestamp', datetime.now())


@dataclass(frozen=True)
class SectionCommandResult(CommandResult):
    """Result for section-specific commands."""

    section_id: Optional[str] = None
    prompt_id: Optional[str] = None
    affected_sections: Optional[List[str]] = None  # For bulk operations