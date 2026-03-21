"""
CV Data Management routes.

Handles viewing, editing, and managing CV data.
"""

import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from pathlib import Path

from core.data_manager import load_cv_data, save_cv_data
from core.models import CVData
from core.validation import validate_cv_data

logger = logging.getLogger(__name__)

cv_data_bp = Blueprint('cv_data', __name__)


@cv_data_bp.route('/')
def view():
    """View complete CV data."""
    try:
        cv_data_path = current_app.config['CV_DATA_PATH']
        
        if not cv_data_path.exists():
            flash('No CV data found. Please create your CV data first.', 'warning')
            return redirect(url_for('cv_data.create'))
        
        cv_data = load_cv_data(str(cv_data_path))
        return render_template('cv_data/view.html', cv_data=cv_data)
    
    except Exception as e:
        logger.error(f"Error loading CV data: {e}")
        flash(f'Error loading CV data: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))


@cv_data_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create new CV data from scratch."""
    if request.method == 'POST':
        # Handle CV creation
        # This would be a complex form, for now just show the template
        flash('CV creation form submitted', 'info')
        return redirect(url_for('cv_data.view'))
    
    return render_template('cv_data/create.html')


@cv_data_bp.route('/edit/personal-info', methods=['GET', 'POST'])
def edit_personal_info():
    """Edit personal information."""
    try:
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        if request.method == 'POST':
            # Update personal info
            cv_data.personal.name = request.form.get('name', '')
            cv_data.personal.email = request.form.get('email', '')
            cv_data.personal.phone = request.form.get('phone', '')
            cv_data.personal.location = request.form.get('location', '')
            cv_data.personal.linkedin = request.form.get('linkedin', '')
            cv_data.personal.github = request.form.get('github', '')
            cv_data.personal.website = request.form.get('website', '')
            
            # Save
            save_cv_data(cv_data, str(cv_data_path))
            flash('Personal information updated successfully', 'success')
            return redirect(url_for('cv_data.view'))
        
        return render_template('cv_data/edit_personal_info.html', cv_data=cv_data)
    
    except Exception as e:
        logger.error(f"Error editing personal info: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cv_data.view'))


@cv_data_bp.route('/edit/summary', methods=['GET', 'POST'])
def edit_summary():
    """Edit professional summary."""
    try:
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        if request.method == 'POST':
            cv_data.summary = request.form.get('summary', '')
            save_cv_data(cv_data, str(cv_data_path))
            flash('Summary updated successfully', 'success')
            return redirect(url_for('cv_data.view'))
        
        return render_template('cv_data/edit_summary.html', cv_data=cv_data)
    
    except Exception as e:
        logger.error(f"Error editing summary: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cv_data.view'))


@cv_data_bp.route('/experiences')
def list_experiences():
    """List all work experiences."""
    try:
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        return render_template('cv_data/experiences.html', cv_data=cv_data)
    
    except Exception as e:
        logger.error(f"Error loading experiences: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))


@cv_data_bp.route('/validate')
def validate():
    """Validate CV data and show report."""
    try:
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        validation_report = validate_cv_data(cv_data)
        
        return render_template(
            'cv_data/validate.html',
            cv_data=cv_data,
            report=validation_report
        )
    
    except Exception as e:
        logger.error(f"Error validating CV: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))


@cv_data_bp.route('/api/stats')
def api_stats():
    """API endpoint for CV statistics."""
    try:
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        stats = {
            'experiences': len(cv_data.experience),
            'achievements': sum(len(exp.achievements) for exp in cv_data.experience),
            'skills': len(cv_data.skills.technical) if cv_data.skills and cv_data.skills.technical else 0,
            'education': len(cv_data.education) if cv_data.education else 0,
        }
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
