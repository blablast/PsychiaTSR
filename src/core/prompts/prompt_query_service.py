"""Prompt query service - handles complex queries and search operations."""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from .prompt_repository import SystemPromptRepository, StagePromptRepository


class PromptQueryService:
    """Handles complex queries and search operations across prompt repositories."""

    def __init__(self, system_repo: SystemPromptRepository, stage_repo: StagePromptRepository):
        self.system_repo = system_repo
        self.stage_repo = stage_repo

    def search_prompts(self,
                      query: str,
                      search_in: List[str] = None,
                      prompt_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search prompts by text content.

        Args:
            query: Search query text
            search_in: Where to search (content, title, note) - defaults to all
            prompt_types: Types to search (system, stage) - defaults to all

        Returns:
            List of matching prompts with search metadata
        """
        if not query or not query.strip():
            return []

        query_lower = query.lower().strip()
        search_in = search_in or ["content", "title", "note"]
        prompt_types = prompt_types or ["system", "stage"]
        results = []

        # Search system prompts
        if "system" in prompt_types:
            system_prompts = self.system_repo.list_all_prompts()
            for prompt in system_prompts:
                matches = self._search_in_prompt(prompt, query_lower, search_in)
                if matches:
                    result = prompt.copy()
                    result["search_metadata"] = {
                        "type": "system",
                        "matches": matches,
                        "relevance_score": len(matches)
                    }
                    results.append(result)

        # Search stage prompts
        if "stage" in prompt_types:
            stage_prompts = self.stage_repo.list_all_prompts()
            for prompt in stage_prompts:
                matches = self._search_in_prompt(prompt, query_lower, search_in)
                if matches:
                    result = prompt.copy()
                    result["search_metadata"] = {
                        "type": "stage",
                        "matches": matches,
                        "relevance_score": len(matches)
                    }
                    results.append(result)

        # Sort by relevance (number of matches)
        results.sort(key=lambda x: x["search_metadata"]["relevance_score"], reverse=True)

        return results

    def get_prompts_by_status(self, status: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all prompts with specific status.

        Args:
            status: Status to filter by (active, inactive, draft)

        Returns:
            Dictionary with system and stage prompts
        """
        result = {
            "system": [],
            "stage": []
        }

        # Get system prompts with status
        system_prompts = self.system_repo.list_all_prompts()
        result["system"] = [
            prompt for prompt in system_prompts
            if prompt.get("metadata", {}).get("status") == status
        ]

        # Get stage prompts with status
        stage_prompts = self.stage_repo.list_all_prompts()
        result["stage"] = [
            prompt for prompt in stage_prompts
            if prompt.get("metadata", {}).get("status") == status
        ]

        return result

    def get_prompts_by_date_range(self,
                                 start_date: str,
                                 end_date: str,
                                 date_field: str = "created_at") -> List[Dict[str, Any]]:
        """
        Get prompts created/updated within date range.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            date_field: Field to filter by (created_at, updated_at)

        Returns:
            List of prompts within date range
        """
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            return []

        results = []

        # Check system prompts
        system_prompts = self.system_repo.list_all_prompts()
        for prompt in system_prompts:
            prompt_date_str = prompt.get("metadata", {}).get(date_field)
            if prompt_date_str and self._is_in_date_range(prompt_date_str, start_dt, end_dt):
                prompt_with_type = prompt.copy()
                prompt_with_type["prompt_type"] = "system"
                results.append(prompt_with_type)

        # Check stage prompts
        stage_prompts = self.stage_repo.list_all_prompts()
        for prompt in stage_prompts:
            prompt_date_str = prompt.get("metadata", {}).get(date_field)
            if prompt_date_str and self._is_in_date_range(prompt_date_str, start_dt, end_dt):
                prompt_with_type = prompt.copy()
                prompt_with_type["prompt_type"] = "stage"
                results.append(prompt_with_type)

        # Sort by date (newest first)
        results.sort(
            key=lambda x: x.get("metadata", {}).get(date_field, ""),
            reverse=True
        )

        return results

    def get_agent_prompt_summary(self, agent_type: str) -> Dict[str, Any]:
        """
        Get comprehensive summary of prompts for an agent.

        Args:
            agent_type: Agent type (therapist, supervisor)

        Returns:
            Summary dictionary with counts and details
        """
        summary = {
            "agent": agent_type,
            "system_prompts": {
                "total": 0,
                "active": 0,
                "inactive": 0,
                "latest": None
            },
            "stage_prompts": {
                "total": 0,
                "active": 0,
                "inactive": 0,
                "by_stage": {}
            }
        }

        # System prompts summary
        system_prompts = [
            p for p in self.system_repo.list_all_prompts()
            if p.get("metadata", {}).get("agent") == agent_type
        ]

        summary["system_prompts"]["total"] = len(system_prompts)

        for prompt in system_prompts:
            status = prompt.get("metadata", {}).get("status", "unknown")
            if status == "active":
                summary["system_prompts"]["active"] += 1
                summary["system_prompts"]["latest"] = prompt
            elif status == "inactive":
                summary["system_prompts"]["inactive"] += 1

        # Stage prompts summary
        stage_prompts = self.stage_repo.get_all_for_agent(agent_type)
        summary["stage_prompts"]["total"] = len(stage_prompts)

        for prompt in stage_prompts:
            status = prompt.get("metadata", {}).get("status", "unknown")
            stage = prompt.get("metadata", {}).get("stage", "unknown")

            if status == "active":
                summary["stage_prompts"]["active"] += 1
            elif status == "inactive":
                summary["stage_prompts"]["inactive"] += 1

            # Group by stage
            if stage not in summary["stage_prompts"]["by_stage"]:
                summary["stage_prompts"]["by_stage"][stage] = {
                    "total": 0,
                    "active": 0,
                    "inactive": 0
                }

            summary["stage_prompts"]["by_stage"][stage]["total"] += 1
            if status == "active":
                summary["stage_prompts"]["by_stage"][stage]["active"] += 1
            elif status == "inactive":
                summary["stage_prompts"]["by_stage"][stage]["inactive"] += 1

        return summary

    def find_duplicates(self, similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Find potentially duplicate prompts based on content similarity.

        Args:
            similarity_threshold: Similarity threshold (0.0 to 1.0)

        Returns:
            List of potential duplicate groups
        """
        # Simple implementation - in production you might use more sophisticated similarity algorithms
        all_prompts = []

        # Collect all prompts
        system_prompts = self.system_repo.list_all_prompts()
        for prompt in system_prompts:
            prompt["prompt_type"] = "system"
            all_prompts.append(prompt)

        stage_prompts = self.stage_repo.list_all_prompts()
        for prompt in stage_prompts:
            prompt["prompt_type"] = "stage"
            all_prompts.append(prompt)

        duplicates = []
        checked = set()

        for i, prompt1 in enumerate(all_prompts):
            if i in checked:
                continue

            similar_group = [prompt1]
            content1 = self._get_prompt_content(prompt1)

            for j, prompt2 in enumerate(all_prompts[i+1:], i+1):
                if j in checked:
                    continue

                content2 = self._get_prompt_content(prompt2)
                similarity = self._calculate_similarity(content1, content2)

                if similarity >= similarity_threshold:
                    similar_group.append(prompt2)
                    checked.add(j)

            if len(similar_group) > 1:
                duplicates.append({
                    "group_size": len(similar_group),
                    "similarity_score": similarity_threshold,
                    "prompts": similar_group
                })

            checked.add(i)

        return duplicates

    def _search_in_prompt(self, prompt: Dict[str, Any], query: str, search_in: List[str]) -> List[str]:
        """Search for query in prompt and return list of matches."""
        matches = []

        # Search in content
        if "content" in search_in:
            sections = prompt.get("configuration", {}).get("sections", {})
            for section_name, section_data in sections.items():
                content = section_data.get("content", "").lower()
                if query in content:
                    matches.append(f"content:{section_name}")

        # Search in titles
        if "title" in search_in:
            sections = prompt.get("configuration", {}).get("sections", {})
            for section_name, section_data in sections.items():
                title = section_data.get("title", "").lower()
                if query in title:
                    matches.append(f"title:{section_name}")

        # Search in note
        if "note" in search_in:
            note = prompt.get("metadata", {}).get("note", "").lower()
            if query in note:
                matches.append("note")

        return matches

    def _is_in_date_range(self, date_str: str, start_dt: datetime, end_dt: datetime) -> bool:
        """Check if date string falls within date range."""
        try:
            prompt_dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return start_dt <= prompt_dt <= end_dt
        except ValueError:
            return False

    def _get_prompt_content(self, prompt: Dict[str, Any]) -> str:
        """Extract all text content from prompt for similarity comparison."""
        content_parts = []

        sections = prompt.get("configuration", {}).get("sections", {})
        for section_data in sections.values():
            title = section_data.get("title", "")
            content = section_data.get("content", "")
            content_parts.extend([title, content])

        return " ".join(content_parts).lower()

    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculate simple similarity score between two content strings."""
        if not content1 or not content2:
            return 0.0

        # Simple word-based similarity
        words1 = set(content1.split())
        words2 = set(content2.split())

        if not words1 and not words2:
            return 1.0

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0