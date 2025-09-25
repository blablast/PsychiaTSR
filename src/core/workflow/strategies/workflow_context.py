"""Workflow context data structures."""

from dataclasses import dataclass
from typing import List
from src.core.models.schemas import MessageData


@dataclass(frozen=True)
class WorkflowContext:
    """Immutable workflow context containing all necessary data."""

    user_message: str
    current_stage: str
    conversation_history: List[MessageData]
    session_id: str

    @classmethod
    def from_request(cls, request):
        """Create WorkflowContext from WorkflowRequest."""
        return request.context