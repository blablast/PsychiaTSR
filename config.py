import json
import os
from pathlib import Path


class Config:
    """Configuration management for the SFBT application"""

    # Load config from JSON file
    BASE_DIR = Path(__file__).parent
    CONFIG_FILE = BASE_DIR / "config" / "app_config.json"

    # Load configuration
    _config_data = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            _config_data = json.load(f)

    # API Keys from environment (.env)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

    # Agent configurations from new structure
    _agents_config = _config_data.get("agents", {})

    # Therapist configuration
    _therapist_config = _agents_config.get("therapist", {})
    DEFAULT_THERAPIST_PROVIDER = _therapist_config.get("provider", "openai")
    DEFAULT_THERAPIST_MODEL = _therapist_config.get("model", "gpt-4o-mini")

    # Supervisor configuration
    _supervisor_config = _agents_config.get("supervisor", {})
    DEFAULT_SUPERVISOR_PROVIDER = _supervisor_config.get("provider", "gemini")
    DEFAULT_SUPERVISOR_MODEL = _supervisor_config.get("model", "gemini-1.5-flash")

    # Global parameters
    DEFAULT_TEMPERATURE = _config_data.get("parameters", {}).get("temperature", 0.7)
    DEFAULT_MAX_TOKENS = _config_data.get("parameters", {}).get("max_tokens", 150)
    DEFAULT_TOP_P = _config_data.get("parameters", {}).get("top_p", 0.9)

    # App Configuration from config.json
    APP_TITLE = _config_data.get("app", {}).get("title", "Psychia - TSR Therapy Assistant")
    APP_ICON = _config_data.get("app", {}).get("icon", "🧠")

    # Directory Configuration from config.json
    LOGS_DIR = _config_data.get("directories", {}).get("logs_dir", "./logs")
    PROMPT_DIR = _config_data.get("directories", {}).get("prompt_dir", "./config/json/prompts")
    STAGES_DIR = _config_data.get("directories", {}).get("stages_dir", "./config")

    # Memory and Context Configuration
    _memory_config = _config_data.get("memory", {})
    MAX_THERAPIST_CONTEXT_MESSAGES = _memory_config.get("max_therapist_messages", 20)
    MAX_SUPERVISOR_CONTEXT_MESSAGES = _memory_config.get("max_supervisor_messages", 15)
    ENABLE_CONVERSATION_SUMMARY = _memory_config.get("enable_summary", True)
    CONTEXT_COMPRESSION_THRESHOLD = _memory_config.get("compression_threshold", 100)

    
    @classmethod
    def get_llm_config(cls, provider: str, agent_type: str = None) -> dict:
        """Get LLM configuration for specified provider and optionally specific agent"""
        base_config = {}

        if provider.lower() == "openai":
            base_config["api_key"] = cls.OPENAI_API_KEY
        elif provider.lower() == "gemini":
            base_config["api_key"] = cls.GOOGLE_API_KEY
        else:
            raise ValueError(f"Unknown provider: {provider}")

        # Add agent-specific parameters if agent_type provided
        if agent_type:
            agent_params = cls.get_agent_parameters(agent_type)
            base_config.update(agent_params)
        else:
            # Fallback to global parameters
            base_config.update({
                "temperature": cls.DEFAULT_TEMPERATURE,
                "max_tokens": cls.DEFAULT_MAX_TOKENS,
                "top_p": cls.DEFAULT_TOP_P
            })

        return base_config

    @classmethod
    def get_agent_parameters(cls, agent_type: str) -> dict:
        """Get parameters for specified agent (therapist/supervisor)"""
        agent_config = cls._agents_config.get(agent_type, {})
        agent_params = agent_config.get("parameters", {})

        # Return agent-specific parameters with fallbacks
        return {
            "temperature": agent_params.get("temperature", cls.DEFAULT_TEMPERATURE),
            "max_tokens": agent_params.get("max_tokens", cls.DEFAULT_MAX_TOKENS),
            "top_p": agent_params.get("top_p", cls.DEFAULT_TOP_P)
        }

    @classmethod
    def get_agent_config(cls, agent_type: str) -> dict:
        """Get complete configuration for specified agent"""
        agent_config = cls._agents_config.get(agent_type, {})

        return {
            "provider": agent_config.get("provider", "openai"),
            "model": agent_config.get("model", "gpt-4o-mini"),
            "parameters": cls.get_agent_parameters(agent_type)
        }

    @classmethod
    def get_agent_defaults(cls) -> dict:
        """Get default provider and model configuration for each agent"""
        return {
            "therapist": {
                "provider": cls.DEFAULT_THERAPIST_PROVIDER,
                "model": cls.DEFAULT_THERAPIST_MODEL
            },
            "supervisor": {
                "provider": cls.DEFAULT_SUPERVISOR_PROVIDER,
                "model": cls.DEFAULT_SUPERVISOR_MODEL
            }
        }

    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        for directory in [cls.LOGS_DIR, cls.PROMPT_DIR, cls.STAGES_DIR]:
            Path(directory).mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate_config(cls) -> dict:
        """Validate configuration and return status"""
        status = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check API keys
        if not cls.OPENAI_API_KEY and not cls.GOOGLE_API_KEY:
            status["errors"].append("No API keys configured")
            status["valid"] = False
        
        # Check directories
        try:
            cls.ensure_directories()
        except Exception as e:
            status["errors"].append(f"Failed to create directories: {str(e)}")
            status["valid"] = False
        
        # Check model names
        if not cls.DEFAULT_THERAPIST_MODEL:
            status["warnings"].append("DEFAULT_THERAPIST_MODEL not set")
        
        if not cls.DEFAULT_SUPERVISOR_MODEL:
            status["warnings"].append("DEFAULT_SUPERVISOR_MODEL not set")
        
        # Check optional API keys
        if not cls.OPENAI_API_KEY:
            status["warnings"].append("OpenAI API key not configured (optional)")
        
        return status
    
    @classmethod
    def to_dict(cls) -> dict:
        """Convert configuration to dictionary"""
        return {
            "providers": {
                "therapist": {
                    "provider": cls.DEFAULT_THERAPIST_PROVIDER,
                    "model": cls.DEFAULT_THERAPIST_MODEL
                },
                "supervisor": {
                    "provider": cls.DEFAULT_SUPERVISOR_PROVIDER,
                    "model": cls.DEFAULT_SUPERVISOR_MODEL
                }
            },
            "directories": {
                "logs_dir": cls.LOGS_DIR,
                "prompt_dir": cls.PROMPT_DIR,
                "stages_dir": cls.STAGES_DIR
            },
            "model_params": {
                "temperature": cls.DEFAULT_TEMPERATURE,
                "max_tokens": cls.DEFAULT_MAX_TOKENS,
                "top_p": cls.DEFAULT_TOP_P
            },
            "ui": {
                "app_title": cls.APP_TITLE,
                "app_icon": cls.APP_ICON
            }
        }