"""SectionOrder Value Object for managing section ordering."""

from dataclasses import dataclass
from typing import List, Dict
from .prompt_section import PromptSection


@dataclass(frozen=True)
class SectionOrder:
    """
    Value Object for managing section ordering operations.

    Encapsulates ordering logic and validation for prompt sections.
    """

    section_ids: tuple[str, ...]  # Immutable sequence

    def __post_init__(self):
        """Validate ordering invariants."""
        if len(self.section_ids) != len(set(self.section_ids)):
            raise ValueError("Duplicate section IDs in order")

    @classmethod
    def from_sections(cls, sections: List[PromptSection]) -> "SectionOrder":
        """Create order from list of sections."""
        sorted_sections = sorted(sections, key=lambda s: s.order)
        section_ids = tuple(s.id for s in sorted_sections)
        return cls(section_ids)

    @classmethod
    def from_ids(cls, section_ids: List[str]) -> "SectionOrder":
        """Create order from list of IDs."""
        return cls(tuple(section_ids))

    def move_section(self, section_id: str, new_position: int) -> "SectionOrder":
        """
        Move section to new position.

        Args:
            section_id: ID of section to move
            new_position: New position (0-indexed)

        Returns:
            New SectionOrder with updated positions
        """
        if section_id not in self.section_ids:
            raise ValueError(f"Section {section_id} not found in order")

        if new_position < 0 or new_position >= len(self.section_ids):
            raise ValueError(f"Invalid position {new_position}")

        ids_list = list(self.section_ids)
        # Remove from current position
        ids_list.remove(section_id)
        # Insert at new position
        ids_list.insert(new_position, section_id)

        return SectionOrder(tuple(ids_list))

    def swap_sections(self, section_id_1: str, section_id_2: str) -> "SectionOrder":
        """
        Swap positions of two sections.

        Args:
            section_id_1: First section ID
            section_id_2: Second section ID

        Returns:
            New SectionOrder with swapped positions
        """
        if section_id_1 not in self.section_ids:
            raise ValueError(f"Section {section_id_1} not found")
        if section_id_2 not in self.section_ids:
            raise ValueError(f"Section {section_id_2} not found")

        ids_list = list(self.section_ids)
        idx_1 = ids_list.index(section_id_1)
        idx_2 = ids_list.index(section_id_2)

        # Swap positions
        ids_list[idx_1], ids_list[idx_2] = ids_list[idx_2], ids_list[idx_1]

        return SectionOrder(tuple(ids_list))

    def add_section(self, section_id: str, position: int = None) -> "SectionOrder":
        """
        Add new section to order.

        Args:
            section_id: ID of section to add
            position: Position to insert (defaults to end)

        Returns:
            New SectionOrder with added section
        """
        if section_id in self.section_ids:
            raise ValueError(f"Section {section_id} already in order")

        ids_list = list(self.section_ids)

        if position is None:
            ids_list.append(section_id)
        else:
            if position < 0 or position > len(ids_list):
                raise ValueError(f"Invalid position {position}")
            ids_list.insert(position, section_id)

        return SectionOrder(tuple(ids_list))

    def remove_section(self, section_id: str) -> "SectionOrder":
        """
        Remove section from order.

        Args:
            section_id: ID of section to remove

        Returns:
            New SectionOrder without the section
        """
        if section_id not in self.section_ids:
            raise ValueError(f"Section {section_id} not found")

        ids_list = list(self.section_ids)
        ids_list.remove(section_id)

        return SectionOrder(tuple(ids_list))

    def get_position(self, section_id: str) -> int:
        """Get position of section in order."""
        try:
            return self.section_ids.index(section_id)
        except ValueError:
            raise ValueError(f"Section {section_id} not found")

    def apply_to_sections(self, sections: List[PromptSection]) -> List[PromptSection]:
        """
        Apply ordering to list of sections.

        Args:
            sections: List of sections to order

        Returns:
            List of sections in the specified order
        """
        sections_dict = {s.id: s for s in sections}
        ordered_sections = []

        for i, section_id in enumerate(self.section_ids):
            if section_id in sections_dict:
                section = sections_dict[section_id]
                # Update order if different
                if section.order != i:
                    section = section.change_order(i)
                ordered_sections.append(section)

        return ordered_sections

    def to_dict(self) -> Dict[str, List[str]]:
        """Convert to dictionary for serialization."""
        return {"section_ids": list(self.section_ids)}

    @classmethod
    def from_dict(cls, data: Dict[str, List[str]]) -> "SectionOrder":
        """Create from dictionary."""
        return cls(tuple(data["section_ids"]))

    def __len__(self) -> int:
        """Get number of sections in order."""
        return len(self.section_ids)

    def __contains__(self, section_id: str) -> bool:
        """Check if section is in order."""
        return section_id in self.section_ids
