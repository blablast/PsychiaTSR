"""Stage information data structure."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class StageInfo:
    """Information about a therapy stage."""
    stage_id: str
    name: str
    order: int
    description: Optional[str] = None