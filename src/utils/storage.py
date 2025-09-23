import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class StorageProvider:
    """JSON-based storage provider for sessions and logs"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.sessions_dir = self.data_dir / "sessions"
        self.logs_dir = self.data_dir / "logs"
        self.therapist_logs_dir = self.logs_dir / "therapist"
        self.supervisor_logs_dir = self.logs_dir / "supervisor"
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.sessions_dir, self.therapist_logs_dir, self.supervisor_logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "current_stage": "",
            "messages": [],
            "supervisor_outputs": [],
            "prompts_used": {},
            "metadata": {
                "safety_flags": [],
                "notes": [],
                "models_used": {}
            }
        }
        
        session_file = self.sessions_dir / f"{session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        return session_id
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data by ID"""
        session_file = self.sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def save_session(self, session_data: Dict[str, Any]) -> bool:
        """Save session data"""
        session_id = session_data.get("session_id")
        if not session_id:
            return False
        
        session_file = self.sessions_dir / f"{session_id}.json"
        
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            return True
        except IOError:
            return False
    
    def append_message(self, session_id: str, role: str, text: str, prompt_used: str = "") -> bool:
        """Append a message to session"""
        session_data = self.load_session(session_id)
        if not session_data:
            return False
        
        message = {
            "role": role,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "prompt_used": prompt_used
        }
        
        session_data["messages"].append(message)
        return self.save_session(session_data)
    
    def save_supervisor(self, session_id: str, output: Dict[str, Any]) -> bool:
        """Save supervisor output to session"""
        session_data = self.load_session(session_id)
        if not session_data:
            return False
        
        supervisor_entry = {
            "timestamp": datetime.now().isoformat(),
            "output": output
        }
        
        session_data["supervisor_outputs"].append(supervisor_entry)
        return self.save_session(session_data)
    
    def update_stage(self, session_id: str, stage: str) -> bool:
        """Update current stage in session"""
        session_data = self.load_session(session_id)
        if not session_data:
            return False
        
        session_data["current_stage"] = stage
        return self.save_session(session_data)
    
    def update_prompt_used(self, session_id: str, stage: str, prompt_id: str) -> bool:
        """Update prompt used for a stage"""
        session_data = self.load_session(session_id)
        if not session_data:
            return False
        
        session_data["prompts_used"][stage] = prompt_id
        return self.save_session(session_data)
    
    def add_safety_flag(self, session_id: str, flag: str) -> bool:
        """Add safety flag to session metadata"""
        session_data = self.load_session(session_id)
        if not session_data:
            return False
        
        session_data["metadata"]["safety_flags"].append({
            "flag": flag,
            "timestamp": datetime.now().isoformat()
        })
        return self.save_session(session_data)

    def update_session_models(self, session_id: str, therapist_model: str, supervisor_model: str,
                             therapist_provider: str = "openai", supervisor_provider: str = "gemini") -> bool:
        """Update session with current model information"""
        session_data = self.load_session(session_id)
        if not session_data:
            return False

        session_data["metadata"]["models_used"] = {
            "therapist": {
                "model": therapist_model,
                "provider": therapist_provider,
                "updated_at": datetime.now().isoformat()
            },
            "supervisor": {
                "model": supervisor_model,
                "provider": supervisor_provider,
                "updated_at": datetime.now().isoformat()
            }
        }
        return self.save_session(session_data)
    
    def log_therapist_response(self, session_id: str, full_response: str, prompt_used: str = "") -> bool:
        """Log full therapist response to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.therapist_logs_dir / f"{session_id}_{timestamp}.log"
        
        log_entry = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "prompt_used": prompt_used,
            "full_response": full_response
        }
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, ensure_ascii=False, indent=2)
            return True
        except IOError:
            return False
    
    def log_supervisor_response(self, session_id: str, full_response: str, decision_json: Dict[str, Any]) -> bool:
        """Log full supervisor response to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.supervisor_logs_dir / f"{session_id}_{timestamp}.log"
        
        log_entry = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "full_response": full_response,
            "decision": decision_json
        }
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, ensure_ascii=False, indent=2)
            return True
        except IOError:
            return False
    
    def list_sessions(self) -> List[str]:
        """List all available session IDs"""
        session_files = list(self.sessions_dir.glob("*.json"))
        return [f.stem for f in session_files]
    
    def save_prompt(self, stage: str, prompt_text: str, review: str = "") -> str:
        """Save a new prompt version for a stage"""
        prompt_dir = Path("./prompts")
        prompt_dir.mkdir(exist_ok=True)
        
        prompt_file = prompt_dir / f"{stage}.json"
        
        prompt_id = f"p{int(datetime.now().timestamp())}"
        new_prompt = {
            "id": prompt_id,
            "prompt_text": prompt_text,
            "created_at": datetime.now().isoformat(),
            "review": review,
            "active": True
        }
        
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            
            for prompt in prompts:
                prompt["active"] = False
        else:
            prompts = []
        
        prompts.append(new_prompt)
        
        with open(prompt_file, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)
        
        return prompt_id

    def add_technical_log(self, session_id: str, log_entry: Dict[str, Any]) -> bool:
        """Add technical log entry to session data"""
        session_data = self.load_session(session_id)
        if not session_data:
            return False

        # Initialize technical_logs if not exists
        if "technical_logs" not in session_data:
            session_data["technical_logs"] = []

        # Add the log entry
        session_data["technical_logs"].append(log_entry)

        # Save updated session
        return self.save_session(session_data)