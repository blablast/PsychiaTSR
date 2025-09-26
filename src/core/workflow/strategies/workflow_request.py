"""Workflow request types and data structures."""

from dataclasses import dataclass
from enum import Enum
from .workflow_context import WorkflowContext


class WorkflowType(Enum):
    """Types of workflow strategies."""

    CONVERSATION = "conversation"


@dataclass(frozen=True)
class WorkflowRequest:
    """Workflow request containing type and context."""

    type: WorkflowType
    context: WorkflowContext

    @classmethod
    def conversation(
        cls, user_message: str, current_stage: str, conversation_history, session_id: str
    ):
        """Create conversation workflow request."""
        context = WorkflowContext(
            user_message=user_message,
            current_stage=current_stage,
            conversation_history=conversation_history,
            session_id=session_id,
        )
        return cls(type=WorkflowType.CONVERSATION, context=context)
