"""
CV Generation routes.

Handles job input, CV generation workflow, and PDF download.
"""

import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, session
from pathlib import Path
from datetime import datetime
import yaml

from core.data_manager import load_cv_data
from core.job.parser import JobDescriptionParser
from core.job.scraper import LinkedInJobScraper
from core.scoring.achievement_scorer import AchievementScorer
from core.generation import CVContentSelector, CVTailoringEngine, PDFGenerator
from core.llm.factory import LLMManager

logger = logging.getLogger(__name__)

generate_bp = Blueprint('generate', __name__)


@generate_bp.route('/')
def index():
    """CV generation workflow start page."""
    return render_template('generate/index.html')


@generate_bp.route('/job-input', methods=['GET', 'POST'])
def job_input():
    """Input job description (manual or LinkedIn URL)."""
    if request.method == 'POST':
        input_type = request.form.get('input_type', 'manual')
        
        if input_type == 'manual':
            job_description = request.form.get('job_description', '')
            
            if not job_description.strip():
                flash('Please enter a job description', 'warning')
                return redirect(url_for('generate.job_input'))
            
            # Store in session
            session['job_description'] = job_description
            session['job_source'] = 'manual'
            
            flash('Job description saved', 'success')
            return redirect(url_for('generate.analyze'))
        
        elif input_type == 'linkedin':
            linkedin_url = request.form.get('linkedin_url', '')
            
            if not linkedin_url.strip():
                flash('Please enter a LinkedIn job URL', 'warning')
                return redirect(url_for('generate.job_input'))
            
            try:
                # Scrape job
                scraper = LinkedInJobScraper()
                job_data = scraper.scrape_job(linkedin_url)
                
                # Store in session
                session['job_description'] = job_data.get('description', '')
                session['job_title'] = job_data.get('title', '')
                session['job_company'] = job_data.get('company', '')
                session['job_source'] = 'linkedin'
                session['job_url'] = linkedin_url
                
                flash('Job scraped successfully from LinkedIn', 'success')
                return redirect(url_for('generate.analyze'))
            
            except Exception as e:
                logger.error(f"Error scraping LinkedIn job: {e}")
                flash(f'Error scraping job: {str(e)}', 'danger')
                return redirect(url_for('generate.job_input'))
    
    return render_template('generate/job_input.html')


