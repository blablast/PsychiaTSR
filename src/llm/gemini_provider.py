"""Google Gemini provider for cloud LLM inference with conversation memory."""

import os
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
from .base import LLMProvider

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiProvider(LLMProvider):
    """Google Gemini provider using shared base functionality."""

    def __init__(self, model_name: str = "gemini-pro", **kwargs):
        super().__init__(model_name, **kwargs)

        if not GEMINI_AVAILABLE:
            raise ImportError("Google AI package not installed. Install with: pip install google-generativeai")

        self.api_key = kwargs.get('api_key') or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GOOGLE_API_KEY environment variable or pass api_key parameter.")

        # Keep sync client for backward compatibility
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

        # Provider-specific configuration
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

        # Gemini-specific state (for sync API compatibility)
        self.chat_session = None
        self.conversation_history = []  # Separate from base conversation_messages

    def start_conversation(self, system_prompt: Optional[str] = None) -> None:
        """Start a new conversation session with optional system prompt."""
        # Use base class for conversation state
        super().start_conversation(system_prompt)

        # Initialize Gemini-specific session
        self.chat_session = self.model.start_chat(history=[])
        self.conversation_history = []

        # Handle system prompt for sync API
        if system_prompt and not self.system_prompt_set:
            self._set_gemini_system_prompt(system_prompt)

    def _set_gemini_system_prompt(self, system_prompt: str) -> None:
        """Set system prompt for Gemini sync API."""
        if not self.chat_session:
            self.chat_session = self.model.start_chat(history=[])

        try:
            # Send system prompt and get confirmation for sync API
            response = self.chat_session.send_message(
                f"System: {system_prompt}\n\nRespond only with 'OK' to confirm you understand your role."
            )
            self.conversation_history.append(("system", system_prompt))
        except Exception as e:
            raise Exception(f"Failed to set system prompt: {str(e)}")

    def _convert_to_gemini_format(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Convert OpenAI-style messages to Gemini format."""
        gemini_messages = []

        for msg in messages:
            if msg["role"] == "system":
                # System messages become part of instruction or first user message
                continue
            elif msg["role"] == "user":
                gemini_messages.append({
                    "role": "user",
                    "parts": [{"text": msg["content"]}]
                })
            elif msg["role"] == "assistant":
                gemini_messages.append({
                    "role": "model",
                    "parts": [{"text": msg["content"]}]
                })

        return gemini_messages

    def _prepare_gemini_api_params(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Prepare Gemini-specific API parameters."""
        gemini_messages = self._convert_to_gemini_format(messages)

        # Handle system prompt as instruction
        system_instruction = None
        if messages and messages[0]["role"] == "system":
            system_instruction = messages[0]["content"]

        # Prepare common parameters
        common_params = self._prepare_common_params(**kwargs)

        request_data = {
            "contents": gemini_messages,
            "generationConfig": {
                "temperature": common_params["temperature"],
                "maxOutputTokens": common_params["max_tokens"],
                "topP": common_params["top_p"]
            }
        }

        # Add structured output support
        response_schema = kwargs.get("response_schema")
        if response_schema:
            request_data["generationConfig"]["responseMimeType"] = "application/json"
            request_data["generationConfig"]["responseSchema"] = response_schema

        if system_instruction:
            request_data["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        return request_data

    async def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """Async generate text using Gemini API with aiohttp."""
        try:
            # Use base class method to prepare messages
            messages = self._prepare_messages(prompt, system_prompt)

            # Prepare Gemini-specific API parameters
            request_data = self._prepare_gemini_api_params(messages, **kwargs)

            session = await self._get_session()
            url = f"{self.base_url}/models/{self.model_name}:generateContent"

            async with session.post(
                url,
                json=request_data,
                params={"key": self.api_key},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Gemini API error {response.status}: {error_text}")

                result = await response.json()

                if "candidates" not in result or not result["candidates"]:
                    raise Exception("No response from Gemini API")

                candidate = result["candidates"][0]
                if "content" not in candidate or "parts" not in candidate["content"]:
                    raise Exception("Invalid response format from Gemini API")

                response_text = candidate["content"]["parts"][0]["text"]

                # Add assistant response to conversation
                self.add_assistant_message(response_text)

                return response_text

        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

    async def generate_stream_async(self, prompt: str, system_prompt: str = None, **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming response using Gemini API with aiohttp."""
        try:
            # Use base class method to prepare messages
            messages = self._prepare_messages(prompt, system_prompt)

            # Prepare Gemini-specific API parameters
            request_data = self._prepare_gemini_api_params(messages, **kwargs)

            session = await self._get_session()
            url = f"{self.base_url}/models/{self.model_name}:streamGenerateContent"

            async with session.post(
                url,
                json=request_data,
                params={"key": self.api_key},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Gemini API error {response.status}: {error_text}")

                full_response = ""
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line:
                        try:
                            chunk_data = json.loads(line)
                            if "candidates" in chunk_data and chunk_data["candidates"]:
                                candidate = chunk_data["candidates"][0]
                                if "content" in candidate and "parts" in candidate["content"]:
                                    for part in candidate["content"]["parts"]:
                                        if "text" in part:
                                            content = part["text"]
                                            full_response += content
                                            yield content
                        except json.JSONDecodeError:
                            continue

                # Add complete assistant response to conversation
                if full_response:
                    self.add_assistant_message(full_response)

        except Exception as e:
            raise Exception(f"Gemini Streaming API error: {str(e)}")

    # HTTP session management now inherited from base class

    def _extract_response_text(self, response) -> str:
        """Safely extract text from Gemini response, handling different finish reasons."""
        try:
            # Check if response has candidates
            if not hasattr(response, 'candidates') or not response.candidates:
                return '{"decision": "stay", "reason": "Gemini API nie zwrócił żadnych kandydatów odpowiedzi", "handoff": {"error": "No candidates in response"}}'

            candidate = response.candidates[0]

            # Check finish reason
            finish_reason = getattr(candidate, 'finish_reason', None)

            if finish_reason == 2:  # SAFETY
                return '{"decision": "stay", "reason": "Odpowiedź została zablokowana przez filtry bezpieczeństwa Gemini", "handoff": {"error": "Safety filters triggered", "finish_reason": "SAFETY"}}'
            elif finish_reason == 3:  # RECITATION
                return '{"decision": "stay", "reason": "Odpowiedź została zablokowana z powodu potencjalnego naruszenia praw autorskich", "handoff": {"error": "Recitation detected", "finish_reason": "RECITATION"}}'
            elif finish_reason == 4:  # OTHER
                return '{"decision": "stay", "reason": "Odpowiedź została zablokowana z innego powodu", "handoff": {"error": "Blocked for other reason", "finish_reason": "OTHER"}}'

            # Try to get text normally
            if hasattr(response, 'text') and response.text:
                return response.text

            # Fallback: try to extract from parts
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                if candidate.content.parts and hasattr(candidate.content.parts[0], 'text'):
                    return candidate.content.parts[0].text

            # If no text found, return a valid JSON error response
            return '{"decision": "stay", "reason": "Gemini API nie zwrócił tekstu odpowiedzi", "handoff": {"error": "No text in response", "finish_reason": str(finish_reason)}}'

        except Exception as e:
            return f'{{"decision": "stay", "reason": "Błąd przy wyciąganiu tekstu z odpowiedzi Gemini: {str(e)}", "handoff": {{"error": "Response extraction failed", "exception": "{str(e)}"}}}}'

    def generate_sync(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """Generate text using Gemini API with conversation memory."""
        try:
            # Initialize chat session if needed
            if not self.chat_session:
                self.start_conversation(system_prompt)
            elif system_prompt and not self.system_prompt_set:
                self._set_gemini_system_prompt(system_prompt)

            # Prepare common parameters
            common_params = self._prepare_common_params(**kwargs)

            # Prepare generation config
            generation_config = genai.types.GenerationConfig(
                temperature=common_params["temperature"],
                max_output_tokens=common_params["max_tokens"],
                top_p=common_params["top_p"]
            )

            # Add structured output support for sync API
            response_schema = kwargs.get("response_schema")
            if response_schema:
                generation_config.response_mime_type = "application/json"
                generation_config.response_schema = response_schema

            # Send only the current prompt (model remembers context)
            response = self.chat_session.send_message(prompt, generation_config=generation_config)

            # Handle different finish reasons
            response_text = self._extract_response_text(response)

            # Store in our history for debugging
            self.conversation_history.append(("user", prompt))
            self.conversation_history.append(("assistant", response_text))

            # Also update base class conversation for consistency
            self.add_user_message(prompt)
            self.add_assistant_message(response_text)

            return response_text

        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

    def generate_stream(self, prompt: str, system_prompt: str = None, **kwargs):
        """Generate streaming text using Gemini API."""
        try:
            # Initialize chat session if needed
            if not self.chat_session:
                self.start_conversation(system_prompt)
            elif system_prompt and not self.system_prompt_set:
                self._set_gemini_system_prompt(system_prompt)

            # Prepare common parameters
            common_params = self._prepare_common_params(**kwargs)

            # Send streaming request
            response = self.chat_session.send_message(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=common_params["temperature"],
                    max_output_tokens=common_params["max_tokens"],
                    top_p=common_params["top_p"]
                ),
                stream=True
            )

            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    yield chunk.text

            # Store in our history for debugging
            self.conversation_history.append(("user", prompt))
            self.conversation_history.append(("assistant", full_response))

            # Also update base class conversation for consistency
            self.add_user_message(prompt)
            self.add_assistant_message(full_response)

        except Exception as e:
            raise Exception(f"Gemini Streaming API error: {str(e)}")

    def reset_conversation(self) -> None:
        """Reset conversation memory."""
        # Reset base class conversation
        super().reset_conversation()

        # Reset Gemini-specific state
        self.chat_session = None
        self.conversation_history = []

    # Other conversation management methods now inherited from base class

    def is_available(self) -> bool:
        """Check if Gemini API is available."""
        if not GEMINI_AVAILABLE:
            return False

        try:
            # Test with a minimal request
            test_response = self.model.generate_content("Hi")
            return bool(test_response.text)
        except:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        return {
            "provider": "google",
            "model": self.model_name,
            "type": "cloud",
            "supports_streaming": True,
            "supports_functions": True,
            "context_length": 32768  # Gemini Pro context length
        }