from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class SupervisorDecision:
    """Schema for supervisor decision output"""
    decision: str  # "stay" or "advance"
    reason: str
    handoff: Dict[str, Any]
    safety_risk: bool = False
    safety_message: str = ""


@dataclass
class MessageData:
    """Schema for chat messages"""
    role: str  # "user", "therapist", "supervisor"
    text: str
    timestamp: str
    prompt_used: str = ""


@dataclass
class SessionData:
    """Schema for session data"""
    session_id: str
    user_id: Optional[str]
    created_at: str
    current_stage: str
    messages: List[MessageData]
    supervisor_outputs: List[Dict[str, Any]]
    prompts_used: Dict[str, str]
    metadata: Dict[str, Any]


