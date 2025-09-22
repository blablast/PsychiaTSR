import re
from typing import List, Dict, Any


class SafetyChecker:
    """Safety checker for user inputs and responses"""
    
    # Keywords that might indicate self-harm risk
    SELF_HARM_KEYWORDS = [
        "samobójstwo", "zabić się", "skończyć z życiem", "nie chcę żyć", "nie chcę już żyć",
        "śmierć", "umrzeć", "skrzywdzić się", "pokaleczyć się", "myślę o samobójstwie",
        "chcę umrzeć", "wolę umrzeć", "lepiej będzie jak umrę",
        "suicide", "kill myself", "end my life", "don't want to live",
        "hurt myself", "harm myself", "cut myself", "want to die"
    ]
    
    # Keywords that might indicate harm to others
    HARM_OTHERS_KEYWORDS = [
        "zabić kogoś", "skrzywdzić kogoś", "przemoc", "atak",
        "kill someone", "hurt someone", "violence", "attack"
    ]
    
    # Crisis support information
    CRISIS_SUPPORT_MESSAGE = """
🚨 **WAŻNE - POMOC W KRYZYSIE**

Jeśli czujesz zagrożenie lub myślisz o krzywdzeniu siebie lub innych, skontaktuj się natychmiast z pomocą:

**Telefon Zaufania dla Dzieci i Młodzieży**: 116 111
**Centrum Wsparcia dla osób w stanie kryzysu psychicznego**: 800 70 2222
**Pogotowie Ratunkowe**: 999 lub 112

**Online:**
- www.kryzys.pl
- www.pokonackryzys.pl

Ta rozmowa nie zastępuje profesjonalnej pomocy medycznej lub psychologicznej.
"""
    
    def __init__(self):
        self.risk_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for risk detection"""
        patterns = []
        
        all_keywords = self.SELF_HARM_KEYWORDS + self.HARM_OTHERS_KEYWORDS
        
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
        
        # Check for self-harm indicators
        for keyword in self.SELF_HARM_KEYWORDS:
            if keyword.lower() in text_lower:
                risks["has_risk"] = True
                risks["self_harm_risk"] = True
                risks["matched_keywords"].append(keyword)
        
        # Check for harm to others indicators
        for keyword in self.HARM_OTHERS_KEYWORDS:
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
        
        # Check for inappropriate content
        medical_advice_patterns = [
            r"zażywaj.*lek", r"take.*medication", r"diagnoza", r"diagnosis",
            r"choroba", r"illness", r"zaburzenie", r"disorder"
        ]
        
        for pattern in medical_advice_patterns:
            if re.search(pattern, response_lower):
                validation["issues"].append("Unikaj udzielania porad medycznych")
                validation["is_valid"] = False
        
        # Check for "why" questions (discouraged in SFBT)
        why_patterns = [r"\bdlaczego\b", r"\bwhy\b"]
        for pattern in why_patterns:
            if re.search(pattern, response_lower):
                validation["warnings"].append("Unikaj pytań 'dlaczego' w TSR")
        
        # Check response length (should be 1-3 sentences)
        sentences = re.split(r'[.!?]+', response.strip())
        sentence_count = len([s for s in sentences if s.strip()])
        
        if sentence_count > 3:
            validation["warnings"].append("Odpowiedź może być zbyt długa (>3 zdania)")
        
        # Check if ends with question
        if not re.search(r'[?]$', response.strip()):
            validation["warnings"].append("Odpowiedź powinna kończyć się pytaniem")
        
        return validation
    
    def get_crisis_message(self) -> str:
        """Get crisis support message"""
        return self.CRISIS_SUPPORT_MESSAGE
    
    def should_show_crisis_message(self, safety_check: Dict[str, Any]) -> bool:
        """Determine if crisis message should be shown"""
        return safety_check.get("risk_level") in ["high", "medium"]
    
    def filter_sensitive_content(self, text: str) -> str:
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