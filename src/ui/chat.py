"""Chat display functionality for Psychia TSR"""

from typing import Optional, Dict

import streamlit as st
from dotenv import load_dotenv

from src.core.session import format_timestamp
from src.core.workflow import send_supervisor_request_stream
from src.ui.technical_log_display import add_technical_log

# Audio imports
try:
    from src.audio.services.audio_service import AudioService
    from src.ui.audio.audio_config_widget import AudioConfigWidget
    from src.ui.audio.webrtc_widget import WebRTCWidget

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# Always available fallback
from src.ui.audio.fallback_audio_widget import FallbackAudioWidget

load_dotenv()


def display_chat_interface() -> None:
    """Display main chat interface with message history and streaming support."""

    # Audio service setup (only if enabled and available)
    audio_service = None
    if AUDIO_AVAILABLE and st.session_state.get("audio_enabled", False):
        audio_service = AudioService()
        add_technical_log("audio_status", "🎵 Audio service aktywny na stronie konwersacji")

        # Set up audio - prioritize HTML5 over WebRTC for playback-only
        tts_config = st.session_state.get("_tts_cfg")
        if tts_config and tts_config.get("api_key") and tts_config.get("voice_id"):

            # Check user preference for audio mode
            prefer_webrtc = st.session_state.get("webrtc_mode", False)
            use_fallback = st.session_state.get("fallback_mode", True)

            if prefer_webrtc:
                # Try WebRTC first if user explicitly wants it
                try:
                    from src.ui.audio.webrtc_widget import WebRTCWidget

                    webrtc_widget = WebRTCWidget(audio_service)
                    pcm_buffer = webrtc_widget.ensure_pcm_buffer()

                    # Only render WebRTC streamer if we have a valid ElevenLabs config
                    webrtc_widget.render_webrtc_streamer(pcm_buffer)
                    add_technical_log(
                        "audio_status",
                        f"🎙️ WebRTC aktywne (Voice: {tts_config.get('voice_id', 'unknown')})",
                    )

                except Exception as e:
                    add_technical_log("audio_error", f"❌ Błąd WebRTC: {str(e)}")

                    # Show fallback option
                    with st.expander("🔧 Alternatywne rozwiązania audio", expanded=False):
                        st.info(
                            """💡 **WebRTC nie działa? Wypróbuj te rozwiązania:**

**Natychmiastowe:**
1. Odśwież stronę (F5) i zezwól na uprawnienia audio
2. Spróbuj przeglądarki Chrome lub Edge
3. Wyłącz blokery reklam na tej stronie

**Diagnostyka:**
4. Sprawdź czy inne strony z audio działają
5. Przetestuj mikrofon w ustawieniach systemu
6. Sprawdź czy słuchawki/głośniki są podłączone

**Alternatywa:**
Przełącz na HTML5 Audio w Ustawieniach - nie wymaga mikrofonu.
                        """
                        )

                        FallbackAudioWidget.show_browser_compatibility()

            elif use_fallback:
                # Use HTML5 Audio - no microphone required!
                add_technical_log(
                    "audio_status",
                    f"🎙️ HTML5 Audio aktywne (Voice: {tts_config.get('voice_id', 'unknown')})",
                )

        elif st.session_state.get("audio_enabled", False):
            add_technical_log("audio_warning", "⚠️ Audio włączone ale brak konfiguracji TTS")
    elif st.session_state.get("audio_enabled", False):
        add_technical_log("audio_error", "❌ Audio włączone ale moduł niedostępny")

    # Create a scrollable container for messages
    messages_container = st.container(height=750)

    with messages_container:
        conversation_container = st.container()
        streaming_container = st.container()

        with conversation_container:
            # ALWAYS show conversation history first
            if "conversation_manager" in st.session_state:
                conversation = (
                    st.session_state.conversation_manager.get_full_conversation_for_display()
                )

                for message in conversation:
                    # Check if this is a pending message
                    is_pending = getattr(message, "is_pending", False)

                    # Render message with appropriate avatar
                    avatar = "💚" if message.role == "therapist" else None
                    with st.chat_message(message.role, avatar=avatar):
                        # Message content in main column
                        col_content, col_audio = st.columns([9, 1])

                        with col_content:
                            content = message.text
                            if is_pending:
                                content += " ⏳"  # Add pending indicator
                            st.write(content)

                        # Audio play button for therapist messages (if audio file exists)
                        with col_audio:
                            if (
                                message.role == "therapist"
                                and hasattr(message, "audio_file_path")
                                and message.audio_file_path
                            ):
                                _render_audio_play_button(message)

                    # Show timestamp and response times for all messages
                    if hasattr(message, "timestamp"):
                        caption_parts = [f"🕒 {format_timestamp(message.timestamp)}"]

                        # Add response times for therapist messages
                        if message.role == "therapist":
                            response_times = _get_response_times_for_message(message)
                            if response_times:
                                sup_time = response_times.get("supervisor_time_ms", 0)
                                ther_time = response_times.get("therapist_time_ms", 0)
                                first_chunk_time = response_times.get("first_chunk_time_ms")

                                if sup_time > 0 or ther_time > 0:
                                    time_parts = []
                                    if sup_time > 0:
                                        time_parts.append(f"SUP: {sup_time/1000:.2f}s")
                                    if first_chunk_time is not None:
                                        time_parts.append(
                                            f"1st: {first_chunk_time/1000:.2f}s - {(sup_time+first_chunk_time)/1000:.2f} from start"
                                        )
                                    if ther_time > 0:
                                        time_parts.append(f"THE: {ther_time/1000:.2f}s")

                                    time_str = f"({', '.join(time_parts)})"
                                    caption_parts.append(time_str)

                        st.caption(" ".join(caption_parts))

        # Show streaming response AFTER conversation history
        if (
            hasattr(st.session_state, "processing_message")
            and st.session_state.processing_message
            and "stream_generator" in st.session_state
        ):
            with streaming_container:
                with st.chat_message("therapist", avatar="💚"):
                    # Collect streamed content
                    full_response = ""
                    response_placeholder = st.empty()

                    # Set up TTS router if audio is enabled and configured
                    tts_router = None
                    use_html5_audio = False
                    accumulated_text = ""  # For HTML5 audio batch processing

                    if (
                        audio_service
                        and st.session_state.get("audio_enabled", False)
                        and st.session_state.get("_tts_cfg")
                    ):

                        tts_config = st.session_state["_tts_cfg"]
                        prefer_webrtc = st.session_state.get("webrtc_mode", False)
                        use_fallback = st.session_state.get("fallback_mode", True)

                        if prefer_webrtc:
                            # Try WebRTC TTS router
                            pcm_buffer = st.session_state.get("pcm_buffer")
                            if pcm_buffer:
                                tts_router = audio_service.create_tts_router(tts_config, pcm_buffer)
                                add_technical_log("audio_tts", "🎵 TTS WebRTC router aktywny")
                            else:
                                use_html5_audio = True
                        elif use_fallback:
                            # Use HTML5 audio mode
                            use_html5_audio = True
                            add_technical_log("audio_tts", "🎵 TTS HTML5 mode aktywny")

                    # Consume ALL chunks to let workflow generator complete
                    for chunk in st.session_state.stream_generator:
                        if isinstance(chunk, str):
                            full_response += chunk
                            response_placeholder.write(full_response)

                            # Feed text to TTS if enabled (WebRTC mode)
                            if tts_router:
                                # WebRTC streaming mode
                                tts_router.feed(chunk)
                            elif use_html5_audio:
                                # HTML5 batch mode - accumulate text for post-streaming
                                accumulated_text += chunk
                        # Allow generator to complete and execute commit logic

                    # Finalize TTS processing
                    if tts_router:
                        tts_router.flush_and_close()
                        add_technical_log(
                            "audio_tts",
                            f"🎵 TTS WebRTC zakończone - wygenerowano audio dla {len(full_response)} znaków",
                        )
                    elif use_html5_audio and accumulated_text.strip():
                        # Generate and save audio file (no auto-player, just for 🔊 button)
                        add_technical_log(
                            "audio_debug",
                            f"🎵 Generuję audio dla przycisku play: {len(accumulated_text)} znaków",
                        )

                    # Store the final response in session state for persistence
                    st.session_state.last_streamed_response = full_response

                    # Store audio generation data for post-streaming processing
                    if use_html5_audio and accumulated_text.strip() and tts_config:
                        st.session_state.pending_audio_generation = {
                            "text": accumulated_text.strip(),
                            "tts_config": tts_config,
                        }

                    # Mark that we should rerun after streaming completes
                    st.session_state.stream_refresh_pending = True

                # Clear the processing state after streaming
                st.session_state.pop("processing_message", None)
                st.session_state.pop("stream_generator", None)

        # Auto-scroll to bottom by adding empty space at the end
        st.empty()

    # Process pending audio generation after streaming completes
    if hasattr(st.session_state, "pending_audio_generation"):
        audio_data = st.session_state.pending_audio_generation
        st.session_state.pop("pending_audio_generation", None)

        # Generate and save audio to disk
        _process_and_save_audio(audio_data["text"], audio_data["tts_config"])

    # Trigger a rerun once after streaming completes to refresh the conversation
    if st.session_state.pop("stream_refresh_pending", False):
        st.rerun()

    # Check if we need to process a pending message
    if hasattr(st.session_state, "pending_user_message") and st.session_state.pending_user_message:
        prompt = st.session_state.pending_user_message
        st.session_state.pending_user_message = None

        # Add user message to ConversationManager for immediate display
        if "conversation_manager" in st.session_state:
            st.session_state.conversation_manager.accept_user_input(prompt)

        # Initialize agents if needed (lazy loading)
        if st.session_state.therapist_agent is None:
            with st.spinner("🤖 Inicjalizuję agentów terapii..."):
                from src.core.workflow import initialize_agents

                if not initialize_agents():
                    st.error("Nie można zainicjować agentów terapii")
                    return

        # Set up streaming
        with st.spinner("🔍 Konsultuję z supervisorem..."):
            st.session_state.processing_message = True
            st.session_state.stream_generator = send_supervisor_request_stream(prompt)

        # Rerun to show streaming
        st.rerun()

    # Chat input - always at the bottom
    if prompt := st.chat_input("Napisz swoją wiadomość..."):
        # Create new session if none exists
        if not st.session_state.session_id:
            from src.core.session import create_new_session

            create_new_session()
            add_technical_log(
                "info", f"🆕 Nowa sesja utworzona automatycznie: {st.session_state.session_id}"
            )

        # Initialize ConversationManager if needed
        if "conversation_manager" not in st.session_state:
            from src.core.conversation import ConversationManager

            st.session_state.conversation_manager = ConversationManager()

        # Log user message immediately
        add_technical_log("info", f"👤 Użytkownik: {prompt}")

        # Set pending message for processing on next rerun
        st.session_state.pending_user_message = prompt

        # Force immediate refresh to show user message
        st.rerun()

    st.divider()


