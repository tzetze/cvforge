"""
CV improvement module for CVForge.

Provides LLM-powered suggestions for enhancing CV content.
"""

from core.improvement.cv_improver import (
    CVImprover,
    ImprovementReport,
    ImprovementSuggestion,
    analyze_and_improve_cv
)

__all__ = [
    "CVImprover",
    "ImprovementReport",
    "ImprovementSuggestion",
    "analyze_and_improve_cv",
]

