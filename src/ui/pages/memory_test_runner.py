"""Memory test runner - extracted from long run_memory_test method."""

from datetime import datetime
from typing import Dict, Any, Tuple
import streamlit as st

from config import Config
from ...llm import OpenAIProvider, GeminiProvider


class MemoryTestRunner:
    """Handles memory testing with step-by-step execution."""

    def __init__(
        self,
        provider: str,
        model: str,
        system_prompt: str,
        stage_prompt: str,
        temperature: float,
        max_tokens: int,
    ):
        """Initialize test runner."""
        self.provider = provider
        self.model = model
        self.system_prompt = system_prompt
        self.stage_prompt = stage_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.llm_provider = None
        self.test_results = None

    def run_test(self) -> Dict[str, Any]:
        """Execute complete memory test."""
        try:
            # Initialize components
            self._initialize_provider()
            self._initialize_test_results()
            self._initialize_ui_elements()

            # Execute test steps
            self._execute_step_1_system_prompt()
            self._execute_step_2_stage_prompt()
            self._execute_step_3_initial_query()
            self._execute_step_4_followup_query()
            self._execute_step_5_memory_check()

            # Finalize results
            self._finalize_test_results()

            return self.test_results

        except Exception as e:
            return self._create_error_result(str(e))

    def _initialize_provider(self) -> None:
        """Initialize LLM provider."""
        from config import Config

        config = Config.get_instance()
        if self.provider == "OpenAI":
            self.llm_provider = OpenAIProvider(self.model, api_key=config.OPENAI_API_KEY)
        else:
            self.llm_provider = GeminiProvider(self.model, api_key=config.GOOGLE_API_KEY)

    def _initialize_test_results(self) -> None:
        """Initialize test results structure."""
        self.test_results = {
            "provider": self.provider,
            "model": self.model,
            "timestamp": datetime.now().isoformat(),
            "start_time": datetime.now(),
            "supports_memory": self._check_memory_support(),
            "steps": [],
        }

    def _check_memory_support(self) -> bool:
        """Check if provider supports conversation memory."""
        return hasattr(self.llm_provider, "conversation_messages") or hasattr(
            self.llm_provider, "chat_session"
        )

    def _initialize_ui_elements(self) -> None:
        """Initialize UI progress elements."""
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        self.status_text.text("🚀 Rozpoczynam test pamięci modelu...")

    def _execute_step_1_system_prompt(self) -> None:
        """Step 1: Set system prompt."""
        self.status_text.text("🔧 Krok 1/5: Ustawianie system prompt...")
        self.progress_bar.progress(0.2)

        if hasattr(self.llm_provider, "set_system_prompt"):
            self.llm_provider.set_system_prompt(self.system_prompt)
            result = {
                "step": 1,
                "action": "set_system_prompt",
                "success": True,
                "method": "set_system_prompt",
            }
        else:
            result = {
                "step": 1,
                "action": "set_system_prompt",
                "success": False,
                "method": "not_supported",
            }

        self.test_results["steps"].append(result)

    def _execute_step_2_stage_prompt(self) -> None:
        """Step 2: Set stage prompt."""
        self.status_text.text("🎯 Krok 2/5: Ustawianie stage prompt...")
        self.progress_bar.progress(0.4)

        if self.test_results["supports_memory"]:
            if hasattr(self.llm_provider, "add_user_message") and hasattr(
                self.llm_provider, "add_assistant_message"
            ):
                self.llm_provider.add_user_message(
                    f"NOWY ETAP TERAPII:\n{self.stage_prompt}\n\nOd teraz pracuj zgodnie z tym etapem."
                )
                self.llm_provider.add_assistant_message(
                    "Rozumiem. Pracuję zgodnie z wytycznymi tego etapu."
                )
                result = {
                    "step": 2,
                    "action": "set_stage_prompt",
                    "success": True,
                    "method": "conversation_memory",
                }
            else:
                result = {
                    "step": 2,
                    "action": "set_stage_prompt",
                    "success": False,
                    "method": "no_conversation_methods",
                }
        else:
            result = {
                "step": 2,
                "action": "set_stage_prompt",
                "success": False,
                "method": "no_memory_support",
            }

        self.test_results["steps"].append(result)

    def _execute_step_3_initial_query(self) -> None:
        """Step 3: Send initial query."""
        self.status_text.text("💬 Krok 3/5: Wysyłanie pierwszego zapytania...")
        self.progress_bar.progress(0.6)

        query = "Cześć! Mam problem ze stresem w pracy. Czy możesz mi pomóc?"

        try:
            # Build request for memory-capable providers
            if self.test_results["supports_memory"]:
                response = self._send_memory_query(query)
                method = "conversation_memory"
            else:
                response = self._send_stateless_query(query)
                method = "stateless"

            result = {
                "step": 3,
                "action": "initial_query",
                "success": True,
                "method": method,
                "query": query,
                "response": response,
                "response_length": len(response),
            }

        except Exception as e:
            result = {
                "step": 3,
                "action": "initial_query",
                "success": False,
                "error": str(e),
                "query": query,
            }

        self.test_results["steps"].append(result)

    def _execute_step_4_followup_query(self) -> None:
        """Step 4: Send follow-up query."""
        self.status_text.text("🔄 Krok 4/5: Wysyłanie pytania kontrolnego...")
        self.progress_bar.progress(0.8)

        query = "Jakie techniki relaksu mi wcześniej polecałeś?"

        try:
            if self.test_results["supports_memory"]:
                response = self._send_memory_query(query)
                method = "conversation_memory"
            else:
                response = self._send_stateless_query(query)
                method = "stateless"

            result = {
                "step": 4,
                "action": "followup_query",
                "success": True,
                "method": method,
                "query": query,
                "response": response,
                "response_length": len(response),
            }

        except Exception as e:
            result = {
                "step": 4,
                "action": "followup_query",
                "success": False,
                "error": str(e),
                "query": query,
            }

        self.test_results["steps"].append(result)

    def _execute_step_5_memory_check(self) -> None:
        """Step 5: Check conversation memory."""
        self.status_text.text("🧠 Krok 5/5: Sprawdzanie pamięci konwersacji...")
        self.progress_bar.progress(1.0)

        memory_info = {}

        if hasattr(self.llm_provider, "conversation_messages"):
            memory_info["conversation_messages"] = len(self.llm_provider.conversation_messages)
            memory_info["memory_type"] = "conversation_messages"

        elif hasattr(self.llm_provider, "chat_session"):
            try:
                history = self.llm_provider.chat_session.history
                memory_info["history_entries"] = len(history)
                memory_info["memory_type"] = "chat_session"
            except Exception:
                memory_info["history_entries"] = 0
                memory_info["memory_type"] = "chat_session_error"

        else:
            memory_info["memory_type"] = "none"

        result = {"step": 5, "action": "memory_check", "success": True, "memory_info": memory_info}

        self.test_results["steps"].append(result)

    def _send_memory_query(self, query: str) -> str:
        """Send query using memory-capable provider."""
        if hasattr(self.llm_provider, "add_user_message"):
            self.llm_provider.add_user_message(query)

        if hasattr(self.llm_provider, "generate_response"):
            return self.llm_provider.generate_response(
                query, temperature=self.temperature, max_tokens=self.max_tokens
            )
        elif hasattr(self.llm_provider, "get_response"):
            return self.llm_provider.get_response(
                query, temperature=self.temperature, max_tokens=self.max_tokens
            )
        else:
            raise ValueError("Provider doesn't have response generation method")

    def _send_stateless_query(self, query: str) -> str:
        """Send query using stateless provider."""
        # Build full prompt with context
        full_prompt = f"{self.system_prompt}\n\nEtap terapii:\n{self.stage_prompt}\n\nUżytkownik: {query}\nTerapeuta:"

        if hasattr(self.llm_provider, "generate_response"):
            return self.llm_provider.generate_response(
                full_prompt, temperature=self.temperature, max_tokens=self.max_tokens
            )
        elif hasattr(self.llm_provider, "get_response"):
            return self.llm_provider.get_response(
                full_prompt, temperature=self.temperature, max_tokens=self.max_tokens
            )
        else:
            raise ValueError("Provider doesn't have response generation method")

    def _finalize_test_results(self) -> None:
        """Finalize test results."""
        self.test_results["end_time"] = datetime.now()
        self.test_results["duration_seconds"] = (
            self.test_results["end_time"] - self.test_results["start_time"]
        ).total_seconds()

        # Calculate success rate
        successful_steps = sum(
            1 for step in self.test_results["steps"] if step.get("success", False)
        )
        self.test_results["success_rate"] = successful_steps / len(self.test_results["steps"])

        self.status_text.text("✅ Test zakończony pomyślnie!")

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result."""
        return {
            "provider": self.provider,
            "model": self.model,
            "timestamp": datetime.now().isoformat(),
            "error": error_message,
            "success": False,
        }
