"""UI Pages Package for PsychiaTSR Streamlit Application.

This package contains all Streamlit page implementations for the therapy system,
organized by functionality and following clean architecture principles.

Page Categories:
    Therapy Pages:
        - therapy.py: Main conversation interface with dual-agent system
        - conversation_settings.py: LLM provider and model configuration

    Management Pages:
        - prompts_unified.py: Comprehensive prompt management interface
        - prompts_new.py: Advanced prompt editing and testing

    Testing & Development:
        - model_test.py: 5-stage model testing and validation
        - testing.py: Development utilities and debugging tools

    Data & Export:
        - export.py: Session data export and analysis
        - reports.py: Therapy session analytics (planned)

Architecture:
    - Clean separation from business logic (src/core/)
    - Service layer integration through dependency injection
    - Streamlit session state management for UI persistence
    - Component-based design with reusable UI elements

Integration:
    Pages integrate with the core workflow system, session management,
    and configuration services while maintaining UI layer boundaries.

Navigation:
    Central navigation through sidebar with page routing handled
    by the main application controller (app.py).
"""