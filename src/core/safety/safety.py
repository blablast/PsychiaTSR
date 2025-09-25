import json
import re
from pathlib import Path
from typing import List, Dict, Any


class SafetyChecker:
    """Safety checker for user inputs and responses"""

    def __init__(self):
        self._config = self._load_safety_config()
        self.risk_patterns = self._compile_patterns()

    @staticmethod
    def _load_safety_config() -> Dict[str, Any]:
        """Load safety configuration from template file."""
        try:
            template_path = Path("config/templates/defaults/safety_config_default.json")
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass

        # Fallback to hardcoded values
        return {
            "self_harm_keywords": [
                "samobójstwo", "zabić się", "skończyć z życiem", "nie chcę żyć", "nie chcę już żyć",
                "śmierć", "umrzeć", "skrzywdzić się", "pokaleczyć się", "myślę o samobójstwie",
                "chcę umrzeć", "wolę umrzeć", "lepiej będzie jak umrę",
                "suicide", "kill myself", "end my life", "don't want to live",
                "hurt myself", "harm myself", "cut myself", "want to die"
            ],
            "harm_others_keywords": [
                "zabić kogoś", "skrzywdzić kogoś", "przemoc", "atak",
                "kill someone", "hurt someone", "violence", "attack"
            ],
            "crisis_support_message": "\n🚨 **WAŻNE - POMOC W KRYZYSIE**\n\nJeśli czujesz zagrożenie lub myślisz o krzywdzeniu siebie lub innych, skontaktuj się natychmiast z pomocą:\n\n**Telefon Zaufania dla Dzieci i Młodzieży**: 116 111\n**Centrum Wsparcia dla osób w stanie kryzysu psychicznego**: 800 70 2222\n**Pogotowie Ratunkowe**: 999 lub 112\n\n**Online:**\n- www.kryzys.pl\n- www.pokonackryzys.pl\n\nTa rozmowa nie zastępuje profesjonalnej pomocy medycznej lub psychologicznej.\n",
            "validation_patterns": {
                "medical_advice_patterns": [
                    "zażywaj.*lek", "take.*medication", "diagnoza", "diagnosis",
                    "choroba", "illness", "zaburzenie", "disorder"
                ],
                "why_patterns": [
                    "\\bdlaczego\\b", "\\bwhy\\b"
                ]
            },
            "response_validation": {
                "max_sentences": 3,
                "should_end_with_question": True
            }
        }
    
    def _compile_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for risk detection"""
        patterns = []

        self_harm_keywords = self._config.get("self_harm_keywords", [])
        harm_others_keywords = self._config.get("harm_others_keywords", [])
        all_keywords = self_harm_keywords + harm_others_keywords

        for keyword in all_keywords:
            pattern = re.compile(r'\b' + re.escape(keyword.lower()) + r'\b', re.IGNORECASE)
            patterns.append(pattern)

        return patterns
    
    def check_user_input(self, text: str) -> Dict[str, Any]:
        """Check user input for safety risks"""
        text_lower = text.lower()

        risks = {
            "has_risk": False,
            "self_harm_risk": False,
            "harm_others_risk": False,
            "matched_keywords": [],
            "risk_level": "none"  # none, low, medium, high
        }

        self_harm_keywords = self._config.get("self_harm_keywords", [])
        harm_others_keywords = self._config.get("harm_others_keywords", [])

        # Check for self-harm indicators
        for keyword in self_harm_keywords:
            if keyword.lower() in text_lower:
                risks["has_risk"] = True
                risks["self_harm_risk"] = True
                risks["matched_keywords"].append(keyword)

        # Check for harm to others indicators
        for keyword in harm_others_keywords:
            if keyword.lower() in text_lower:
                risks["has_risk"] = True
                risks["harm_others_risk"] = True
                risks["matched_keywords"].append(keyword)

        # Determine risk level
        if risks["has_risk"]:
            if risks["self_harm_risk"] or risks["harm_others_risk"]:
                risks["risk_level"] = "high"
            else:
                risks["risk_level"] = "medium"

        return risks
    
    def validate_therapist_response(self, response: str) -> Dict[str, Any]:
        """Validate therapist response for appropriate content"""
        validation = {
            "is_valid": True,
            "issues": [],
            "warnings": []
        }

        response_lower = response.lower()
        validation_patterns = self._config.get("validation_patterns", {})

        # Check for inappropriate content
        medical_advice_patterns = validation_patterns.get("medical_advice_patterns", [])

        for pattern in medical_advice_patterns:
            if re.search(pattern, response_lower):
                validation["issues"].append("Unikaj udzielania porad medycznych")
                validation["is_valid"] = False

        # Check for "why" questions (discouraged in SFBT)
        why_patterns = validation_patterns.get("why_patterns", [])
        for pattern in why_patterns:
            if re.search(pattern, response_lower):
                validation["warnings"].append("Unikaj pytań 'dlaczego' w TSR")

        # Check response length (should be 1-3 sentences)
        sentences = re.split(r'[.!?]+', response.strip())
        sentence_count = len([s for s in sentences if s.strip()])

        response_config = self._config.get("response_validation", {})
        max_sentences = response_config.get("max_sentences", 3)

        if sentence_count > max_sentences:
            validation["warnings"].append(f"Odpowiedź może być zbyt długa (>{max_sentences} zdania)")

        # Check if ends with question
        should_end_with_question = response_config.get("should_end_with_question", True)
        if should_end_with_question and not re.search(r'[?]$', response.strip()):
            validation["warnings"].append("Odpowiedź powinna kończyć się pytaniem")

        return validation
    
    def get_crisis_message(self) -> str:
        """Get crisis support message"""
        return self._config.get("crisis_support_message", "")
    
    @staticmethod
    def should_show_crisis_message(safety_check: Dict[str, Any]) -> bool:
        """Determine if crisis message should be shown"""
        return safety_check.get("risk_level") in ["high", "medium"]
    
    @staticmethod
    def filter_sensitive_content(text: str) -> str:
        """Filter or mask sensitive content for logging"""
        # For now, just return as-is but this could be enhanced
        # to mask personal information, etc.
        return text
    
    def validate_session_safety(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate overall session safety"""
        safety_summary = {
            "total_risks": 0,
            "high_risk_messages": 0,
            "requires_intervention": False,
            "safety_flags": []
        }
        
        for message in messages:
            if message.get("role") == "user":
                safety_check = self.check_user_input(message.get("text", ""))
                if safety_check["has_risk"]:
                    safety_summary["total_risks"] += 1
                    if safety_check["risk_level"] == "high":
                        safety_summary["high_risk_messages"] += 1
                        safety_summary["requires_intervention"] = True
                        safety_summary["safety_flags"].append({
                            "timestamp": message.get("timestamp"),
                            "risk_type": "self_harm" if safety_check["self_harm_risk"] else "harm_others",
                            "keywords": safety_check["matched_keywords"]
                        })
        
        return safety_summary