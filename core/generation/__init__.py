"""
CV generation module for CVForge.

This module provides functionality for selecting relevant CV content,
tailoring it to specific job requirements using LLM, and generating
professional PDF CVs.
"""

from core.generation.cv_selector import CVContentSelector, SelectedContent
from core.generation.cv_tailor import CVTailoringEngine, TailoredCV
from core.generation.pdf_generator import PDFGenerator, generate_cv_pdf

__all__ = [
    "CVContentSelector",
    "SelectedContent",
    "CVTailoringEngine",
    "TailoredCV",
    "PDFGenerator",
    "generate_cv_pdf",
]

