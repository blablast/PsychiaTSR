"""PromptTemplate aggregate root for managing prompt sections."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from .prompt_section import PromptSection
from .section_order import SectionOrder


@dataclass
class PromptTemplate:
    """
    Aggregate root for prompt templates.

    Manages prompt sections and maintains consistency.
    """

    id: str
    agent_type: str  # therapist, supervisor
    prompt_type: str  # system, stage
    stage_id: Optional[str] = None  # for stage prompts
    sections: List[PromptSection] = None
    metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize aggregate after construction."""
        if self.sections is None:
            self.sections = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

        self._validate()

    def _validate(self):
        """Validate template invariants."""
        if not self.agent_type:
            raise ValueError("Agent type is required")

        if not self.prompt_type:
            raise ValueError("Prompt type is required")

        if self.prompt_type not in ["system", "stage"]:
            raise ValueError("Prompt type must be 'system' or 'stage'")

        if self.prompt_type == "stage" and not self.stage_id:
            raise ValueError("Stage ID required for stage prompts")

        # Validate section order consistency
        expected_orders = list(range(len(self.sections)))
        actual_orders = sorted([s.order for s in self.sections])
        if actual_orders != expected_orders:
            raise ValueError("Section orders must be consecutive starting from 0")

    @classmethod
    def create_new(
        cls, agent_type: str, prompt_type: str, stage_id: str = None
    ) -> "PromptTemplate":
        """
        Create a new prompt template with generated ID and timestamps.

        Args:
            agent_type: Type of agent (therapist, supervisor)
            prompt_type: Type of prompt (system, stage)
            stage_id: Stage identifier for stage prompts

        Returns:
            New PromptTemplate instance
        """
        return cls(
            id=str(uuid.uuid4()),
            agent_type=agent_type,
            prompt_type=prompt_type,
            stage_id=stage_id,
            sections=[],
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def add_section(
        self, title: str, content: str, section_type: str = "standard"
    ) -> PromptSection:
        """
        Add new section to template.

        Args:
            title: Section title
            content: Section content
            section_type: Type of section

        Returns:
            The newly created section
        """
        next_order = len(self.sections)
        section = PromptSection.create_new(title, content, next_order, section_type)

        self.sections.append(section)
        self.updated_at = datetime.now()

        return section

    def update_section(
        self, section_id: str, title: str = None, content: str = None
    ) -> PromptSection:
        """
        Update existing section.

        Args:
            section_id: ID of section to update
            title: New title (optional)
            content: New content (optional)

        Returns:
            The updated section

        Raises:
            ValueError: If section not found
        """
        section_index = self._find_section_index(section_id)
        if section_index is None:
            raise ValueError(f"Section {section_id} not found")

        old_section = self.sections[section_index]
        updated_section = old_section.update_content(title, content)

        self.sections[section_index] = updated_section
        self.updated_at = datetime.now()

        return updated_section

    def remove_section(self, section_id: str) -> bool:
        """
        Remove section from template.

        Args:
            section_id: ID of section to remove

        Returns:
            True if section was removed, False if not found
        """
        section_index = self._find_section_index(section_id)
        if section_index is None:
            return False

        # Remove section
        self.sections.pop(section_index)

        # Reorder remaining sections
        self._reorder_sections()
        self.updated_at = datetime.now()

        return True

    def reorder_sections(self, new_order: SectionOrder) -> None:
        """
        Reorder sections according to new ordering.

        Args:
            new_order: New section ordering

        Raises:
            ValueError: If ordering is invalid
        """
        # Validate that all sections are included
        section_ids = {s.id for s in self.sections}
        order_ids = set(new_order.section_ids)

        if section_ids != order_ids:
            raise ValueError("Section order must include all sections")

        # Apply new ordering
        self.sections = new_order.apply_to_sections(self.sections)
        self.updated_at = datetime.now()

    def move_section(self, section_id: str, new_position: int) -> None:
        """
        Move section to new position.

        Args:
            section_id: ID of section to move
            new_position: New position (0-indexed)

        Raises:
            ValueError: If section not found or position invalid
        """
        if new_position < 0 or new_position >= len(self.sections):
            raise ValueError(f"Invalid position {new_position}")

        section_index = self._find_section_index(section_id)
        if section_index is None:
            raise ValueError(f"Section {section_id} not found")

        # Move section
        section = self.sections.pop(section_index)
        self.sections.insert(new_position, section)

        # Reorder
        self._reorder_sections()
        self.updated_at = datetime.now()

    def get_section(self, section_id: str) -> Optional[PromptSection]:
        """Get section by ID."""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

    def get_sections_ordered(self) -> List[PromptSection]:
        """Get sections in display order."""
        return sorted(self.sections, key=lambda s: s.order)

    def generate_prompt_text(self) -> str:
        """
        Generate complete prompt text from all sections.

        Returns:
            Complete prompt text with sections in order
        """
        ordered_sections = self.get_sections_ordered()
        section_texts = []

        for section in ordered_sections:
            if section.title and section.content:
                section_texts.append(f"{section.title}:\n{section.content}")

        return "\n\n".join(section_texts)

    def get_statistics(self) -> Dict[str, Any]:
        """Get template statistics."""
        total_chars = sum(s.get_char_count() for s in self.sections)
        total_words = sum(s.get_word_count() for s in self.sections)

        return {
            "section_count": len(self.sections),
            "total_characters": total_chars,
            "total_words": total_words,
            "average_section_length": total_chars // len(self.sections) if self.sections else 0,
            "empty_sections": sum(1 for s in self.sections if s.is_empty()),
        }

    def _find_section_index(self, section_id: str) -> Optional[int]:
        """Find index of section by ID."""
        for i, section in enumerate(self.sections):
            if section.id == section_id:
                return i
        return None

    def _reorder_sections(self) -> None:
        """Reorder sections to have consecutive orders starting from 0."""
        for i, section in enumerate(self.sections):
            if section.order != i:
                self.sections[i] = section.change_order(i)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "prompt_type": self.prompt_type,
            "stage_id": self.stage_id,
            "sections": [s.to_dict() for s in self.sections],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptTemplate":
        """Create from dictionary."""
        sections = [PromptSection.from_dict(s) for s in data.get("sections", [])]

        created_at = None
        updated_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        return cls(
            id=data["id"],
            agent_type=data["agent_type"],
            prompt_type=data["prompt_type"],
            stage_id=data.get("stage_id"),
            sections=sections,
            metadata=data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at,
        )