def display_stage_controls():
    """Display stage navigation controls below chat"""
    from src.core.session import advance_stage

    st.subheader("🎯 Kontrola etapu terapii")

    # Stage navigation buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("⬅️ Poprzedni etap", use_container_width=True):
            if advance_stage("previous"):
                # Force agents reinitialization with new stage prompts
                _reinitialize_agents_for_new_stage()
            st.rerun()

    with col2:
        if st.button("➡️ Następny etap", use_container_width=True):
            if advance_stage("next"):
                # Force agents reinitialization with new stage prompts
                _reinitialize_agents_for_new_stage()
            st.rerun()

    with col3:
        st.caption("Zmiana etapu automatycznie odnowi prompty systemowe")


def _reinitialize_agents_for_new_stage():
    """Reinitialize agents to load new stage prompts"""
    # Clear existing agents to force reinitialization with new prompts
    st.session_state.therapist_agent = None
    st.session_state.supervisor_agent = None

    # Log stage change
    add_technical_log(
        "stage_transition", f"🔄 Agents reinitialized for stage: {st.session_state.current_stage}"
    )


def _render_audio_play_button(message) -> None:
    """Render audio play button for therapist message."""
    try:
        # Check if audio file exists on disk
        session_id = st.session_state.get("session_id")
        if not session_id:
            return

        message_id = getattr(message, "id", None)
        if not message_id:
            return

        from src.infrastructure.storage import StorageProvider
        from config import Config

        config = Config.get_instance()

        storage = StorageProvider(config.LOGS_DIR)
        audio_path = storage.get_audio_file_path(session_id, message_id)

        if audio_path and audio_path.exists():
            # Use unique key for each button to avoid conflicts
            button_key = f"play_audio_{message_id}"

            if st.button("🔊", help="Odtwórz audio", key=button_key):
                # Read audio file and display player
                with open(audio_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()

                # Show audio player
                st.audio(audio_bytes, format="audio/mp3")
                add_technical_log("audio_play", f"🎵 Odtwarzanie audio dla wiadomości {message_id}")

    except Exception as e:
        # Silent fail for audio button issues
        pass


def _process_and_save_audio(text: str, tts_config: dict) -> None:
    """Generate TTS audio and save to disk for the last therapist message."""
    try:
        add_technical_log(
            "audio_debug", f"🎵 Rozpoczynam generowanie i zapisywanie audio dla {len(text)} znaków"
        )

        # Generate TTS audio data
        from src.audio.providers.elevenlabs_provider import ElevenLabsTTSProvider
        from src.infrastructure.storage import StorageProvider
        from config import Config

        tts_provider = ElevenLabsTTSProvider(
            api_key=tts_config.get("api_key"), voice_id=tts_config.get("voice_id")
        )

        if not tts_provider.is_available():
            add_technical_log(
                "audio_error",
                f"❌ ElevenLabs niedostępne - API key: {'tak' if tts_config.get('api_key') else 'nie'}",
            )
            return

        # Generate MP3 audio
        audio_data = tts_provider.text_to_speech(text.strip())
        if not audio_data:
            add_technical_log("audio_error", "❌ Puste dane audio z ElevenLabs")
            return

        add_technical_log(
            "audio_debug", f"🎵 Audio wygenerowane, rozmiar: {len(audio_data)} bajtów"
        )

        # Get current session and last message
        session_id = st.session_state.get("session_id")
        if not session_id:
            add_technical_log("audio_error", "❌ Brak session_id dla zapisania audio")
            return

        # Get the last message from conversation manager (should be therapist response)
        if "conversation_manager" not in st.session_state:
            add_technical_log("audio_error", "❌ Brak conversation_manager dla audio")
            return

        conversation = st.session_state.conversation_manager.get_full_conversation_for_display()
        if not conversation:
            add_technical_log("audio_error", "❌ Pusta konwersacja dla audio")
            return

        # Find the last therapist message
        last_therapist_msg = None
        for msg in reversed(conversation):
            if msg.role == "therapist":
                last_therapist_msg = msg
                break

        if not last_therapist_msg:
            add_technical_log("audio_error", "❌ Nie znaleziono wiadomości terapeuty dla audio")
            return

        # Generate message ID if not exists
        message_id = getattr(last_therapist_msg, "id", None)
        if not message_id:
            import time

            message_id = str(int(time.time() * 1000))
            last_therapist_msg.id = message_id  # Add ID to the message

        # Save audio file to disk
        config = Config.get_instance()
        storage = StorageProvider(config.LOGS_DIR)
        audio_file_path = storage.save_audio_file(session_id, message_id, audio_data)

        if audio_file_path:
            # Update the message with audio file path
            last_therapist_msg.audio_file_path = audio_file_path
            add_technical_log(
                "audio_tts", f"🎵 Audio zapisane: {audio_file_path} ({len(audio_data)} bajtów)"
            )

            # Also save updated session to logs directory
            try:
                session_data = storage.load_session(session_id)
                if session_data:
                    storage.save_session_log(session_id, session_data)
            except Exception as e:
                add_technical_log("audio_warning", f"⚠️ Błąd zapisywania sesji do logs: {str(e)}")
        else:
            add_technical_log("audio_error", "❌ Błąd zapisywania pliku audio")

    except Exception as e:
        add_technical_log("audio_error", f"❌ Błąd procesowania audio: {str(e)}")


def _get_latest_response_times() -> Optional[Dict[str, int]]:
    """Get the latest supervisor and therapist response times from technical logs."""
    try:
        # Try to get from session_data first
        if hasattr(st.session_state, "session_data") and st.session_state.session_data:
            technical_logs = st.session_state.session_data.get("technical_logs", [])
        # Fallback to logger in session state
        elif hasattr(st.session_state, "therapy_session_logger"):
            logger = st.session_state.therapy_session_logger
            if hasattr(logger, "get_logs"):
                log_entries = logger.get_logs()
                technical_logs = [
                    entry.__dict__ if hasattr(entry, "__dict__") else entry for entry in log_entries
                ]
            else:
                return None
        else:
            return None

        # Find the most recent supervisor and therapist response times
        supervisor_time = None
        therapist_time = None
        first_chunk_time = None

        # Reverse iterate to find most recent times
        for log_entry in reversed(technical_logs):
            if supervisor_time is None and log_entry.get("event_type") == "supervisor_response":
                supervisor_time = log_entry.get("response_time_ms")

            if therapist_time is None and log_entry.get("event_type") == "therapist_response":
                therapist_time = log_entry.get("response_time_ms")
                # Get first chunk time from the same entry
                entry_data = log_entry.get("data", {})
                if isinstance(entry_data, dict):
                    first_chunk_time = entry_data.get("first_chunk_time_ms")

            # Stop when we have both times
            if supervisor_time is not None and therapist_time is not None:
                break

        if supervisor_time is not None or therapist_time is not None:
            result = {
                "supervisor_time_ms": supervisor_time or 0,
                "therapist_time_ms": therapist_time or 0,
            }
            if first_chunk_time is not None:
                result["first_chunk_time_ms"] = first_chunk_time
            return result

        return None

    except Exception:
        # Silently fail if we can't get response times
        return None


def _get_response_times_for_message(message):
    """Get response times that correspond to a specific message by finding matching timestamp."""
    try:
        technical_logs = st.session_state.get("technical_log", [])
        if not technical_logs or not hasattr(message, "timestamp"):
            return None

        message_timestamp = message.timestamp
        if not message_timestamp:
            return None

        # Convert message timestamp to comparable format
        from datetime import datetime

        try:
            if message_timestamp.endswith("Z"):
                msg_dt = datetime.fromisoformat(message_timestamp.replace("Z", "+00:00"))
            else:
                msg_dt = datetime.fromisoformat(message_timestamp)
        except Exception:
            return None

        # Find the closest therapist_response log entry to this message timestamp
        best_match = None
        min_time_diff = float("inf")

        for log_entry in technical_logs:
            if log_entry.get("event_type") != "therapist_response":
                continue

            log_timestamp = log_entry.get("timestamp")
            if not log_timestamp:
                continue

            try:
                if log_timestamp.endswith("Z"):
                    log_dt = datetime.fromisoformat(log_timestamp.replace("Z", "+00:00"))
                else:
                    log_dt = datetime.fromisoformat(log_timestamp)

                time_diff = abs((log_dt - msg_dt).total_seconds())

                # Find the log entry closest in time to the message (within 10 seconds)
                if time_diff < min_time_diff and time_diff < 10:
                    min_time_diff = time_diff
                    best_match = log_entry
            except Exception:
                continue

        if not best_match:
            return None

        # Get therapist response times from the matched log entry
        therapist_time = best_match.get("response_time_ms")
        entry_data = best_match.get("data", {})
        first_chunk_time = (
            entry_data.get("first_chunk_time_ms") if isinstance(entry_data, dict) else None
        )

        # Find the supervisor response that occurred just before this therapist response
        supervisor_time = None
        best_match_timestamp = best_match.get("timestamp")

        for log_entry in technical_logs:
            if log_entry.get("event_type") != "supervisor_response":
                continue

            log_timestamp = log_entry.get("timestamp")
            if log_timestamp and log_timestamp < best_match_timestamp:
                # This supervisor response occurred before our therapist response
                supervisor_time = log_entry.get("response_time_ms")

        if therapist_time is not None:
            result = {
                "supervisor_time_ms": supervisor_time or 0,
                "therapist_time_ms": therapist_time or 0,
            }
            if first_chunk_time is not None:
                result["first_chunk_time_ms"] = first_chunk_time
            return result

        return None

    except Exception:
        # Silently fail if we can't get response times
        return None
