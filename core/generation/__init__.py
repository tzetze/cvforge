"""
CV generation module for CVForge.

This module provides functionality for selecting relevant CV content
and tailoring it to specific job requirements using LLM.
"""

from core.generation.cv_selector import CVContentSelector, SelectedContent
from core.generation.cv_tailor import CVTailoringEngine, TailoredCV

__all__ = [
    "CVContentSelector",
    "SelectedContent",
    "CVTailoringEngine",
    "TailoredCV",
]

