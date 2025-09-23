"""Abstract base class for workflow strategies."""

from abc import ABC, abstractmethod
from ..workflow_result import WorkflowResult
from .workflow_context import WorkflowContext


class WorkflowStrategy(ABC):
    """Abstract base class for workflow execution strategies."""

    @abstractmethod
    def execute(self, context: WorkflowContext) -> WorkflowResult:
        """
        Execute the workflow strategy.

        Args:
            context: Workflow context with all necessary data

        Returns:
            WorkflowResult with execution results
        """
        pass