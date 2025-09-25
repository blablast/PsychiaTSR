"""Manages therapy stage information and progression logic."""

import json
from pathlib import Path
from typing import List, Optional

from .stage_info import StageInfo


class StageManager:
    """Manages therapy stage information and progression logic."""

    def __init__(self, stages_config_path: str):
        self._stages_config_path = stages_config_path
        self._stages_cache: Optional[List[StageInfo]] = None

    def get_all_stages(self) -> List[StageInfo]:
        """Get all available therapy stages."""
        if self._stages_cache is None:
            self._load_stages()
        return self._stages_cache or []

    def get_first_stage(self) -> Optional[StageInfo]:
        """Get the first stage in the progression."""
        stages = self.get_all_stages()
        if not stages:
            return None
        # Return stage with lowest order (already sorted in _load_stages)
        return min(stages, key=lambda stage: stage.order)

    def get_stage_by_id(self, stage_id: str) -> Optional[StageInfo]:
        """Get stage information by ID."""
        stages = self.get_all_stages()
        return next((stage for stage in stages if stage.stage_id == stage_id), None)

    def get_next_stage(self, current_stage_id: str) -> Optional[StageInfo]:
        """Get the next stage in the progression."""
        stages = self.get_all_stages()
        current_stage = self._get_current_stage(current_stage_id)

        next_stages = [s for s in stages if s.order == current_stage.order + 1]
        return next_stages[0] if next_stages else None

    def get_previous_stage(self, current_stage_id: str) -> Optional[StageInfo]:
        """Get the previous stage in the progression."""
        stages = self.get_all_stages()
        current_stage = self._get_current_stage(current_stage_id)

        prev_stages = [s for s in stages if s.order == current_stage.order - 1]
        return prev_stages[0] if prev_stages else None

    def _get_current_stage(self, stage_id: str) -> Optional[StageInfo]:
        """Get current stage information by ID."""
        stages = self.get_all_stages()
        current_stage = self.get_stage_by_id(stage_id)

        if not current_stage:
            return self.get_first_stage()

        return current_stage

    def _load_stages(self) -> None:
        """Load stages from configuration file."""
        try:
            stages_file = Path(self._stages_config_path) / "stages.json"
            with open(stages_file, 'r', encoding='utf-8') as f:
                stages_data = json.load(f)

            self._stages_cache = [
                StageInfo(
                    stage_id=stage["id"],
                    name=stage["name"],
                    order=stage["order"],
                    description=stage.get("description")
                )
                for stage in stages_data
            ]

            # Sort by order
            self._stages_cache.sort(key=lambda x: x.order)

        except Exception as e:
            raise ValueError(f"Failed to load stages configuration: {str(e)}")