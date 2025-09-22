"""
Main workflow manager coordinating supervisor evaluation and therapist response.

Follows Single Responsibility Principle by delegating specific tasks to
specialized classes while orchestrating the overall workflow.
"""

from ..agents.interfaces.agent_provider_interface import IAgentProvider
from ..prompts.unified_prompt_manager import UnifiedPromptManager
from ..session.session_manager import SessionManager
from .supervisor_evaluator import SupervisorEvaluator
from .therapist_responder import TherapistResponder
from .workflow_result import WorkflowResult


class TherapyWorkflowManager:
    """
    Main workflow manager coordinating supervisor evaluation and therapist response.

    Follows Single Responsibility Principle by delegating specific tasks to
    specialized classes while orchestrating the overall workflow.
    """

    def __init__(self,
                 agent_provider: IAgentProvider,
                 prompt_manager: UnifiedPromptManager,
                 session_manager: SessionManager,
                 logger):
        self._agent_provider = agent_provider
        self._prompt_manager = prompt_manager
        self._session_manager = session_manager
        self._logger = logger

        # Initialize specialized handlers
        self._supervisor_evaluator = SupervisorEvaluator(
            agent_provider, prompt_manager, logger
        )
        self._therapist_responder = TherapistResponder(
            agent_provider, prompt_manager, logger
        )


    def process_user_message(self, user_message: str) -> WorkflowResult:
        """
        Process user message through complete therapy workflow.

        Args:
            user_message: User's message to process

        Returns:
            WorkflowResult containing complete workflow results
        """
        if not self._agent_provider.is_initialized():
            return WorkflowResult(
                success=False,
                message="Therapy agents not initialized",
                error="AGENTS_NOT_INITIALIZED"
            )

        try:
            original_user_message = user_message
            message_for_llm = user_message

            current_stage = self._session_manager.get_current_stage()
            # Get conversation history without stage transition messages for supervisor evaluation
            conversation_history = self._session_manager.get_conversation_history(exclude_stage_transitions=True)

            # Step 1: Supervisor evaluation (using translated message for LLM)
            self._logger.log_info("🔍 Rozpoczynam konsultację z supervisorem...")

            supervisor_result = self._supervisor_evaluator.evaluate_stage(
                current_stage, message_for_llm, conversation_history
            )

            if not supervisor_result.success:
                return supervisor_result

            supervisor_decision = supervisor_result.data["decision"]

            # Log supervisor decision immediately after receiving it
            self._logger.log_info(
                f"🔍 Supervisor decision: [{supervisor_decision.decision}] {supervisor_decision.reason}"
            )

            # CRITICAL: Check for safety risk - if detected, activate crisis protocol
            if supervisor_decision.safety_risk:
                self._logger.log_error("🚨 KRYZYS: Wykryto zagrożenie bezpieczeństwa!")
                return self._handle_crisis_situation(user_message, supervisor_decision)

            # Step 2: Handle stage progression if needed
            if supervisor_decision.decision == "advance":
                old_stage = current_stage
                progression_result = self._session_manager.advance_to_next_stage()
                if not progression_result.success:
                    self._logger.log_error(f"Stage progression failed: {progression_result.error}")
                else:
                    new_stage = self._session_manager.get_current_stage()
                    # Log stage change with clear visual separation
                    self._logger.log_info("=" * 60)
                    self._logger.log_info(f"🎯 ZMIANA ETAPU TERAPII: '{old_stage}' → '{new_stage}'")
                    self._logger.log_info("Nowe prompty systemowe zostaną ustawione dla agentów")
                    self._logger.log_info("=" * 60)
                current_stage = self._session_manager.get_current_stage()

            # Step 3: Generate therapist response (using translated message for LLM)
            self._logger.log_info("💬 Generuję odpowiedź terapeuty...")
            # self._logger.log_info(f"💬 Wiadomość dla terapeuty: '{message_for_llm}'")
            # Terapeuta też nie potrzebuje stage transition messages
            therapist_result = self._therapist_responder.generate_response(
                current_stage, message_for_llm, conversation_history
            )

            if not therapist_result.success:
                return therapist_result

            therapist_response = therapist_result.data["response"]

            # Add stage transition message if stage changed (before therapist response)
            if supervisor_decision.decision == "advance":
                self._add_stage_transition_message(current_stage)

            # Step 4: Update conversation history
            # Check if user message is already in session (added by chat interface)
            messages = self._session_manager.get_conversation_history()
            if not messages or messages[-1].text != original_user_message:
                self._session_manager.add_user_message(original_user_message)

            self._session_manager.add_assistant_message(
                therapist_response,
                therapist_result.data["prompt_used"]["id"]
            )

            return WorkflowResult(
                success=True,
                message="User message processed successfully",
                data={
                    "supervisor_decision": supervisor_decision,
                    "therapist_response": therapist_response,
                    "stage_changed": supervisor_decision.decision == "advance",
                    "current_stage": current_stage
                }
            )

        except Exception as e:
            self._logger.log_error(f"Workflow processing failed: {str(e)}")
            return WorkflowResult(
                success=False,
                message="Workflow processing failed",
                error=str(e)
            )

    def _handle_crisis_situation(self, user_message: str, supervisor_decision) -> WorkflowResult:
        """
        Handle crisis situation when safety_risk is detected.

        Args:
            user_message: User's message that triggered crisis
            supervisor_decision: Supervisor decision with safety_risk=True

        Returns:
            WorkflowResult with crisis response
        """
        # Log crisis
        self._logger.log_error("🚨 PROTOKÓŁ KRYZYSOWY AKTYWOWANY")

        # Set crisis flag in session
        import streamlit as st
        st.session_state.show_crisis_message = True

        # Generate crisis response instead of normal therapy
        crisis_response = (
            "**⚠️ NATYCHMIASTOWA POMOC POTRZEBNA**\n\n"
            "Rozumiem, że przeżywasz bardzo trudny moment. Twoje bezpieczeństwo jest najważniejsze.\n\n"
            "**PILNE KONTAKTY:**\n"
            "• **Telefon Zaufania**: 116 123 (bezpłatny, całodobowy)\n"
            "• **Pogotowie Ratunkowe**: 112\n"
            "• **Najbliższy SOR** (Szpitalny Oddział Ratunkowy)\n\n"
            "**Nie jesteś sam/sama.** Jeśli masz myśli o skrzywdzeniu siebie, proszę natychmiast skontaktuj się "
            "z którymś z powyższych numerów lub udaj się do najbliższego szpitala.\n\n"
            "Czy możesz mi powiedzieć, czy jesteś teraz w bezpiecznym miejscu?"
        )


        # Add crisis response to conversation
        self._session_manager.add_user_message(user_message)
        self._session_manager.add_assistant_message(crisis_response, "crisis_protocol_v1")

        # Log crisis response
        self._logger.log_info("🚨 Wysłano odpowiedź kryzysową")

        return WorkflowResult(
            success=True,
            message="Crisis protocol activated",
            data={
                "crisis_mode": True,
                "supervisor_decision": supervisor_decision,
                "therapist_response": crisis_response,
                "stage_changed": False,
                "current_stage": self._session_manager.get_current_stage()
            }
        )

    @staticmethod
    def _add_stage_transition_message(new_stage: str) -> None:
        """Add stage transition message to chat before therapist response."""
        # Import here to avoid circular imports
        import streamlit as st
        from ..session import load_stages

        stages = load_stages()
        current_stage_info = next((stage for stage in stages if stage["id"] == new_stage), None)

        if current_stage_info:
            stage_name = current_stage_info['name']
            stage_order = current_stage_info['order']

            transition_message = f"🎯 **Przeszliśmy do nowego etapu terapii**\n\n**Etap {stage_order}: {stage_name}**\n\nTerapeuta będzie teraz pracować z Tobą używając technik specyficznych dla tego etapu."

            # Initialize messages if not exists
            if "messages" not in st.session_state:
                st.session_state.messages = []

            # Add transition message before therapist response
            st.session_state.messages.append({
                "role": "assistant",
                "content": transition_message,
                "timestamp": "",
                "is_stage_transition": True
            })

