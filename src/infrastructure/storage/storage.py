import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class StorageProvider:
    """JSON-based storage provider for sessions and logs"""

    def __init__(self, logs_dir: str = "./logs"):
        self.logs_dir = Path(logs_dir)
        # Remove old data_dir and sessions_dir - everything goes in logs/ now

        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _get_session_template() -> Dict[str, Any]:
        """Get session template from template file."""
        try:
            template_path = Path("config/templates/defaults/session_template.json")
            if template_path.exists():
                with open(template_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass

        # Fallback to hardcoded template
        return {
            "session_id": "",
            "user_id": None,
            "created_at": "",
            "current_stage": "",
            "messages": [],
            "supervisor_outputs": [],
            "prompts_used": {},
            "metadata": {"safety_flags": [], "notes": [], "models_used": {}},
        }

    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        session_data = self._get_session_template()

        # Fill in session-specific data
        session_data["session_id"] = session_id
        session_data["user_id"] = user_id
        session_data["created_at"] = datetime.now().isoformat()

        # Create session directory and session file inside it
        session_dir = self.logs_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        session_file = session_dir / "session.json"
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        return session_id

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data by ID"""
        # Load from logs/{session_id}/session.json
        session_file = self.logs_dir / session_id / "session.json"

        if not session_file.exists():
            return None

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def save_session(self, session_data: Dict[str, Any]) -> bool:
        """Save session data"""
        session_id = session_data.get("session_id")
        if not session_id:
            return False

        # Save to logs/{session_id}/session.json
        session_dir = self.logs_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        session_file = session_dir / "session.json"

        try:
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            return True
        except IOError:
            return False

    def append_message(
        self,
        session_id: str,
        role: str,
        text: str,
        prompt_used: str = "",
        audio_file_path: str = None,
    ) -> str:
        """Append a message to session and return message ID"""
        session_data = self.load_session(session_id)
        if not session_data:
            return ""

        # Generate unique message ID using timestamp in milliseconds
        import time

        message_id = str(int(time.time() * 1000))

        message = {
            "id": message_id,
            "role": role,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "prompt_used": prompt_used,
        }

        # Add audio file path if provided
        if audio_file_path:
            message["audio_file_path"] = audio_file_path

        session_data["messages"].append(message)

        # Initialize audio_files dict if not exists
        if "audio_files" not in session_data:
            session_data["audio_files"] = {}

        # Add to audio_files mapping if audio provided
        if audio_file_path:
            session_data["audio_files"][message_id] = audio_file_path.split("/")[
                -1
            ]  # Just filename

        success = self.save_session(session_data)
        return message_id if success else ""

    def save_supervisor(self, session_id: str, output: Dict[str, Any]) -> bool:
        """Save supervisor output to session"""
        session_data = self.load_session(session_id)
        if not session_data:
            return False

        supervisor_entry = {"timestamp": datetime.now().isoformat(), "output": output}

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

        session_data["metadata"]["safety_flags"].append(
            {"flag": flag, "timestamp": datetime.now().isoformat()}
        )
        return self.save_session(session_data)

    def update_session_models(
        self,
        session_id: str,
        therapist_model: str,
        supervisor_model: str,
        therapist_provider: str = "openai",
        supervisor_provider: str = "gemini",
    ) -> bool:
        """Update session with current model information"""
        session_data = self.load_session(session_id)
        if not session_data:
            return False

        session_data["metadata"]["models_used"] = {
            "therapist": {
                "model": therapist_model,
                "provider": therapist_provider,
                "updated_at": datetime.now().isoformat(),
            },
            "supervisor": {
                "model": supervisor_model,
                "provider": supervisor_provider,
                "updated_at": datetime.now().isoformat(),
            },
        }
        return self.save_session(session_data)

    def list_sessions(self) -> List[str]:
        """List all available session IDs"""
        # List all session directories in logs/
        session_dirs = [
            d for d in self.logs_dir.iterdir() if d.is_dir() and (d / "session.json").exists()
        ]
        return [d.name for d in session_dirs]

    @staticmethod
    def save_prompt(stage: str, prompt_text: str, review: str = "") -> str:
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
            "active": True,
        }

        if prompt_file.exists():
            with open(prompt_file, "r", encoding="utf-8") as f:
                prompts = json.load(f)

            for prompt in prompts:
                prompt["active"] = False
        else:
            prompts = []

        prompts.append(new_prompt)

        with open(prompt_file, "w", encoding="utf-8") as f:
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

    def update_audio_config(
        self, session_id: str, audio_enabled: bool, tts_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update session with current audio configuration"""
        session_data = self.load_session(session_id)
        if not session_data:
            return False

        # Initialize audio config if doesn't exist
        if "audio_config" not in session_data:
            session_data["audio_config"] = {}

        session_data["audio_config"]["enabled"] = audio_enabled
        if tts_config:
            # Don't store API key for security - only voice_id and other settings
            safe_config = {k: v for k, v in tts_config.items() if k != "api_key"}
            session_data["audio_config"]["tts_config"] = safe_config

        return self.save_session(session_data)

    def get_audio_config(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get audio configuration from session"""
        session_data = self.load_session(session_id)
        if not session_data:
            return None

        return session_data.get("audio_config")

    # === AUDIO FILE MANAGEMENT ===

    def ensure_session_audio_dir(self, session_id: str) -> Path:
        """Ensure audio directory exists for session and return path"""
        session_dir = self.logs_dir / session_id
        audio_dir = session_dir / "audio"

        session_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)

        return audio_dir

    def save_audio_file(self, session_id: str, message_id: str, audio_data: bytes) -> Optional[str]:
        """
        Save audio data to disk and return relative file path.

        Args:
            session_id: Session identifier
            message_id: Message identifier (timestamp in ms)
            audio_data: MP3 audio data

        Returns:
            Relative path to saved file or None if failed
        """
        if not audio_data:
            return None

        try:
            audio_dir = self.ensure_session_audio_dir(session_id)
            filename = f"msg_{message_id}.mp3"
            file_path = audio_dir / filename

            # Save audio data
            with open(file_path, "wb") as f:
                f.write(audio_data)

            # Return relative path for portability
            return f"logs/{session_id}/audio/{filename}"

        except Exception as e:
            print(f"Error saving audio file: {e}")
            return None

    def get_audio_file_path(self, session_id: str, message_id: str) -> Optional[Path]:
        """Get full path to audio file if it exists"""
        audio_dir = self.logs_dir / session_id / "audio"
        file_path = audio_dir / f"msg_{message_id}.mp3"

        return file_path if file_path.exists() else None

    def audio_file_exists(self, session_id: str, message_id: str) -> bool:
        """Check if audio file exists for message"""
        return self.get_audio_file_path(session_id, message_id) is not None

    def save_session_log(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Save session data to logs directory (session.json)"""
        try:
            session_dir = self.logs_dir / session_id
            session_dir.mkdir(parents=True, exist_ok=True)

            log_file = session_dir / "session.json"
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"Error saving session log: {e}")
            return False
