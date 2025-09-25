"""Async workflow manager that integrates with Streamlit via the bridge."""

from typing import AsyncGenerator, Generator

from .strategies.async_conversation_workflow_strategy import AsyncConversationWorkflowStrategy
from ...ui.workflow.async_streamlit_bridge import StreamlitAsyncBridge, async_to_sync, async_generator_to_sync


class AsyncWorkflowManager:
    """
    Async workflow manager that provides high-performance async workflows
    while maintaining compatibility with Streamlit's synchronous environment.
    """

    def __init__(self, agent_provider, prompt_manager, conversation_manager, logger):
        """Initialize with injected dependencies."""
        self._agent_provider = agent_provider
        self._prompt_manager = prompt_manager
        self._conversation_manager = conversation_manager
        self._logger = logger

        # Create async strategy
        self._async_strategy = AsyncConversationWorkflowStrategy(
            agent_provider=agent_provider,
            prompt_manager=prompt_manager,
            conversation_manager=conversation_manager,
            logger=logger
        )

    @async_to_sync
    async def process_user_message_async(self, user_message: str, current_stage: str) -> dict:
        """
        Process user message asynchronously and return result.

        This method can be called from Streamlit as if it were synchronous,
        but internally uses async/await for better performance.
        """
        try:
            if self._logger:
                self._logger.log_info("Starting async workflow processing")

            result = await self._async_strategy.process_user_message_async(
                user_message=user_message,
                current_stage=current_stage
            )

            if result.success:
                return {
                    "success": True,
                    "response": result.data.get("response", ""),
                    "supervisor_decision": result.data.get("supervisor_decision"),
                    "response_time_ms": result.data.get("response_time_ms", 0),
                    "message": result.message
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "message": result.message
                }

        except Exception as e:
            if self._logger:
                self._logger.log_error(f"Async workflow processing failed: {str(e)}")

            return {
                "success": False,
                "error": str(e),
                "message": f"Async workflow failed: {str(e)}"
            }

    @async_generator_to_sync
    async def process_user_message_streaming_async(self, user_message: str, current_stage: str) -> Generator[str, None, None]:
        """
        Process user message with streaming response asynchronously.

        This method can be used in Streamlit as a regular generator,
        but internally uses async streaming for better performance.
        """
        try:
            if self._logger:
                self._logger.log_info("Starting async streaming workflow processing")

            async for chunk in self._async_strategy.process_user_message_streaming_async(
                user_message=user_message,
                current_stage=current_stage
            ):
                yield chunk

        except Exception as e:
            if self._logger:
                self._logger.log_error(f"Async streaming workflow processing failed: {str(e)}")
            yield f"[Błąd async streaming: {str(e)}]"

    @staticmethod
    def is_async_available() -> bool:
        """Check if async functionality is available and working."""
        try:
            # Test that we can create and run a simple async operation
            async def test_async():
                return True

            result = StreamlitAsyncBridge.run_async(test_async())
            return result is True
        except Exception:
            return False

    def get_performance_info(self) -> dict:
        """Get information about async performance capabilities."""
        return {
            "async_available": self.is_async_available(),
            "bridge_active": StreamlitAsyncBridge.is_bridge_active(),
            "features": [
                "Async LLM calls",
                "Concurrent agent processing",
                "Real-time streaming",
                "Non-blocking I/O"
            ],
            "benefits": [
                "Faster response times",
                "Better resource utilization",
                "Improved user experience",
                "Scalable processing"
            ]
        }

    def cleanup(self):
        """Clean up async resources."""
        try:
            StreamlitAsyncBridge.close()
            if self._logger:
                self._logger.log_info("Async workflow manager cleaned up successfully")
        except Exception as e:
            if self._logger:
                self._logger.log_error(f"Error during async cleanup: {str(e)}")


# Convenience functions
def create_async_workflow_manager(agent_provider, prompt_manager, conversation_manager, logger):
    """Create an async workflow manager with the provided dependencies."""
    return AsyncWorkflowManager(
        agent_provider=agent_provider,
        prompt_manager=prompt_manager,
        conversation_manager=conversation_manager,
        logger=logger
    )


def send_supervisor_request_stream_async(prompt: str) -> Generator[str, None, None]:
    """
    Async version of send_supervisor_request_stream.

    This function provides async performance benefits for supervisor requests.
    """
    import streamlit as st

    # Get current session components
    if 'conversation_manager' not in st.session_state:
        yield "[Błąd: Brak managera konwersacji]"
        return

    # Create async workflow manager
    from ..prompts.unified_prompt_manager import UnifiedPromptManager
    from config import Config

    try:
        # Get dependencies (similar to existing workflow)
        config = Config.get_instance()
        prompt_manager = UnifiedPromptManager(config.PROMPT_DIR)
        from ...ui.session.streamlit_agent_provider import StreamlitAgentProvider
        agent_provider = StreamlitAgentProvider()

        # Create async workflow manager
        async_manager = create_async_workflow_manager(
            agent_provider=agent_provider,
            prompt_manager=prompt_manager,
            conversation_manager=st.session_state.conversation_manager,
            logger=getattr(st.session_state, 'therapy_session_logger', None)
        )

        # Process with async streaming
        current_stage = getattr(st.session_state, 'current_stage', 'opening')

        # Use the async streaming workflow
        yield from async_manager.process_user_message_streaming_async(prompt, current_stage)

    except Exception as e:
        yield f"[Błąd async workflow: {str(e)}]"