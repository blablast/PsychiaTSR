import os
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from .base import LLMProvider
import openai


class OpenAIProvider(LLMProvider):
    """OpenAI provider using shared base functionality"""

    def __init__(self, model_name: str = "gpt-3.5-turbo", **kwargs):
        super().__init__(model_name, **kwargs)

        self.api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        self.client = openai.OpenAI(api_key=self.api_key)

        # Provider-specific configuration
        self.base_url = "https://api.openai.com/v1"

        # Structured output configuration (set once per session)
        self._default_response_format = None

    def set_default_response_format(self, response_format: dict) -> None:
        """Set default response format for all subsequent requests."""
        self._default_response_format = response_format

    def clear_default_response_format(self) -> None:
        """Clear default response format."""
        self._default_response_format = None
    
    # Conversation methods now inherited from base class

    def _prepare_openai_api_params(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Prepare OpenAI-specific API parameters."""
        api_params = {
            "model": self.model_name,
            "messages": messages,
        }

        common_params = self._prepare_common_params(**kwargs)
        # Model-specific parameter handling
        if "gpt-5" in self.model_name:
            # gpt-5 specific parameters
            api_params.update({
                "max_completion_tokens": common_params["max_tokens"],
                "temperature": 1,
            })
        else:
            # Standard GPT models
            api_params.update({
                "max_tokens": common_params["max_tokens"],
                "temperature": common_params["temperature"],
                "top_p": common_params["top_p"]
            })

        # Add structured output support (from per-request or default)
        response_format = kwargs.get("response_format") or self._default_response_format
        if response_format:
            api_params["response_format"] = response_format

        return api_params

    def generate_sync(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate response using OpenAI API with conversation memory."""
        try:
            # Use base class method to prepare messages
            messages = self._prepare_messages(prompt, system_prompt)

            # Prepare OpenAI-specific API parameters
            api_params = self._prepare_openai_api_params(messages, **kwargs)

            response = self.client.chat.completions.create(**api_params)
            response_text = response.choices[0].message.content.strip()

            # Add assistant response to conversation history
            self.add_assistant_message(response_text)

            return response_text

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    async def _get_openai_session(self):
        """Get aiohttp session with OpenAI headers."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        return await self._get_session(headers)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate response using OpenAI API with aiohttp."""
        try:
            # Use base class method to prepare messages
            messages = self._prepare_messages(prompt, system_prompt)

            # Prepare OpenAI-specific API parameters with streaming disabled
            api_params = self._prepare_openai_api_params(messages, **kwargs)

            session = await self._get_openai_session()
            async with session.post(f"{self.base_url}/chat/completions", json=api_params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")

                result = await response.json()
                response_text = result["choices"][0]["message"]["content"].strip()

                # Add assistant response to conversation history
                self.add_assistant_message(response_text)

                return response_text

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    async def generate_stream_async(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming response using OpenAI API with aiohttp."""
        try:
            # Use base class method to prepare messages
            messages = self._prepare_messages(prompt, system_prompt)

            # Prepare OpenAI-specific API parameters with streaming enabled
            api_params = self._prepare_openai_api_params(messages, **kwargs)
            api_params["stream"] = True

            session = await self._get_openai_session()
            async with session.post(f"{self.base_url}/chat/completions", json=api_params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")

                full_response = ""
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        line = line[6:]  # Remove 'data: ' prefix

                        if line == '[DONE]':
                            break

                        if line:
                            try:
                                chunk_data = json.loads(line)
                                if chunk_data.get('choices') and chunk_data['choices'][0].get('delta'):
                                    content = chunk_data['choices'][0]['delta'].get('content')
                                    if content:
                                        full_response += content
                                        yield content
                            except json.JSONDecodeError:
                                continue

                # Add complete assistant response to conversation history
                if full_response:
                    self.add_assistant_message(full_response)

        except Exception as e:
            raise Exception(f"OpenAI Streaming API error: {str(e)}")

    # HTTP session management now inherited from base class

    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None, **kwargs):
        """Generate streaming response using OpenAI API."""
        try:
            # Use base class method to prepare messages
            messages = self._prepare_messages(prompt, system_prompt)

            # Prepare OpenAI-specific API parameters with streaming enabled
            api_params = self._prepare_openai_api_params(messages, **kwargs)
            api_params["stream"] = True

            stream = self.client.chat.completions.create(**api_params)

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content

            # Add complete assistant response to conversation history
            self.add_assistant_message(full_response)

        except Exception as e:
            raise Exception(f"OpenAI Streaming API error: {str(e)}")

    # Conversation management methods now inherited from base class

    def is_available(self) -> bool:
        """Check if OpenAI API is available"""
        return bool(self.api_key)