"""Query Handler for prompt read operations."""

from typing import Protocol, runtime_checkable, List
from ..domain.prompt_template import PromptTemplate
from ..domain.prompt_section import PromptSection
from .section_queries import (
    GetPromptSectionsQuery, GetSectionByIdQuery, GetPromptTemplateQuery,
    SearchSectionsQuery, GetPromptStatisticsQuery,
    SectionsQueryResult, SectionQueryResult, PromptTemplateQueryResult,
    StatisticsQueryResult
)


@runtime_checkable
class PromptQueryRepository(Protocol):
    """Repository interface for prompt read operations."""

    def get_template(self, prompt_id: str) -> PromptTemplate:
        """Get prompt template by ID."""
        ...

    def search_templates(self, agent_type: str = None, prompt_type: str = None, stage_id: str = None) -> List[PromptTemplate]:
        """Search templates by criteria."""
        ...


class PromptQueryHandler:
    """
    Query Handler for prompt operations.

    Handles all read operations for prompt data.
    Optimized for query performance and data presentation.
    """

    def __init__(self, repository: PromptQueryRepository):
        """
        Initialize query handler.

        Args:
            repository: Repository for prompt read operations
        """
        self._repository = repository

    def handle_get_prompt_sections(self, query: GetPromptSectionsQuery) -> SectionsQueryResult:
        """
        Handle get prompt sections query.

        Args:
            query: Get sections query

        Returns:
            Result containing sections
        """
        try:
            template = self._repository.get_template(query.prompt_id)
            sections = template.get_sections_ordered()

            # Filter metadata if not requested
            if not query.include_metadata:
                sections = [
                    PromptSection(
                        id=s.id,
                        title=s.title,
                        content=s.content,
                        order=s.order,
                        section_type=s.section_type,
                        metadata=None,
                        created_at=s.created_at,
                        updated_at=s.updated_at
                    ) for s in sections
                ]

            return SectionsQueryResult(
                success=True,
                message="Sections retrieved successfully",
                sections=sections,
                total_count=len(sections)
            )

        except Exception as e:
            return SectionsQueryResult(
                success=False,
                message="Failed to retrieve sections",
                error=str(e),
                sections=[],
                total_count=0
            )

    def handle_get_section_by_id(self, query: GetSectionByIdQuery) -> SectionQueryResult:
        """
        Handle get section by ID query.

        Args:
            query: Get section query

        Returns:
            Result containing section
        """
        try:
            template = self._repository.get_template(query.prompt_id)
            section = template.get_section(query.section_id)

            if not section:
                return SectionQueryResult(
                    success=False,
                    message="Section not found",
                    section=None
                )

            return SectionQueryResult(
                success=True,
                message="Section retrieved successfully",
                section=section
            )

        except Exception as e:
            return SectionQueryResult(
                success=False,
                message="Failed to retrieve section",
                error=str(e),
                section=None
            )

    def handle_get_prompt_template(self, query: GetPromptTemplateQuery) -> PromptTemplateQueryResult:
        """
        Handle get prompt template query.

        Args:
            query: Get template query

        Returns:
            Result containing template
        """
        try:
            template = self._repository.get_template(query.prompt_id)

            # Filter sections if not requested
            if not query.include_sections:
                template = PromptTemplate(
                    id=template.id,
                    agent_type=template.agent_type,
                    prompt_type=template.prompt_type,
                    stage_id=template.stage_id,
                    sections=[],
                    metadata=template.metadata if query.include_metadata else {},
                    created_at=template.created_at,
                    updated_at=template.updated_at
                )

            return PromptTemplateQueryResult(
                success=True,
                message="Template retrieved successfully",
                template=template
            )

        except Exception as e:
            return PromptTemplateQueryResult(
                success=False,
                message="Failed to retrieve template",
                error=str(e),
                template=None
            )

    def handle_search_sections(self, query: SearchSectionsQuery) -> SectionsQueryResult:
        """
        Handle search sections query.

        Args:
            query: Search query

        Returns:
            Result containing matching sections
        """
        try:
            # If prompt_id is specified, search within that prompt
            if query.prompt_id:
                template = self._repository.get_template(query.prompt_id)
                all_sections = template.get_sections_ordered()
            else:
                # Search across all templates matching criteria
                templates = self._repository.search_templates(
                    query.agent_type,
                    query.prompt_type,
                    query.stage_id
                )
                all_sections = []
                for template in templates:
                    all_sections.extend(template.get_sections_ordered())

            # Apply filters
            filtered_sections = self._apply_search_filters(all_sections, query)

            # Apply pagination
            total_count = len(filtered_sections)
            if query.limit:
                start_idx = query.offset
                end_idx = start_idx + query.limit
                filtered_sections = filtered_sections[start_idx:end_idx]

            return SectionsQueryResult(
                success=True,
                message="Search completed successfully",
                sections=filtered_sections,
                total_count=total_count
            )

        except Exception as e:
            return SectionsQueryResult(
                success=False,
                message="Search failed",
                error=str(e),
                sections=[],
                total_count=0
            )

    def handle_get_prompt_statistics(self, query: GetPromptStatisticsQuery) -> StatisticsQueryResult:
        """
        Handle get prompt statistics query.

        Args:
            query: Statistics query

        Returns:
            Result containing statistics
        """
        try:
            template = self._repository.get_template(query.prompt_id)
            statistics = template.get_statistics()

            return StatisticsQueryResult(
                success=True,
                message="Statistics retrieved successfully",
                statistics=statistics
            )

        except Exception as e:
            return StatisticsQueryResult(
                success=False,
                message="Failed to retrieve statistics",
                error=str(e),
                statistics={}
            )

    def _apply_search_filters(self, sections: List[PromptSection], query: SearchSectionsQuery) -> List[PromptSection]:
        """Apply search filters to sections list."""
        filtered = sections

        # Filter by section type
        if query.section_type:
            filtered = [s for s in filtered if s.section_type == query.section_type]

        # Filter by search term (title and content)
        if query.search_term:
            search_term_lower = query.search_term.lower()
            filtered = [
                s for s in filtered
                if search_term_lower in s.title.lower() or search_term_lower in s.content.lower()
            ]

        return filtered