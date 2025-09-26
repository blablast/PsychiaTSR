"""Session information data structure."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SessionInfo:
    """Information about the current session."""

    session_id: Optional[str]
    current_stage: str
    message_count: int
    created_at: Optional[str] = None
