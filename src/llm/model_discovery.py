"""Dynamic model discovery with intelligent caching."""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use system environment

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider


class ModelDiscovery:
    """Dynamic model discovery with intelligent JSON caching."""

    CACHE_FILE = Path("config/models_cache.json")
    DEFAULT_CACHE_DURATION_DAYS = 7


    @classmethod
    def load_cache(cls) -> Dict[str, Any]:
        """Load models cache from JSON file."""
        try:
            if cls.CACHE_FILE.exists():
                with open(cls.CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass

        # Return empty cache structure if file doesn't exist or is corrupted
        return cls._get_empty_cache()

    @classmethod
    def save_cache(cls, cache_data: Dict[str, Any]) -> None:
        """Save models cache to JSON file."""
        try:
            cls.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(cls.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save models cache: {e}")

    @classmethod
    def _get_empty_cache(cls) -> Dict[str, Any]:
        """Get empty cache structure from template file."""
        try:
            template_path = Path("config/templates/defaults/models_cache_default.json")
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    cache_template = json.load(f)
                    # Override cache duration from class constant
                    cache_template["cache_duration_days"] = cls.DEFAULT_CACHE_DURATION_DAYS
                    return cache_template
        except Exception:
            pass

        # Fallback to hardcoded structure
        return {
            "cache_version": "1.0",
            "last_updated": None,
            "expires_at": None,
            "cache_duration_days": cls.DEFAULT_CACHE_DURATION_DAYS,
            "providers": {
                "openai": {"models": [], "last_fetched": None, "status": "not_fetched", "error": None},
                "gemini": {"models": [], "last_fetched": None, "status": "not_fetched", "error": None}
            },
            "fallback_models": {
                "openai": [],
                "gemini": []
            }
        }

    @classmethod
    def is_cache_expired(cls, cache_data: Dict[str, Any]) -> bool:
        """Check if cache is expired."""
        if not cache_data.get("expires_at"):
            return True

        try:
            expires_at = datetime.fromisoformat(cache_data["expires_at"].replace('Z', '+00:00'))
            return datetime.now().astimezone() > expires_at
        except Exception:
            return True

    @classmethod
    def _has_api_key(cls, provider: str) -> bool:
        """Check if API key is available for provider."""
        if provider == "openai":
            return bool(os.getenv('OPENAI_API_KEY'))
        elif provider == "gemini":
            return bool(os.getenv('GOOGLE_API_KEY'))
        return False

    @classmethod
    async def _fetch_openai_models(cls) -> List[Dict[str, Any]]:
        """Fetch available models from OpenAI API."""
        try:
            headers = {
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.openai.com/v1/models", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = []

                        for model in data.get("data", []):
                            model_id = model.get("id", "")

                            # Filter for chat completion models
                            if any(prefix in model_id for prefix in ["gpt-", "o1-"]):
                                models.append({
                                    "id": model_id,
                                    "name": model_id.upper().replace("-", " ").title(),
                                    "provider": "openai",
                                    "context_length": cls._get_openai_context_length(model_id),
                                    "description": f"OpenAI {model_id} model",
                                    "available": True
                                })

                        return models
        except Exception as e:
            print(f"Error fetching OpenAI models: {e}")

        return []

    @classmethod
    def _get_openai_context_length(cls, model_id: str) -> int:
        """Get context length for OpenAI model."""
        context_map = {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 16385,
            "o1-preview": 128000,
            "o1-mini": 128000
        }

        for pattern, length in context_map.items():
            if pattern in model_id:
                return length

        return 4096  # Default

    @classmethod
    async def _fetch_gemini_models(cls) -> List[Dict[str, Any]]:
        """Fetch available models from Gemini API."""
        try:
            api_key = os.getenv('GOOGLE_API_KEY')
            url = "https://generativelanguage.googleapis.com/v1beta/models"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params={"key": api_key}) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = []

                        for model in data.get("models", []):
                            model_name = model.get("name", "")
                            if "models/" in model_name:
                                model_id = model_name.split("models/")[-1]

                                # Filter for text generation models
                                if "gemini" in model_id and "generateContent" in model.get("supportedGenerationMethods", []):
                                    models.append({
                                        "id": model_id,
                                        "name": model.get("displayName", model_id.title()),
                                        "provider": "gemini",
                                        "context_length": cls._get_gemini_context_length(model_id),
                                        "description": model.get("description", f"Google {model_id} model"),
                                        "available": True
                                    })

                        return models
        except Exception as e:
            print(f"Error fetching Gemini models: {e}")

        return []

    @classmethod
    def _get_gemini_context_length(cls, model_id: str) -> int:
        """Get context length for Gemini model."""
        context_map = {
            "gemini-2.0": 2000000,
            "gemini-1.5-pro": 2000000,
            "gemini-1.5-flash": 1000000,
            "gemini-pro": 32768
        }

        for pattern, length in context_map.items():
            if pattern in model_id:
                return length

        return 32768  # Default

    @classmethod
    async def _fetch_all_models(cls) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch models from all providers concurrently."""
        tasks = {
            "openai": cls._fetch_openai_models(),
            "gemini": cls._fetch_gemini_models(),
        }

        results = {}
        for provider, task in tasks.items():
            try:
                results[provider] = await task
            except Exception as e:
                print(f"Error fetching {provider} models: {e}")
                results[provider] = []

        return results

    @classmethod
    async def refresh_models_cache(cls) -> Dict[str, Any]:
        """Refresh models cache by fetching from APIs."""
        cache_data = cls.load_cache()
        current_time = datetime.now().isoformat() + "Z"

        try:
            # Fetch models from all providers
            fetched_models = await cls._fetch_all_models()

            # Update cache with fetched models
            for provider, models in fetched_models.items():
                if provider in cache_data["providers"]:
                    cache_data["providers"][provider].update({
                        "models": models,
                        "last_fetched": current_time,
                        "status": "success" if models else "empty",
                        "error": None
                    })

            # Update cache metadata
            cache_duration = cache_data.get("cache_duration_days", cls.DEFAULT_CACHE_DURATION_DAYS)
            expires_at = datetime.now() + timedelta(days=cache_duration)

            cache_data.update({
                "last_updated": current_time,
                "expires_at": expires_at.isoformat() + "Z"
            })

            # Save updated cache
            cls.save_cache(cache_data)

        except Exception as e:
            print(f"Error refreshing models cache: {e}")

        return cache_data

    @classmethod
    def get_models_from_cache(cls, use_fallback: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """Get models from cache, with optional fallback to static list."""
        cache_data = cls.load_cache()
        models = {}

        for provider in ["openai", "gemini"]:
            provider_data = cache_data.get("providers", {}).get(provider, {})
            cached_models = provider_data.get("models", [])

            if cached_models:
                # Add availability status based on API key
                for model in cached_models:
                    model["available"] = cls._has_api_key(provider) if provider in ["openai", "gemini"] else True

                models[provider] = cached_models
            elif use_fallback and provider in cache_data.get("fallback_models", {}):
                # Use fallback models if cache is empty
                fallback_models = cache_data["fallback_models"][provider]
                for model in fallback_models:
                    model["available"] = cls._has_api_key(provider)

                models[provider] = fallback_models
            else:
                models[provider] = []

        return models

    @classmethod
    async def discover_models(cls, force_refresh: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """Main method to discover models using cache-first strategy."""
        cache_data = cls.load_cache()

        # Check if we need to refresh
        should_refresh = force_refresh or cls.is_cache_expired(cache_data)

        if should_refresh:
            try:
                cache_data = await cls.refresh_models_cache()
            except Exception as e:
                print(f"Failed to refresh models cache: {e}")

        return cls.get_models_from_cache()

    @staticmethod
    def get_openai_models() -> List[Dict[str, Any]]:
        """Get available OpenAI models."""
        cache_models = ModelDiscovery.get_models_from_cache()
        return cache_models.get("openai", [])

    @staticmethod
    def get_gemini_models() -> List[Dict[str, Any]]:
        """Get available Gemini models."""
        cache_models = ModelDiscovery.get_models_from_cache()
        return cache_models.get("gemini", [])

    @staticmethod
    def get_available_models() -> List[Dict[str, Any]]:
        """Get all available models as a flat list."""
        all_models = []
        providers = ModelDiscovery.get_models_from_cache()

        for provider_name, models in providers.items():
            for model in models:
                # Add consistent fields for UI
                model_info = {
                    'model_id': model['id'],
                    'name': model['name'],
                    'provider': provider_name,
                    'available': model.get('available', False)
                }
                all_models.append(model_info)

        return all_models

    @staticmethod
    def get_all_available_models() -> Dict[str, List[Dict[str, Any]]]:
        """Get all available models grouped by provider."""
        return ModelDiscovery.get_models_from_cache()

    @classmethod
    def test_model_availability(cls, provider: str, model_id: str) -> bool:
        """Test if a specific model is available and working."""
        try:
            if provider == 'openai':
                llm = OpenAIProvider(model_id, api_key=os.getenv('OPENAI_API_KEY'))
                return llm.is_available()
            elif provider == 'gemini':
                llm = GeminiProvider(model_id, api_key=os.getenv('GOOGLE_API_KEY'))
                return llm.is_available()
            else:
                return False
        except Exception:
            return False

    @classmethod
    def get_recommended_models(cls) -> Dict[str, Optional[str]]:
        """Get recommended models for different roles."""
        available_models = cls.get_models_from_cache()

        recommendations: Dict[str, Optional[str]] = {
            'therapist': None,
            'supervisor': None
        }

        # Priority order for recommendations
        priority_models = [
            ('openai', 'gpt-4o-mini'),
            ('openai', 'gpt-4o'),
            ('gemini', 'gemini-2.5-flash'),
            ('gemini', 'gemini-2.5-pro'),
        ]

        for provider, model_id in priority_models:
            provider_models = available_models.get(provider, [])
            matching_model = next((m for m in provider_models if m['id'] == model_id and m.get('available')), None)

            if matching_model:
                if not recommendations['therapist']:
                    recommendations['therapist'] = f"{provider}:{model_id}"
                if not recommendations['supervisor']:
                    recommendations['supervisor'] = f"{provider}:{model_id}"

                # Both roles filled
                if recommendations['therapist'] and recommendations['supervisor']:
                    break

        return recommendations