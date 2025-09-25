"""Command Handler for prompt write operations."""

from typing import Protocol, runtime_checkable
from ..domain.prompt_template import PromptTemplate
from ..domain.section_order import SectionOrder
from .section_commands import (
    CreateSectionCommand, UpdateSectionCommand, DeleteSectionCommand,
    ReorderSectionsCommand, MoveSectionCommand, DuplicateSectionCommand,
    SectionCommandResult
)


@runtime_checkable
class PromptRepository(Protocol):
    """Repository interface for prompt persistence."""

    def get_template(self, prompt_id: str) -> PromptTemplate:
        """Get prompt template by ID."""
        ...

    def save_template(self, template: PromptTemplate) -> None:
        """Save prompt template."""
        ...


class PromptCommandHandler:
    """
    Command Handler for prompt operations.

    Handles all write operations for prompt data.
    Encapsulates business logic and maintains aggregate consistency.
    """

    def __init__(self, repository: PromptRepository):
        """
        Initialize command handler.

        Args:
            repository: Repository for prompt persistence
        """
        self._repository = repository

    def handle_create_section(self, command: CreateSectionCommand) -> SectionCommandResult:
        """
        Handle create section command.

        Args:
            command: Create section command

        Returns:
            Result of the operation
        """
        try:
            # Load template (aggregate root)
            template = self._repository.get_template(command.prompt_id)

            # Add section to template
            if command.position is not None:
                # Insert at specific position
                section = template.add_section(command.title, command.content, command.section_type)
                template.move_section(section.id, command.position)
            else:
                # Add at end
                section = template.add_section(command.title, command.content, command.section_type)

            # Save updated template
            self._repository.save_template(template)

            return SectionCommandResult(
                success=True,
                message="Section created successfully",
                section_id=section.id,
                prompt_id=command.prompt_id
            )

        except Exception as e:
            return SectionCommandResult(
                success=False,
                message="Failed to create section",
                error=str(e),
                prompt_id=command.prompt_id
            )

    def handle_update_section(self, command: UpdateSectionCommand) -> SectionCommandResult:
        """
        Handle update section command.

        Args:
            command: Update section command

        Returns:
            Result of the operation
        """
        try:
            template = self._repository.get_template(command.prompt_id)

            # Update section
            updated_section = template.update_section(
                command.section_id,
                command.title,
                command.content
            )

            self._repository.save_template(template)

            return SectionCommandResult(
                success=True,
                message="Section updated successfully",
                section_id=command.section_id,
                prompt_id=command.prompt_id
            )

        except Exception as e:
            return SectionCommandResult(
                success=False,
                message="Failed to update section",
                error=str(e),
                section_id=command.section_id,
                prompt_id=command.prompt_id
            )

    def handle_delete_section(self, command: DeleteSectionCommand) -> SectionCommandResult:
        """
        Handle delete section command.

        Args:
            command: Delete section command

        Returns:
            Result of the operation
        """
        try:
            template = self._repository.get_template(command.prompt_id)

            # Remove section
            removed = template.remove_section(command.section_id)
            if not removed:
                return SectionCommandResult(
                    success=False,
                    message="Section not found",
                    section_id=command.section_id,
                    prompt_id=command.prompt_id
                )

            self._repository.save_template(template)

            return SectionCommandResult(
                success=True,
                message="Section deleted successfully",
                section_id=command.section_id,
                prompt_id=command.prompt_id
            )

        except Exception as e:
            return SectionCommandResult(
                success=False,
                message="Failed to delete section",
                error=str(e),
                section_id=command.section_id,
                prompt_id=command.prompt_id
            )

    def handle_reorder_sections(self, command: ReorderSectionsCommand) -> SectionCommandResult:
        """
        Handle reorder sections command.

        Args:
            command: Reorder sections command

        Returns:
            Result of the operation
        """
        try:
            template = self._repository.get_template(command.prompt_id)

            # Create new section order
            new_order = SectionOrder.from_ids(command.section_ids)

            # Apply reordering
            template.reorder_sections(new_order)

            self._repository.save_template(template)

            return SectionCommandResult(
                success=True,
                message="Sections reordered successfully",
                prompt_id=command.prompt_id,
                affected_sections=command.section_ids
            )

        except Exception as e:
            return SectionCommandResult(
                success=False,
                message="Failed to reorder sections",
                error=str(e),
                prompt_id=command.prompt_id
            )

    def handle_move_section(self, command: MoveSectionCommand) -> SectionCommandResult:
        """
        Handle move section command.

        Args:
            command: Move section command

        Returns:
            Result of the operation
        """
        try:
            template = self._repository.get_template(command.prompt_id)

            # Move section to new position
            template.move_section(command.section_id, command.new_position)

            self._repository.save_template(template)

            return SectionCommandResult(
                success=True,
                message="Section moved successfully",
                section_id=command.section_id,
                prompt_id=command.prompt_id
            )

        except Exception as e:
            return SectionCommandResult(
                success=False,
                message="Failed to move section",
                error=str(e),
                section_id=command.section_id,
                prompt_id=command.prompt_id
            )

    def handle_duplicate_section(self, command: DuplicateSectionCommand) -> SectionCommandResult:
        """
        Handle duplicate section command.

        Args:
            command: Duplicate section command

        Returns:
            Result of the operation
        """
        try:
            template = self._repository.get_template(command.prompt_id)

            # Get original section
            original_section = template.get_section(command.section_id)
            if not original_section:
                return SectionCommandResult(
                    success=False,
                    message="Original section not found",
                    section_id=command.section_id,
                    prompt_id=command.prompt_id
                )

            # Create duplicate
            new_title = command.new_title or f"{original_section.title} (Copy)"
            duplicate_section = template.add_section(
                new_title,
                original_section.content,
                original_section.section_type
            )

            # Move to desired position if specified
            if command.position is not None:
                template.move_section(duplicate_section.id, command.position)

            self._repository.save_template(template)

            return SectionCommandResult(
                success=True,
                message="Section duplicated successfully",
                section_id=duplicate_section.id,
                prompt_id=command.prompt_id
            )

        except Exception as e:
            return SectionCommandResult(
                success=False,
                message="Failed to duplicate section",
                error=str(e),
                section_id=command.section_id,
                prompt_id=command.prompt_id
            )