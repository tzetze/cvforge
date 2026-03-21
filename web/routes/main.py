"""
Main routes for CVForge web application.

Handles home page, dashboard, and general navigation.
"""

import logging
from flask import Blueprint, render_template, current_app, flash
from pathlib import Path

from core.data_manager import load_cv_data
from core.validation import validate_cv_data

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page with overview and quick actions."""
    return render_template('index.html')


@main_bp.route('/dashboard')
def dashboard():
    """
    Dashboard showing CV status, validation results, and quick stats.
    """
    try:
        # Load CV data
        cv_data_path = current_app.config['CV_DATA_PATH']
        
        if not cv_data_path.exists():
            flash('No CV data found. Please create your CV data first.', 'warning')
            return render_template('dashboard.html', cv_data=None)
        
        cv_data = load_cv_data(str(cv_data_path))
        
        # Validate CV
        validation_report = validate_cv_data(cv_data)
        
        # Calculate stats
        stats = {
            'total_experiences': len(cv_data.experience),
            'total_achievements': sum(len(exp.achievements) for exp in cv_data.experience),
            'technical_skills': len(cv_data.skills.technical) if cv_data.skills and cv_data.skills.technical else 0,
            'education_entries': len(cv_data.education) if cv_data.education else 0,
            'certifications': len(cv_data.certifications) if cv_data.certifications else 0,
            'projects': len(cv_data.projects) if cv_data.projects else 0,
        }
        
        return render_template(
            'dashboard.html',
            cv_data=cv_data,
            validation_report=validation_report,
            stats=stats
        )
    
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash(f'Error loading CV data: {str(e)}', 'danger')
        return render_template('dashboard.html', cv_data=None)


@main_bp.route('/about')
def about():
    """About page with project information."""
    return render_template('about.html')

