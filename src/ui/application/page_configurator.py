"""Page configuration for Streamlit application."""

import streamlit as st
from config import Config


class PageConfigurator:
    """Handles Streamlit page configuration and styling."""

    @staticmethod
    def configure():
        """Configure Streamlit page settings and apply custom styling."""
        # Initialize configuration instance
        config = Config.get_instance()

        # Page configuration
        st.set_page_config(
            page_title=config.APP_TITLE,
            page_icon=config.APP_ICON,
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Custom CSS for sidebar styling
        st.markdown("""
        <style>
            .sidebar-divider {
                border-top: 2px solid #f0f2f6;
                margin: 1rem 0;
            }
        </style>
        """, unsafe_allow_html=True)