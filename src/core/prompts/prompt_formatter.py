"""Prompt formatting service - handles text formatting and generation."""

from typing import Dict, Any


class PromptFormatter:
    """Handles formatting of prompt data into text suitable for LLM consumption."""

    @staticmethod
    def generate_prompt_text(prompt_data: Dict[str, Any], prompt_type: str = "stage") -> str:
        """
        Generate final prompt text from structured data.

        Args:
            prompt_data: Structured prompt configuration
            prompt_type: Type of prompt (stage, system)

        Returns:
            Generated prompt text ready for LLM consumption
        """
        if not prompt_data:
            return f"# Empty {prompt_type.upper()} PROMPT"

        prompt_parts = []

        # Get metadata
        metadata = prompt_data.get("metadata", {})
        prompt_id = metadata.get("id", "unknown")
        agent = metadata.get("agent", "unknown")

        # Header with metadata
        prompt_parts.append(f"# {prompt_type.upper()} PROMPT - {agent.upper()} - ID {prompt_id}")
        prompt_parts.append("")

        # Add note if present
        note = metadata.get("note")
        if note:
            prompt_parts.append(f"<!-- {note} -->")
            prompt_parts.append("")

        # Generate content from sections
        sections = prompt_data.get("configuration", {}).get("sections", {})

        if not sections:
            prompt_parts.append("<!-- No sections defined -->")
            return "\n".join(prompt_parts)

        for section_key, section in sections.items():
            title = section.get("title", section_key.replace("_", " ").title())
            content = section.get("content", "")

            if content and content.strip():
                prompt_parts.append(f"## {title}")
                prompt_parts.append(content.strip())
                prompt_parts.append("")

        return "\n".join(prompt_parts).strip()

    @staticmethod
    def format_prompt_summary(prompt_data: Dict[str, Any]) -> str:
        """
        Generate a brief summary of prompt for display purposes.

        Args:
            prompt_data: Structured prompt configuration

        Returns:
            Brief prompt summary
        """
        if not prompt_data:
            return "Empty prompt"

        metadata = prompt_data.get("metadata", {})
        sections = prompt_data.get("configuration", {}).get("sections", {})

        # Basic info
        agent = metadata.get("agent", "unknown")
        prompt_id = metadata.get("id", "unknown")
        status = metadata.get("status", "unknown")

        # Count sections and estimate length
        section_count = len(sections)
        total_chars = sum(len(section.get("content", "")) for section in sections.values())

        summary_parts = [
            f"ID {prompt_id}",
            f"{agent}",
            f"{status}",
            f"{section_count} sections",
            f"~{total_chars} chars",
        ]

        return " | ".join(summary_parts)

    @staticmethod
    def format_section_preview(section_data: Dict[str, Any], max_length: int = 100) -> str:
        """
        Generate a preview of a section's content.

        Args:
            section_data: Section data with title and content
            max_length: Maximum length of preview

        Returns:
            Truncated section content preview
        """
        content = section_data.get("content", "")
        if not content:
            return "[Empty section]"

        # Clean up content for preview
        cleaned = content.replace("\n", " ").replace("\r", " ").strip()

        if len(cleaned) <= max_length:
            return cleaned

        # Truncate and add ellipsis
        return cleaned[: max_length - 3] + "..."

    @staticmethod
    def format_metadata_display(metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Format metadata for display in UI.

        Args:
            metadata: Raw metadata dictionary

        Returns:
            Formatted metadata for display
        """
        display_metadata = {}

        # Format ID
        prompt_id = metadata.get("id")
        display_metadata["ID"] = str(prompt_id) if prompt_id is not None else "Unknown"

        # Format agent
        agent = metadata.get("agent", "unknown")
        display_metadata["Agent"] = agent.title()

        # Format stage (if present)
        stage = metadata.get("stage")
        if stage is not None:
            stage_names = {
                1: "Opening",
                2: "Resources",
                3: "Scaling",
                4: "Small Steps",
                5: "Summary",
                6: "Rest/Safety",
            }
            stage_name = stage_names.get(stage, f"Stage {stage}")
            display_metadata["Stage"] = f"{stage} ({stage_name})"

        # Format status
        status = metadata.get("status", "unknown")
        status_display = {"active": "🟢 Active", "inactive": "⚪ Inactive", "draft": "🟡 Draft"}
        display_metadata["Status"] = status_display.get(status, status.title())

        # Format dates
        created_at = metadata.get("created_at")
        if created_at:
            display_metadata["Created"] = PromptFormatter._format_datetime(created_at)

        updated_at = metadata.get("updated_at")
        if updated_at:
            display_metadata["Updated"] = PromptFormatter._format_datetime(updated_at)

        # Format note
        note = metadata.get("note")
        if note:
            display_metadata["Note"] = note

        return display_metadata

    @staticmethod
    def _format_datetime(datetime_str: str) -> str:
        """Format ISO datetime string for display."""
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return datetime_str

    @staticmethod
    def format_prompt_for_export(prompt_data: Dict[str, Any], format_type: str = "markdown") -> str:
        """
        Format prompt for export in various formats.

        Args:
            prompt_data: Structured prompt configuration
            format_type: Export format (markdown, txt, json)

        Returns:
            Formatted prompt for export
        """
        if format_type.lower() == "json":
            import json

            return json.dumps(prompt_data, indent=2, ensure_ascii=False)

        elif format_type.lower() == "txt":
            # Plain text format
            text_parts = []

            metadata = prompt_data.get("metadata", {})
            text_parts.append(f"PROMPT ID: {metadata.get('id', 'unknown')}")
            text_parts.append(f"AGENT: {metadata.get('agent', 'unknown')}")
            text_parts.append(f"STATUS: {metadata.get('status', 'unknown')}")
            text_parts.append("")

            sections = prompt_data.get("configuration", {}).get("sections", {})
            for section_key, section in sections.items():
                title = section.get("title", section_key.title())
                content = section.get("content", "")

                text_parts.append(f"{title.upper()}")
                text_parts.append("-" * len(title))
                text_parts.append(content)
                text_parts.append("")

            return "\n".join(text_parts)

        else:  # Default to markdown
            return PromptFormatter.generate_prompt_text(prompt_data)
