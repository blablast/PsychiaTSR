"""Query objects for section operations."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..domain.prompt_section import PromptSection
from ..domain.prompt_template import PromptTemplate


@dataclass(frozen=True)
class GetPromptSectionsQuery:
    """Query to get all sections for a prompt."""

    prompt_id: str
    include_metadata: bool = True


@dataclass(frozen=True)
class GetSectionByIdQuery:
    """Query to get a specific section by ID."""

    prompt_id: str
    section_id: str


@dataclass(frozen=True)
class GetPromptTemplateQuery:
    """Query to get complete prompt template with sections."""

    prompt_id: str
    include_sections: bool = True
    include_metadata: bool = True


@dataclass(frozen=True)
class SearchSectionsQuery:
    """Query to search sections by criteria."""

    prompt_id: Optional[str] = None
    agent_type: Optional[str] = None  # therapist, supervisor
    prompt_type: Optional[str] = None  # system, stage
    stage_id: Optional[str] = None
    search_term: Optional[str] = None  # Search in title/content
    section_type: Optional[str] = None
    limit: Optional[int] = None
    offset: int = 0


@dataclass(frozen=True)
class GetPromptStatisticsQuery:
    """Query to get statistics for a prompt."""

    prompt_id: str


# Query Result objects


@dataclass(frozen=True)
class QueryResult:
    """Base result for query operations."""

    success: bool
    message: str
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.now())


@dataclass(frozen=True)
class SectionsQueryResult(QueryResult):
    """Result containing list of sections."""

    sections: List[PromptSection] = None
    total_count: int = 0

    def __post_init__(self):
        super().__post_init__()
        if self.sections is None:
            object.__setattr__(self, "sections", [])


@dataclass(frozen=True)
class SectionQueryResult(QueryResult):
    """Result containing a single section."""

    section: Optional[PromptSection] = None


@dataclass(frozen=True)
class PromptTemplateQueryResult(QueryResult):
    """Result containing a prompt template."""

    template: Optional[PromptTemplate] = None


@dataclass(frozen=True)
class StatisticsQueryResult(QueryResult):
    """Result containing prompt statistics."""

    statistics: Dict[str, Any] = None

    def __post_init__(self):
        super().__post_init__()
        if self.statistics is None:
            object.__setattr__(self, "statistics", {})
