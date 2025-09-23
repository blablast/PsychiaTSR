from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class SupervisorDecision:
    """Schema for supervisor decision output (TSR compliant)"""
    decision: str  # "stay" or "advance"
    summary: str  # 2-3 zdania neutralnego podsumowania etapu
    addressing: str  # "formal" or "informal"
    reason: str = ""  # Opcjonalne - dla debugowania
    handoff: Dict[str, Any] = None  # Dodatkowe informacje
    safety_risk: bool = False
    safety_message: str = ""

    def __post_init__(self):
        if self.handoff is None:
            self.handoff = {}

    @staticmethod
    def get_json_schema() -> Dict[str, Any]:
        """Get JSON schema for structured output (OpenAI version with additionalProperties)"""
        return {
            "type": "object",
            "properties": {
                "decision": {
                    "type": "string",
                    "enum": ["stay", "advance"],
                    "description": "Decyzja czy zostać w obecnym etapie (stay) czy przejść dalej (advance)"
                },
                "summary": {
                    "type": "string",
                    "description": "2-3 zdania neutralnego podsumowania etapu w trzeciej osobie, bez zwrotów do klienta"
                },
                "addressing": {
                    "type": "string",
                    "enum": ["formal", "informal"],
                    "description": "Ustalona forma zwracania się (formal = Pan/Pani, informal = ty)"
                },
                "reason": {
                    "type": "string",
                    "description": "Uzasadnienie decyzji nadzorcy w języku polskim (opcjonalne dla debugowania)"
                },
                "handoff": {
                    "type": "object",
                    "description": "Dodatkowe informacje przekazywane między etapami",
                    "additionalProperties": True
                },
                "safety_risk": {
                    "type": "boolean",
                    "description": "Czy wykryto ryzyko bezpieczeństwa"
                },
                "safety_message": {
                    "type": "string",
                    "description": "Wiadomość dotycząca bezpieczeństwa (jeśli dotyczy)"
                }
            },
            "required": ["decision", "summary", "addressing"],
            "additionalProperties": False
        }

    @staticmethod
    def get_openai_response_format() -> Dict[str, Any]:
        """Get OpenAI structured outputs format"""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "supervisor_decision",
                "schema": SupervisorDecision.get_json_schema(),
                "strict": True
            }
        }

    @staticmethod
    def get_gemini_response_schema() -> Dict[str, Any]:
        """Get Gemini response schema format (without additionalProperties, TSR compliant)"""
        return {
            "type": "object",
            "properties": {
                "decision": {
                    "type": "string",
                    "enum": ["stay", "advance"],
                    "description": "Decyzja czy zostać w obecnym etapie (stay) czy przejść dalej (advance)"
                },
                "summary": {
                    "type": "string",
                    "description": "2-3 zdania neutralnego podsumowania etapu w trzeciej osobie, bez zwrotów do klienta"
                },
                "addressing": {
                    "type": "string",
                    "enum": ["formal", "informal"],
                    "description": "Ustalona forma zwracania się (formal = Pan/Pani, informal = ty)"
                },
                "reason": {
                    "type": "string",
                    "description": "Uzasadnienie decyzji nadzorcy w języku polskim (opcjonalne dla debugowania)"
                },
                "handoff": {
                    "type": "object",
                    "description": "Dodatkowe informacje przekazywane między etapami",
                    "properties": {
                        "stage_progress": {
                            "type": "string",
                            "description": "Informacja o postępie w aktualnym etapie"
                        },
                        "key_insights": {
                            "type": "string",
                            "description": "Kluczowe spostrzeżenia z rozmowy"
                        },
                        "next_focus": {
                            "type": "string",
                            "description": "Na czym skupić się w następnym etapie"
                        },
                        "error": {
                            "type": "string",
                            "description": "Informacja o błędzie (jeśli wystąpił)"
                        },
                        "error_type": {
                            "type": "string",
                            "description": "Typ błędu (jeśli wystąpił)"
                        }
                    }
                },
                "safety_risk": {
                    "type": "boolean",
                    "description": "Czy wykryto ryzyko bezpieczeństwa"
                },
                "safety_message": {
                    "type": "string",
                    "description": "Wiadomość dotycząca bezpieczeństwa (jeśli dotyczy)"
                }
            },
            "required": ["decision", "summary", "addressing"]
        }


@dataclass
class MessageData:
    """Schema for chat messages"""
    role: str  # "user", "therapist", "supervisor"
    text: str
    timestamp: str
    prompt_used: str = ""
    supervisor_response_time_ms: Optional[int] = None
    therapist_response_time_ms: Optional[int] = None


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


