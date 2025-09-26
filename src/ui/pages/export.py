"""Export project page for Psychia TSR"""

import streamlit as st
import os
import zipfile
import io
from datetime import datetime


def export_project_page():
    """Export project page with all files"""
    st.title("📦 Eksport Projektu")

    # Get all project files
    project_files = []
    excluded_dirs = {"venv", "data", "__pycache__", ".git", ".vscode", "node_modules", "models"}

    # Walk through the project directory
    for root, dirs, files in os.walk("."):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in excluded_dirs]

        for file in files:
            # Skip hidden files, .pyc files, and other non-source files
            if (
                not file.startswith(".")
                and not file.endswith(".pyc")
                and not file.endswith(".pyo")
                and file != "requirements.txt.bak"
            ):
                file_path = os.path.join(root, file)
                project_files.append(file_path)

    st.info(f"Znaleziono {len(project_files)} plików do eksportu")

    # Create ZIP download button
    if st.button("💾 Pobierz projekt jako ZIP", type="primary"):
        # Create ZIP in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in project_files:
                try:
                    # Add file to ZIP
                    zip_file.write(file_path, file_path)
                except Exception as e:
                    st.warning(f"Nie można dodać {file_path} do ZIP: {str(e)}")

        zip_buffer.seek(0)

        # Create download
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"psychia_project_{timestamp}.zip"

        st.download_button(
            label="⬇️ Pobierz ZIP",
            data=zip_buffer.getvalue(),
            file_name=zip_filename,
            mime="application/zip",
        )

        st.success(f"ZIP utworzony: {zip_filename}")

    st.markdown("---")

    # Display each file with filename and content
    for file_path in sorted(project_files):
        with st.expander(f"📄 {file_path}"):
            col1, col2 = st.columns([1, 3])

            with col1:
                st.text_input(
                    "Nazwa pliku:", value=file_path, key=f"filename_{file_path}", disabled=True
                )

            with col2:
                try:
                    # Try to read file content
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    st.text_area(
                        "Zawartość:", value=content, height=200, key=f"content_{file_path}"
                    )
                except Exception as e:
                    st.error(f"Nie można odczytać pliku: {str(e)}")
