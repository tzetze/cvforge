"""
Web routes for CVForge application.
"""

from web.routes.main import main_bp
from web.routes.cv_data import cv_data_bp
from web.routes.generate import generate_bp

__all__ = [
    'main_bp',
    'cv_data_bp',
    'generate_bp',
]

# Made with Bob
