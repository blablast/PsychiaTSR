"""Page routing functionality for Streamlit application."""

import streamlit as st
from src.ui.pages.therapy import therapy_page
from src.ui.pages.prompts import prompts_management_page
from src.ui.pages.export import export_project_page
from src.ui.pages.testing import testing_page
from src.ui.pages.model_test import model_test_page


class PageRouter:
    """Handles page selection and routing logic."""

    # Available pages configuration
    PAGES = {
        "🏠 Terapia": therapy_page,
        "📝 Prompty": prompts_management_page,
        "🧪 Testowanie": testing_page,
        "🤖 Test Modeli": model_test_page,
        "📦 Eksport Projektu": export_project_page
    }

    DEFAULT_PAGE = "🏠 Terapia"

    @classmethod
    def display_page_selector(cls):
        """Display the page selection dropdown in sidebar."""
        return st.sidebar.selectbox(
            "🔄 Wybierz stronę:",
            list(cls.PAGES.keys()),
            key="page_selector"
        )

    @classmethod
    def route_to_page(cls, selected_page: str):
        """Route to the appropriate page based on selection."""
        page_function = cls.PAGES.get(selected_page, cls.PAGES[cls.DEFAULT_PAGE])
        page_function()