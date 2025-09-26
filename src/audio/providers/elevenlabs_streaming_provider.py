"""ElevenLabs Streaming TTS provider for real-time audio."""

import json
import asyncio
import websockets
import base64
import uuid
from typing import AsyncIterator, Optional, Dict, Any
import streamlit as st


class ElevenLabsStreamingProvider:
    """Real-time streaming TTS provider using ElevenLabs streaming API."""

    def __init__(self, api_key: str, voice_id: str = "JBFqnCBsd6RMkjVDRZzb"):
        """
        Initialize streaming provider.

        Args:
            api_key: ElevenLabs API key
            voice_id: Voice ID to use for TTS
        """
        self.api_key = api_key
        self.voice_id = voice_id
        self.websocket_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id=eleven_flash_v2_5"

    def is_available(self) -> bool:
        """Check if streaming TTS is available."""
        return bool(self.api_key and self.voice_id)

    async def stream_text_to_speech(self, text_chunks: AsyncIterator[str]) -> AsyncIterator[bytes]:
        """
        Stream text chunks to ElevenLabs and yield audio chunks in real-time.

        Args:
            text_chunks: Async iterator of text chunks from therapist response

        Yields:
            Audio chunks as bytes (MP3 format)
        """
        if not self.is_available():
            return

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with websockets.connect(
                self.websocket_url, extra_headers=headers, ping_interval=20, ping_timeout=10
            ) as websocket:

                # Send initial configuration
                config_message = {
                    "text": " ",  # Start with a space
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.8,
                        "style": 0.0,
                        "use_speaker_boost": True,
                    },
                    "generation_config": {"chunk_length_schedule": [120, 160, 250, 290]},
                    "xi_api_key": self.api_key,
                }

                await websocket.send(json.dumps(config_message))

                # Create tasks for sending and receiving
                send_task = asyncio.create_task(self._send_text_chunks(websocket, text_chunks))
                receive_task = asyncio.create_task(self._receive_audio_chunks(websocket))

                # Process audio chunks as they arrive
                try:
                    async for audio_chunk in self._receive_audio_chunks(websocket):
                        yield audio_chunk
                except websockets.exceptions.ConnectionClosed:
                    pass
                finally:
                    # Clean up tasks
                    send_task.cancel()
                    receive_task.cancel()

                    try:
                        await send_task
                    except asyncio.CancelledError:
                        pass

                    try:
                        await receive_task
                    except asyncio.CancelledError:
                        pass

        except Exception as e:
            st.error(f"Streaming TTS error: {e}")
            return

    async def _send_text_chunks(self, websocket, text_chunks: AsyncIterator[str]):
        """Send text chunks to WebSocket."""
        try:
            async for chunk in text_chunks:
                if chunk.strip():
                    message = {"text": chunk, "try_trigger_generation": True}
                    await websocket.send(json.dumps(message))
                    await asyncio.sleep(0.01)  # Small delay to prevent overwhelming

            # Send EOS (End of Stream) message
            await websocket.send(json.dumps({"text": ""}))

        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Error sending text chunks: {e}")

    async def _receive_audio_chunks(self, websocket) -> AsyncIterator[bytes]:
        """Receive and decode audio chunks from WebSocket."""
        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)

                # Check for audio data
                if "audio" in data:
                    # Decode base64 audio data
                    audio_chunk = base64.b64decode(data["audio"])
                    yield audio_chunk

                # Check for errors
                elif "error" in data:
                    print(f"ElevenLabs streaming error: {data['error']}")
                    break

                # Check for end of stream
                elif data.get("isFinal", False):
                    break

        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Error receiving audio chunks: {e}")


