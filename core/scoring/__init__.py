"""
Achievement scoring module for CVForge.

This module provides functionality for scoring and ranking CV achievements
based on their relevance to job requirements.
"""

from core.scoring.achievement_scorer import (
    AchievementScorer,
    ScoredAchievement,
)

__all__ = [
    "AchievementScorer",
    "ScoredAchievement",
]

