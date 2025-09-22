import os
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from .base import LLMProvider

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIProvider(LLMProvider):
    """OpenAI provider using shared base functionality"""

    def __init__(self, model_name: str = "gpt-3.5-turbo", **kwargs):
        super().__init__(model_name, **kwargs)

        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")

        self.api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        # Keep sync client for backward compatibility
        self.client = openai.OpenAI(api_key=self.api_key)

        # Provider-specific configuration
        self.base_url = "https://api.openai.com/v1"
    
    # Conversation methods now inherited from base class

    def _prepare_openai_api_params(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Prepare OpenAI-specific API parameters."""
        api_params = {
            "model": self.model_name,
            "messages": messages,
        }

        # Model-specific parameter handling
        if "gpt-5" in self.model_name:
            # gpt-5-nano specific parameters
            api_params["max_completion_tokens"] = kwargs.get("max_tokens", 150)
            api_params["temperature"] = 1.0  # Only supported value
        else:
            # Standard GPT models
            common_params = self._prepare_common_params(**kwargs)
            api_params.update({
                "max_tokens": common_params["max_tokens"],
                "temperature": common_params["temperature"],
                "top_p": common_params["top_p"]
            })

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
        return bool(self.api_key and OPENAI_AVAILABLE)