class StreamingAudioManager:
    """Manages real-time audio streaming in Streamlit."""

    def __init__(self, session_key: str = "streaming_audio_queue"):
        self.session_key = session_key
        self.queue_id = str(uuid.uuid4())

        # Initialize session state for audio queue
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {}

    def add_audio_chunk(self, audio_chunk: bytes) -> str:
        """
        Add audio chunk to session state queue for JavaScript consumption.

        Returns:
            Chunk ID for tracking
        """
        chunk_id = str(uuid.uuid4())

        # Encode audio chunk as base64 for JavaScript
        audio_b64 = base64.b64encode(audio_chunk).decode("utf-8")

        # Add to queue
        if self.queue_id not in st.session_state[self.session_key]:
            st.session_state[self.session_key][self.queue_id] = []

        st.session_state[self.session_key][self.queue_id].append(
            {
                "id": chunk_id,
                "audio_data": audio_b64,
                "timestamp": (
                    asyncio.get_event_loop().time() if hasattr(asyncio, "_get_running_loop") else 0
                ),
            }
        )

        return chunk_id

    def get_audio_queue_id(self) -> str:
        """Get current queue ID for JavaScript access."""
        return self.queue_id

    def clear_queue(self):
        """Clear the current audio queue."""
        if self.queue_id in st.session_state[self.session_key]:
            del st.session_state[self.session_key][self.queue_id]

    def render_streaming_audio_player(self):
        """Render JavaScript component for streaming audio playback."""
        import json

        # Get current queue data
        queue_data = st.session_state[self.session_key].get(self.queue_id, [])
        queue_json = json.dumps(queue_data)

        audio_player_html = f"""
        <div id="streaming-audio-player-{self.queue_id}" data-audio-queue='{queue_json}'>
            <div id="audio-status-{self.queue_id}" style="
                padding: 5px 10px;
                background: rgba(0, 255, 0, 0.1);
                border-radius: 5px;
                font-size: 0.8em;
                margin: 5px 0;
                display: none;
            ">🎵 Odtwarzam audio w czasie rzeczywistym...</div>
        </div>

        <script>
        (function() {{
            const queueId = "{self.queue_id}";
            const sessionKey = "{self.session_key}";

            // Audio context and management
            let audioContext = null;
            let audioQueue = [];
            let isPlaying = false;
            let nextStartTime = 0;

            // Initialize audio context on first user interaction
            function initAudioContext() {{
                if (!audioContext) {{
                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    console.log("🎵 Audio context initialized");
                }}
                return audioContext;
            }}

            // Play audio chunk immediately
            async function playAudioChunk(audioData) {{
                try {{
                    const context = initAudioContext();
                    if (context.state === 'suspended') {{
                        await context.resume();
                    }}

                    // Decode base64 audio data
                    const binaryString = atob(audioData);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {{
                        bytes[i] = binaryString.charCodeAt(i);
                    }}

                    // Decode audio
                    const audioBuffer = await context.decodeAudioData(bytes.buffer.slice());

                    // Create source and play
                    const source = context.createBufferSource();
                    source.buffer = audioBuffer;
                    source.connect(context.destination);

                    // Schedule playback
                    const now = context.currentTime;
                    const startTime = Math.max(now, nextStartTime);
                    source.start(startTime);

                    // Update next start time
                    nextStartTime = startTime + audioBuffer.duration;

                    // Show status
                    const statusDiv = document.getElementById("audio-status-{self.queue_id}");
                    if (statusDiv) {{
                        statusDiv.style.display = 'block';
                        setTimeout(() => {{
                            statusDiv.style.display = 'none';
                        }}, audioBuffer.duration * 1000 + 500);
                    }}

                    console.log(`🎵 Playing audio chunk (duration: ${{audioBuffer.duration.toFixed(2)}}s)`);

                }} catch (error) {{
                    console.error("Error playing audio chunk:", error);
                }}
            }}

            // Check for new audio chunks periodically via data attributes
            function checkForAudioChunks() {{
                const playerDiv = document.getElementById(`streaming-audio-player-${{queueId}}`);
                if (!playerDiv) return;

                const audioData = playerDiv.getAttribute('data-audio-queue');
                if (!audioData) return;

                try {{
                    const audioQueue = JSON.parse(audioData);

                    // Process new chunks
                    audioQueue.forEach(chunk => {{
                        if (!chunk.processed) {{
                            playAudioChunk(chunk.audio_data);
                            chunk.processed = true;
                        }}
                    }});

                    // Update processed state back
                    playerDiv.setAttribute('data-audio-queue', JSON.stringify(audioQueue));
                }} catch (e) {{
                    console.error("Error parsing audio queue:", e);
                }}
            }}

            // Check every 100ms for new chunks
            const intervalId = setInterval(checkForAudioChunks, 100);

            // Initialize on first click anywhere
            document.addEventListener('click', initAudioContext, {{ once: true }});

            // Cleanup on page unload
            window.addEventListener('beforeunload', () => {{
                clearInterval(intervalId);
                if (audioContext) {{
                    audioContext.close();
                }}
            }});

            console.log("🎵 Streaming audio player initialized for queue:", queueId);
        }})();
        </script>
        """

        st.markdown(audio_player_html, unsafe_allow_html=True)
