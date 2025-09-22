"""Log entry data structure."""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: str
    event_type: str
    message: str
    data: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[int] = None
    agent_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp,
            'event_type': self.event_type,
            'message': self.message,
            'data': self.data,
            'response_time_ms': self.response_time_ms,
            'agent_type': self.agent_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create from dictionary."""
        return cls(
            timestamp=data.get('timestamp', ''),
            event_type=data.get('event_type', ''),
            message=data.get('message', ''),
            data=data.get('data'),
            response_time_ms=data.get('response_time_ms'),
            agent_type=data.get('agent_type')
        )