@generate_bp.route('/analyze')
def analyze():
    """Analyze job requirements and show match score."""
    try:
        # Get job description from session
        job_description = session.get('job_description')
        
        if not job_description:
            flash('No job description found. Please input a job first.', 'warning')
            return redirect(url_for('generate.job_input'))
        
        # Load CV data
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        # Parse job description
        parser = JobDescriptionParser()
        job_info = parser.parse({'description': job_description})
        
        # Score achievements
        scorer = AchievementScorer()
        selector = CVContentSelector(scorer)
        
        selected_content = selector.select_content(
            cv_data=cv_data,
            job_requirements=job_info.required_skills,
            top_n=15
        )
        
        # Store in session
        session['job_info'] = {
            'required_skills': job_info.required_skills,
            'preferred_skills': job_info.preferred_skills,
            'keywords': job_info.keywords
        }
        session['match_score'] = selected_content.match_summary.get('overall_match', 0)
        
        return render_template(
            'generate/analyze.html',
            job_info=job_info,
            selected_content=selected_content,
            cv_data=cv_data
        )
    
    except Exception as e:
        logger.error(f"Error analyzing job: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('generate.job_input'))


@generate_bp.route('/tailor', methods=['GET', 'POST'])
def tailor():
    """Tailor CV content with LLM (optional step)."""
    try:
        if request.method == 'POST':
            use_tailoring = request.form.get('use_tailoring') == 'yes'
            session['use_tailoring'] = use_tailoring
            
            if use_tailoring:
                flash('CV will be tailored with LLM', 'info')
            else:
                flash('CV will use selected content without LLM tailoring', 'info')
            
            return redirect(url_for('generate.preview'))
        
        # Check if LLM is configured
        try:
            settings_path = current_app.config['SETTINGS_PATH']
            with open(settings_path) as f:
                settings = yaml.safe_load(f)
            llm_configured = bool(settings.get('llm_providers'))
        except:
            llm_configured = False
        
        return render_template(
            'generate/tailor.html',
            llm_configured=llm_configured
        )
    
    except Exception as e:
        logger.error(f"Error in tailor step: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('generate.analyze'))


@generate_bp.route('/preview')
def preview():
    """Preview generated CV before downloading."""
    try:
        # Load CV data
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        # Get job info from session
        job_description = session.get('job_description')
        job_info_dict = session.get('job_info', {})
        use_tailoring = session.get('use_tailoring', False)
        
        if not job_description:
            flash('Session expired. Please start over.', 'warning')
            return redirect(url_for('generate.job_input'))
        
        # Parse and select content
        parser = JobDescriptionParser()
        job_info = parser.parse({'description': job_description})
        
        scorer = AchievementScorer()
        selector = CVContentSelector(scorer)
        
        selected_content = selector.select_content(
            cv_data=cv_data,
            job_requirements=job_info.required_skills,
            top_n=15
        )
        
        # Tailor if requested
        if use_tailoring:
            try:
                settings_path = current_app.config['SETTINGS_PATH']
                with open(settings_path) as f:
                    settings = yaml.safe_load(f)
                
                llm_manager = LLMManager(settings)
                llm = llm_manager.get_provider("default")
                
                tailor = CVTailoringEngine(llm)
                tailored_cv = tailor.tailor_cv(
                    selected_content=selected_content,
                    job_requirements=job_info.required_skills
                )
                
                summary = tailored_cv.summary
                experiences = tailored_cv.experiences
                flash('CV content tailored with LLM', 'success')
            
            except Exception as e:
                logger.error(f"Error tailoring CV: {e}")
                flash(f'LLM tailoring failed, using selected content: {str(e)}', 'warning')
                summary = cv_data.summary
                experiences = selected_content.experiences
        else:
            summary = cv_data.summary
            experiences = selected_content.experiences
        
        return render_template(
            'generate/preview.html',
            cv_data=cv_data,
            summary=summary,
            experiences=experiences,
            match_score=session.get('match_score', 0)
        )
    
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('generate.job_input'))


@generate_bp.route('/download')
def download():
    """Generate and download PDF."""
    try:
        # Load CV data
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        # Get session data
        job_description = session.get('job_description')
        use_tailoring = session.get('use_tailoring', False)
        
        if not job_description:
            flash('Session expired. Please start over.', 'warning')
            return redirect(url_for('generate.job_input'))
        
        # Parse and select content
        parser = JobDescriptionParser()
        job_info = parser.parse({'description': job_description})
        
        scorer = AchievementScorer()
        selector = CVContentSelector(scorer)
        
        selected_content = selector.select_content(
            cv_data=cv_data,
            job_requirements=job_info.required_skills,
            top_n=15
        )
        
        # Tailor if requested
        if use_tailoring:
            try:
                settings_path = current_app.config['SETTINGS_PATH']
                with open(settings_path) as f:
                    settings = yaml.safe_load(f)
                
                llm_manager = LLMManager(settings)
                llm = llm_manager.get_provider("default")
                
                tailor = CVTailoringEngine(llm)
                tailored_cv = tailor.tailor_cv(
                    selected_content=selected_content,
                    job_requirements=job_info.required_skills
                )
                
                summary = tailored_cv.summary
                experiences = tailored_cv.experiences
            except:
                summary = cv_data.summary
                experiences = selected_content.experiences
        else:
            summary = cv_data.summary
            experiences = selected_content.experiences
        
        # Generate PDF
        generator = PDFGenerator()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_slug = cv_data.personal_info.name.lower().replace(" ", "_")
        output_path = current_app.config['OUTPUT_FOLDER'] / f"{name_slug}_cv_{timestamp}.pdf"
        
        generator.generate_pdf_from_selected_content(
            personal_info=cv_data.personal_info.model_dump(),
            summary=summary,
            experiences=experiences,
            skills=cv_data.skills.model_dump() if cv_data.skills else None,
            education=cv_data.education,
            certifications=cv_data.certifications,
            projects=cv_data.projects,
            output_path=output_path
        )
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"{name_slug}_cv.pdf",
            mimetype='application/pdf'
        )
    
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        flash(f'Error generating PDF: {str(e)}', 'danger')
        return redirect(url_for('generate.preview'))

# Made with Bob
