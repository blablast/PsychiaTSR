"""Result of a workflow operation."""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class WorkflowResult:
    """Result of a workflow operation."""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
