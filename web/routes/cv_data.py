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
        return redirect(url_for('main.index'))


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
            # Collect form data and convert empty strings to None for optional fields
            personal_data = {
                'name': request.form.get('name', ''),
                'email': request.form.get('email', ''),
                'phone': request.form.get('phone', '').strip() or None,
                'location': request.form.get('location', '').strip() or None,
                'linkedin': request.form.get('linkedin', '').strip() or None,
                'github': request.form.get('github', '').strip() or None,
                'website': request.form.get('website', '').strip() or None,
            }
            
            # Create new PersonalInfo object (Pydantic will validate)
            from core.models import PersonalInfo
            cv_data.personal = PersonalInfo(**personal_data)
            
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


@cv_data_bp.route('/edit/experience', methods=['GET', 'POST'])
def edit_experience():
    """Edit work experience entries."""
    try:
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        if request.method == 'POST':
            from core.models import Experience, Achievement
            
            # Parse form data for experiences
            experiences = []
            exp_count = 0
            
            # Count how many experiences were submitted
            while f'experience[{exp_count}][company]' in request.form:
                exp_count += 1
            
            # Process each experience
            for i in range(exp_count):
                # Get basic experience data
                company = request.form.get(f'experience[{i}][company]', '').strip()
                position = request.form.get(f'experience[{i}][position]', '').strip()
                
                if not company or not position:
                    continue  # Skip empty entries
                
                location = request.form.get(f'experience[{i}][location]', '').strip() or None
                start_date = request.form.get(f'experience[{i}][start_date]', '').strip()
                end_date = request.form.get(f'experience[{i}][end_date]', '').strip() or None
                description = request.form.get(f'experience[{i}][description]', '').strip() or None
                
                # Parse achievements for this experience
                achievements = []
                ach_count = 0
                while f'experience[{i}][achievements][{ach_count}][text]' in request.form:
                    ach_text = request.form.get(f'experience[{i}][achievements][{ach_count}][text]', '').strip()
                    
                    if ach_text:
                        # Get skills (comma-separated)
                        skills_str = request.form.get(f'experience[{i}][achievements][{ach_count}][skills]', '')
                        skills = [s.strip() for s in skills_str.split(',') if s.strip()]
                        
                        from core.models import ImpactLevel
                        impact_str = request.form.get(f'experience[{i}][achievements][{ach_count}][impact]', 'medium')
                        impact = ImpactLevel(impact_str) if impact_str else ImpactLevel.MEDIUM
                        
                        # Parse metrics as key-value pairs
                        metrics = {}
                        metric_count = 0
                        while f'experience[{i}][achievements][{ach_count}][metrics][{metric_count}][key]' in request.form:
                            key = request.form.get(f'experience[{i}][achievements][{ach_count}][metrics][{metric_count}][key]', '').strip()
                            value = request.form.get(f'experience[{i}][achievements][{ach_count}][metrics][{metric_count}][value]', '').strip()
                            
                            if key and value:
                                # Try to convert to number if possible
                                try:
                                    if '.' in value:
                                        metrics[key] = float(value)
                                    else:
                                        metrics[key] = int(value)
                                except ValueError:
                                    # Keep as string
                                    metrics[key] = value
                            
                            metric_count += 1
                        
                        # If no metrics were added, set to None
                        if not metrics:
                            metrics = None
                        
                        # Get keywords (comma-separated, optional)
                        keywords_str = request.form.get(f'experience[{i}][achievements][{ach_count}][keywords]', '').strip()
                        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()] if keywords_str else None
                        
                        achievement = Achievement(
                            text=ach_text,
                            skills=skills,
                            impact=impact,
                            metrics=metrics,
                            keywords=keywords
                        )
                        achievements.append(achievement)
                    
                    ach_count += 1
                
                # Create experience entry if it has at least one achievement
                if achievements:
                    experience = Experience(
                        company=company,
                        position=position,
                        location=location,
                        start_date=start_date,
                        end_date=end_date,
                        description=description,
                        achievements=achievements
                    )
                    experiences.append(experience)
            
            # Update CV data
            if experiences:
                cv_data.experience = experiences
                save_cv_data(cv_data, str(cv_data_path))
                flash('Experience updated successfully', 'success')
            else:
                flash('At least one experience with achievements is required', 'warning')
            
            return redirect(url_for('cv_data.view'))
        
        return render_template('cv_data/edit_experience.html', cv_data=cv_data)
    
    except Exception as e:
        logger.error(f"Error editing experience: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cv_data.view'))


@cv_data_bp.route('/edit/skills', methods=['GET', 'POST'])
def edit_skills():
    """Edit skills section."""
    try:
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        if request.method == 'POST':
            from core.models import Skills, TechnicalSkill, Language
            
            # Parse technical skills
            technical_skills = []
            tech_count = 0
            while f'technical[{tech_count}][name]' in request.form:
                name = request.form.get(f'technical[{tech_count}][name]', '').strip()
                if name:
                    from core.models import SkillLevel
                    level_str = request.form.get(f'technical[{tech_count}][level]', '').strip()
                    level = SkillLevel(level_str) if level_str else None
                    years_str = request.form.get(f'technical[{tech_count}][years]', '').strip()
                    years = int(years_str) if years_str and years_str.isdigit() else None
                    
                    technical_skills.append(TechnicalSkill(
                        name=name,
                        level=level,
                        years=years
                    ))
                tech_count += 1
            
            # Parse soft skills
            soft_skills = []
            soft_count = 0
            while f'soft[{soft_count}]' in request.form:
                skill = request.form.get(f'soft[{soft_count}]', '').strip()
                if skill:
                    soft_skills.append(skill)
                soft_count += 1
            
            # Parse languages
            languages = []
            lang_count = 0
            while f'languages[{lang_count}][language]' in request.form:
                language = request.form.get(f'languages[{lang_count}][language]', '').strip()
                proficiency = request.form.get(f'languages[{lang_count}][proficiency]', '').strip()
                if language and proficiency:
                    languages.append(Language(
                        language=language,
                        proficiency=proficiency
                    ))
                lang_count += 1
            
            # Create Skills object
            cv_data.skills = Skills(
                technical=technical_skills if technical_skills else None,
                soft=soft_skills if soft_skills else None,
                languages=languages if languages else None
            )
            
            save_cv_data(cv_data, str(cv_data_path))
            flash('Skills updated successfully', 'success')
            return redirect(url_for('cv_data.view'))
        
        return render_template('cv_data/edit_skills.html', cv_data=cv_data)
    
    except Exception as e:
        logger.error(f"Error editing skills: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cv_data.view'))


@cv_data_bp.route('/edit/education', methods=['GET', 'POST'])
def edit_education():
    """Edit education entries."""
    try:
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        if request.method == 'POST':
            from core.models import Education
            
            # Parse education entries
            education_list = []
            edu_count = 0
            
            while f'education[{edu_count}][institution]' in request.form:
                institution = request.form.get(f'education[{edu_count}][institution]', '').strip()
                degree = request.form.get(f'education[{edu_count}][degree]', '').strip()
                
                if institution and degree:
                    field = request.form.get(f'education[{edu_count}][field]', '').strip() or None
                    from core.models import EducationStatus
                    location = request.form.get(f'education[{edu_count}][location]', '').strip() or None
                    start_date = request.form.get(f'education[{edu_count}][start_date]', '').strip() or None
                    graduation_date = request.form.get(f'education[{edu_count}][graduation_date]', '').strip() or None
                    status_str = request.form.get(f'education[{edu_count}][status]', '').strip()
                    status = EducationStatus(status_str) if status_str else None
                    gpa = request.form.get(f'education[{edu_count}][gpa]', '').strip() or None
                    
                    # Parse honors (comma-separated)
                    honors_str = request.form.get(f'education[{edu_count}][honors]', '').strip()
                    honors = [h.strip() for h in honors_str.split(',') if h.strip()] if honors_str else None
                    
                    # Parse coursework (comma-separated)
                    coursework_str = request.form.get(f'education[{edu_count}][relevant_coursework]', '').strip()
                    coursework = [c.strip() for c in coursework_str.split(',') if c.strip()] if coursework_str else None
                    
                    education = Education(
                        institution=institution,
                        degree=degree,
                        field=field,
                        location=location,
                        start_date=start_date,
                        graduation_date=graduation_date,
                        status=status,
                        gpa=gpa,
                        honors=honors,
                        relevant_coursework=coursework
                    )
                    education_list.append(education)
                
                edu_count += 1
            
            # Update CV data
            cv_data.education = education_list if education_list else None
            save_cv_data(cv_data, str(cv_data_path))
            flash('Education updated successfully', 'success')
            return redirect(url_for('cv_data.view'))
        
        return render_template('cv_data/edit_education.html', cv_data=cv_data)
    
    except Exception as e:
        logger.error(f"Error editing education: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cv_data.view'))


@cv_data_bp.route('/edit/certifications', methods=['GET', 'POST'])
def edit_certifications():
    """Edit certifications."""
    try:
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        if request.method == 'POST':
            # TODO: Implement certification editing
            flash('Certification editing not yet implemented', 'info')
            return redirect(url_for('cv_data.view'))
        
        return render_template('cv_data/edit_certifications.html', cv_data=cv_data)
    
    except Exception as e:
        logger.error(f"Error editing certifications: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cv_data.view'))


@cv_data_bp.route('/edit/volunteer', methods=['GET', 'POST'])
def edit_volunteer():
    """Edit volunteer work."""
    try:
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        if request.method == 'POST':
            # TODO: Implement volunteer work editing
            flash('Volunteer work editing not yet implemented', 'info')
            return redirect(url_for('cv_data.view'))
        
        return render_template('cv_data/edit_volunteer.html', cv_data=cv_data)
    
    except Exception as e:
        logger.error(f"Error editing volunteer work: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cv_data.view'))


@cv_data_bp.route('/edit/projects', methods=['GET', 'POST'])
def edit_projects():
    """Edit projects."""
    try:
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        if request.method == 'POST':
            # TODO: Implement projects editing
            flash('Projects editing not yet implemented', 'info')
            return redirect(url_for('cv_data.view'))
        
        return render_template('cv_data/edit_projects.html', cv_data=cv_data)
    
    except Exception as e:
        logger.error(f"Error editing projects: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cv_data.view'))


@cv_data_bp.route('/edit/publications', methods=['GET', 'POST'])
def edit_publications():
    """Edit publications."""
    try:
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        if request.method == 'POST':
            # TODO: Implement publications editing
            flash('Publications editing not yet implemented', 'info')
            return redirect(url_for('cv_data.view'))
        
        return render_template('cv_data/edit_publications.html', cv_data=cv_data)
    
    except Exception as e:
        logger.error(f"Error editing publications: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cv_data.view'))


@cv_data_bp.route('/edit/awards', methods=['GET', 'POST'])
def edit_awards():
    """Edit awards."""
    try:
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        if request.method == 'POST':
            # TODO: Implement awards editing
            flash('Awards editing not yet implemented', 'info')
            return redirect(url_for('cv_data.view'))
        
        return render_template('cv_data/edit_awards.html', cv_data=cv_data)
    
    except Exception as e:
        logger.error(f"Error editing awards: {e}")
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
        return redirect(url_for('main.index'))


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
        return redirect(url_for('main.index'))


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
            'certifications': len(cv_data.certifications) if cv_data.certifications else 0,
            'volunteer': len(cv_data.volunteer) if cv_data.volunteer else 0,
            'projects': len(cv_data.projects) if cv_data.projects else 0,
            'publications': len(cv_data.publications) if cv_data.publications else 0,
            'awards': len(cv_data.awards) if cv_data.awards else 0,
        }
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
