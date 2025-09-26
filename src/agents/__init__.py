"""Agent System Package for PsychiaTSR Therapy Application.

This package implements the dual-agent architecture for Solution-Focused Brief Therapy,
providing specialized AI agents that work together to deliver therapeutic conversations.

Dual-Agent Architecture:
    TherapistAgent: Conducts therapy conversations following SFBT principles
        - Implements 5-stage therapy progression
        - Generates empathetic, therapeutic responses
        - Supports streaming for real-time interaction
        - Integrates safety monitoring for crisis detection

    SupervisorAgent: Evaluates therapy progress and manages stage transitions
        - Assesses conversation quality and therapeutic progress
        - Makes stage advancement decisions
        - Monitors goal achievement and therapy effectiveness
        - Provides structured evaluation output

Base Architecture:
    - AgentBase: Common functionality and dependency injection
    - AsyncAgentInterface: Streaming and asynchronous operation support
    - Service integration through dependency injection pattern

Therapy Stages:
    1. Opening: Goal setting and rapport building
    2. Resources: Identifying client strengths and exceptions
    3. Scaling: Progress measurement using 1-10 scales
    4. Small Steps: Concrete action planning
    5. Summary: Reinforcement and positive closure

Integration:
    Agents integrate with the workflow orchestration system, receiving
    prompts from the prompt management service and utilizing configured
    LLM providers for response generation.

Usage:
    Agents are created through the ServiceFactory with dependency injection,
    ensuring proper configuration and service integration throughout the system.
"""

from .therapist import TherapistAgent
from .supervisor import SupervisorAgent

__all__ = ["TherapistAgent", "SupervisorAgent"]
