"""Service for prompt section operations."""

from typing import List, Dict, Any, Optional

from ..commands.prompt_command_handler import PromptCommandHandler
from ..queries.prompt_query_handler import PromptQueryHandler
from ..repositories.json_prompt_repository import JsonPromptRepository
from ..commands.section_commands import (
    CreateSectionCommand, UpdateSectionCommand, DeleteSectionCommand,
    ReorderSectionsCommand, MoveSectionCommand, DuplicateSectionCommand,
    SectionCommandResult
)
from ..queries.section_queries import (
    GetPromptSectionsQuery, GetSectionByIdQuery, GetPromptTemplateQuery,
    SearchSectionsQuery, GetPromptStatisticsQuery,
    SectionsQueryResult, SectionQueryResult, PromptTemplateQueryResult,
    StatisticsQueryResult
)
from ..domain.prompt_section import PromptSection
from ..domain.prompt_template import PromptTemplate


class PromptSectionService:
    """
    Service for prompt section operations.

    Provides high-level business operations for managing prompt sections.
    """

    def __init__(self, config_dir: str = "config"):
        """
        Initialize service with dependencies.

        Args:
            config_dir: Configuration directory path
        """
        self.repository = JsonPromptRepository(config_dir)
        self.command_handler = PromptCommandHandler(self.repository)
        self.query_handler = PromptQueryHandler(self.repository)

    # =====================================================================================
    # COMMAND OPERATIONS (Write)
    # =====================================================================================

    def create_section(self, prompt_id: str, title: str, content: str,
                      position: int = None, section_type: str = "standard") -> SectionCommandResult:
        """
        Create new section in prompt.

        Args:
            prompt_id: Target prompt ID
            title: Section title
            content: Section content
            position: Insert position (None = end)
            section_type: Type of section

        Returns:
            Result of create operation
        """
        command = CreateSectionCommand(
            prompt_id=prompt_id,
            title=title,
            content=content,
            position=position,
            section_type=section_type
        )
        return self.command_handler.handle_create_section(command)

    def update_section(self, prompt_id: str, section_id: str,
                      title: str = None, content: str = None) -> SectionCommandResult:
        """
        Update existing section.

        Args:
            prompt_id: Prompt ID
            section_id: Section to update
            title: New title (optional)
            content: New content (optional)

        Returns:
            Result of update operation
        """
        command = UpdateSectionCommand(
            prompt_id=prompt_id,
            section_id=section_id,
            title=title,
            content=content
        )
        return self.command_handler.handle_update_section(command)

    def delete_section(self, prompt_id: str, section_id: str) -> SectionCommandResult:
        """
        Delete section from prompt.

        Args:
            prompt_id: Prompt ID
            section_id: Section to delete

        Returns:
            Result of delete operation
        """
        command = DeleteSectionCommand(prompt_id=prompt_id, section_id=section_id)
        return self.command_handler.handle_delete_section(command)

    def reorder_sections(self, prompt_id: str, section_ids: List[str]) -> SectionCommandResult:
        """
        Reorder sections in prompt.

        Args:
            prompt_id: Prompt ID
            section_ids: New order of section IDs

        Returns:
            Result of reorder operation
        """
        command = ReorderSectionsCommand(prompt_id=prompt_id, section_ids=section_ids)
        return self.command_handler.handle_reorder_sections(command)

    def move_section(self, prompt_id: str, section_id: str, new_position: int) -> SectionCommandResult:
        """
        Move section to new position.

        Args:
            prompt_id: Prompt ID
            section_id: Section to move
            new_position: New position (0-indexed)

        Returns:
            Result of move operation
        """
        command = MoveSectionCommand(
            prompt_id=prompt_id,
            section_id=section_id,
            new_position=new_position
        )
        return self.command_handler.handle_move_section(command)

    def duplicate_section(self, prompt_id: str, section_id: str,
                         new_title: str = None, position: int = None) -> SectionCommandResult:
        """
        Duplicate existing section.

        Args:
            prompt_id: Prompt ID
            section_id: Section to duplicate
            new_title: Title for duplicate (optional)
            position: Position for duplicate (optional)

        Returns:
            Result of duplicate operation
        """
        command = DuplicateSectionCommand(
            prompt_id=prompt_id,
            section_id=section_id,
            new_title=new_title,
            position=position
        )
        return self.command_handler.handle_duplicate_section(command)

    # =====================================================================================
    # QUERY OPERATIONS (Read)
    # =====================================================================================

    def get_sections(self, prompt_id: str, include_metadata: bool = True) -> SectionsQueryResult:
        """
        Get all sections for a prompt.

        Args:
            prompt_id: Prompt ID
            include_metadata: Include section metadata

        Returns:
            Query result with sections
        """
        query = GetPromptSectionsQuery(
            prompt_id=prompt_id,
            include_metadata=include_metadata
        )
        return self.query_handler.handle_get_prompt_sections(query)

    def get_section(self, prompt_id: str, section_id: str) -> SectionQueryResult:
        """
        Get specific section by ID.

        Args:
            prompt_id: Prompt ID
            section_id: Section ID

        Returns:
            Query result with section
        """
        query = GetSectionByIdQuery(prompt_id=prompt_id, section_id=section_id)
        return self.query_handler.handle_get_section_by_id(query)

    def get_template(self, prompt_id: str, include_sections: bool = True,
                    include_metadata: bool = True) -> PromptTemplateQueryResult:
        """
        Get complete prompt template.

        Args:
            prompt_id: Prompt ID
            include_sections: Include sections data
            include_metadata: Include metadata

        Returns:
            Query result with template
        """
        query = GetPromptTemplateQuery(
            prompt_id=prompt_id,
            include_sections=include_sections,
            include_metadata=include_metadata
        )
        return self.query_handler.handle_get_prompt_template(query)

    def search_sections(self, prompt_id: str = None, agent_type: str = None,
                       search_term: str = None, limit: int = None, offset: int = 0) -> SectionsQueryResult:
        """
        Search sections by criteria.

        Args:
            prompt_id: Filter by prompt (optional)
            agent_type: Filter by agent type (optional)
            search_term: Search in title/content (optional)
            limit: Limit results (optional)
            offset: Result offset

        Returns:
            Query result with matching sections
        """
        query = SearchSectionsQuery(
            prompt_id=prompt_id,
            agent_type=agent_type,
            search_term=search_term,
            limit=limit,
            offset=offset
        )
        return self.query_handler.handle_search_sections(query)

    def get_statistics(self, prompt_id: str) -> StatisticsQueryResult:
        """
        Get statistics for prompt.

        Args:
            prompt_id: Prompt ID

        Returns:
            Query result with statistics
        """
        query = GetPromptStatisticsQuery(prompt_id=prompt_id)
        return self.query_handler.handle_get_prompt_statistics(query)

    # =====================================================================================
    # CONVENIENCE METHODS (Business Logic)
    # =====================================================================================

    def generate_prompt_text(self, prompt_id: str) -> str:
        """
        Generate complete prompt text from sections.

        Args:
            prompt_id: Prompt ID

        Returns:
            Complete prompt text
        """
        template_result = self.get_template(prompt_id)
        if not template_result.success or not template_result.template:
            return ""

        return template_result.template.generate_prompt_text()

    def validate_section_order(self, prompt_id: str, section_ids: List[str]) -> Dict[str, Any]:
        """
        Validate section ordering against current sections.

        Args:
            prompt_id: Prompt ID
            section_ids: Proposed order

        Returns:
            Validation result
        """
        sections_result = self.get_sections(prompt_id)
        if not sections_result.success:
            return {"valid": False, "error": "Failed to load sections"}

        current_ids = {s.id for s in sections_result.sections}
        proposed_ids = set(section_ids)

        missing_ids = current_ids - proposed_ids
        extra_ids = proposed_ids - current_ids

        return {
            "valid": len(missing_ids) == 0 and len(extra_ids) == 0,
            "missing_sections": list(missing_ids),
            "extra_sections": list(extra_ids),
            "section_count_match": len(current_ids) == len(proposed_ids)
        }

    def clone_template(self, source_prompt_id: str, new_prompt_id: str,
                      new_agent_type: str = None) -> SectionCommandResult:
        """
        Clone entire template with all sections.

        Args:
            source_prompt_id: Source template ID
            new_prompt_id: New template ID
            new_agent_type: New agent type (optional)

        Returns:
            Result of clone operation
        """
        # This would require additional command support
        # For now, return placeholder implementation
        return SectionCommandResult(
            success=False,
            message="Template cloning not yet implemented",
            error="Feature requires additional command support"
        )