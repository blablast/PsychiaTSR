"""Clean session service - decoupled from UI framework."""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .interfaces.session_context_interface import ISessionContext, IUINotifier
from .interfaces.session_provider_interface import ISessionProvider
from ..services.simple_service_factory import SimpleServiceFactory
from ..models.schemas import MessageData


class SessionService:
    """
    Clean session service using dependency injection.

    Eliminates Streamlit coupling by using interfaces:
    - ISessionContext: Access to session state
    - IUINotifier: UI notifications
    - ISessionProvider: Session storage
    """

    def __init__(self,
                 session_context: ISessionContext,
                 ui_notifier: IUINotifier,
                 session_provider: ISessionProvider = None):
        """Initialize service with injected dependencies."""
        self.session_context = session_context
        self.ui_notifier = ui_notifier
        self.session_provider = session_provider or SimpleServiceFactory.create_storage_provider()
        self.logger = SimpleServiceFactory.create_logger()

    def create_new_session(self, user_message: str = None) -> str:
        """Create new session with decoupled logic."""
        try:
            # Get agent configurations through interface
            therapist_config = self.session_context.get_agent_config("therapist")
            supervisor_config = self.session_context.get_agent_config("supervisor")

            # Create session
            session_data = {
                "user_id": "streamlit_user",
                "session_type": "therapy",
                "therapist_config": therapist_config,
                "supervisor_config": supervisor_config,
                "created_at": datetime.now().isoformat(),
                "messages": []
            }

            # Add initial user message if provided
            if user_message:
                session_data["messages"] = [{
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.now().isoformat()
                }]

            # Save session
            session_id = self.session_provider.create_session(session_data)

            # Update session context
            self.session_context.set_session_value("session_id", session_id)

            # Initialize messages in session context
            if user_message:
                initial_message = {
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.now().isoformat()
                }
                self.session_context.add_message(initial_message)

            # Clear technical log
            self.session_context.set_session_value("technical_log", [])

            self.ui_notifier.show_success(f"Nowa sesja utworzona: {session_id}")

            if self.logger:
                self.logger.log_info(f"New session created: {session_id}")

            return session_id

        except Exception as e:
            error_message = f"Błąd tworzenia sesji: {str(e)}"
            self.ui_notifier.show_error(error_message)

            if self.logger:
                self.logger.log_error(f"Session creation failed: {str(e)}")

            raise

    def save_session_data(self) -> None:
        """Save current session data through decoupled interface."""
        try:
            session_id = self.session_context.get_session_id()
            if not session_id:
                self.ui_notifier.show_warning("Brak aktywnej sesji do zapisania")
                return

            # Get current session data
            messages = self.session_context.get_messages()
            current_stage = self.session_context.get_current_stage()

            # Prepare data for saving
            session_data = {
                "messages": messages,
                "current_stage": current_stage,
                "last_updated": datetime.now().isoformat()
            }

            # Save through session provider
            result = self.session_provider.update_session(session_id, session_data)

            if result.success:
                self.ui_notifier.show_success(result.message)
            else:
                self.ui_notifier.show_error(result.message)

        except Exception as e:
            error_message = f"Błąd zapisywania sesji: {str(e)}"
            self.ui_notifier.show_error(error_message)

            if self.logger:
                self.logger.log_error(f"Session save failed: {str(e)}")

    def get_stage_info_for_current_session(self) -> Optional[Dict[str, Any]]:
        """Get stage information for current session."""
        try:
            current_stage = self.session_context.get_current_stage()
            stage_manager = SimpleServiceFactory.create_stage_manager()
            stages = stage_manager.get_all_stages()

            return next((stage for stage in stages if stage["id"] == current_stage), None)

        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to get stage info: {str(e)}")
            return None

    def setup_conversation_context(self) -> None:
        """Setup conversation context for current session."""
        try:
            # Initialize messages if not present
            if not self.session_context.has_session_value("messages"):
                self.session_context.set_session_value("messages", [])

            # Add stage change message if needed
            current_stage = self.session_context.get_current_stage()
            stage_info = self.get_stage_info_for_current_session()

            if stage_info:
                stage_message = {
                    "role": "system",
                    "content": f"Przejście do etapu: {stage_info.get('name', current_stage)}",
                    "timestamp": datetime.now().isoformat(),
                    "stage": current_stage
                }

                # Add to beginning of messages
                messages = self.session_context.get_messages()
                messages.insert(0, stage_message)

        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to setup conversation context: {str(e)}")

    def get_audio_configuration(self) -> Dict[str, Any]:
        """Get audio configuration for current session."""
        audio_enabled = self.session_context.get_session_value('audio_enabled', False)
        tts_config = self.session_context.get_session_value('_tts_cfg', {})

        return {
            "audio_enabled": audio_enabled,
            "tts_config": tts_config,
            "has_valid_config": bool(tts_config.get("api_key") and tts_config.get("voice_id"))
        }

    def clear_technical_logs(self) -> None:
        """Clear technical logs for current session."""
        try:
            self.session_context.set_session_value("technical_log", [])

            if self.logger:
                self.logger.log_info("Technical logs cleared")

        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to clear technical logs: {str(e)}")

    def get_conversation_messages_as_data(self) -> List[MessageData]:
        """Convert session messages to MessageData objects."""
        try:
            messages = self.session_context.get_messages()

            message_data_list = []
            for msg in messages:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    message_data = MessageData(
                        role=msg["role"],
                        text=msg["content"],
                        timestamp=msg.get("timestamp", datetime.now().isoformat())
                    )
                    message_data_list.append(message_data)

            return message_data_list

        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to convert messages: {str(e)}")
            return []