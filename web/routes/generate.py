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
from core.job.ai_parser import AIJobDescriptionParser
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
            logger.info(f"Stored job description in session (length: {len(job_description)})")
            logger.info(f"Session data: {dict(session)}")
            
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
        logger.info(f"Analyze route - Session keys: {list(session.keys())}")
        logger.info(f"Analyze route - Full session: {dict(session)}")
        job_description = session.get('job_description')
        logger.info(f"Retrieved job_description: {job_description[:100] if job_description else 'None'}...")
        
        if not job_description:
            flash('No job description found. Please input a job first.', 'warning')
            return redirect(url_for('generate.job_input'))
        
        # Load CV data
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        # Parse job description with AI (with fallback to traditional parser)
        try:
            # Try to use AI parser if LLM is configured
            from core.data_manager import DataManager
            data_manager = DataManager()
            settings = data_manager.load_settings()
            settings_dict = settings.model_dump()
            
            llm_manager = LLMManager(settings_dict)
            llm_provider = llm_manager.get_default_provider()
            
            # Use AI parser
            logger.info("Using AI-powered job parser")
            ai_parser = AIJobDescriptionParser(llm_provider)
            job_info = ai_parser.parse({
                'description': job_description,
                'title': session.get('job_title'),
                'company': session.get('job_company')
            })
            session['parser_type'] = 'ai'
            
        except Exception as e:
            # Fall back to traditional parser
            logger.warning(f"AI parser failed, falling back to traditional parser: {e}")
            parser = JobDescriptionParser()
            job_info = parser.parse({'description': job_description})
            session['parser_type'] = 'traditional'
        
        # Score achievements
        scorer = AchievementScorer()
        selector = CVContentSelector(scorer)
        
        selected_content = selector.select_content(
            cv_data=cv_data,
            job_requirements=job_info
        )
        
        # Store in session
        session['job_info'] = {
            'required_skills': job_info.required_skills,
            'preferred_skills': job_info.preferred_skills,
            'keywords': job_info.keywords
        }
        # Calculate overall match from skill_match_rate and average_score
        match_summary = selected_content.job_match_summary
        if match_summary:
            skill_match = match_summary.get('skill_match_rate', 0)
            avg_score = match_summary.get('average_score', 0)
            overall_match = (skill_match * 0.6 + avg_score * 0.4) * 100  # Weighted average as percentage
        else:
            overall_match = 0
        session['match_score'] = overall_match
        
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
            from core.data_manager import DataManager
            data_manager = DataManager()
            settings = data_manager.load_settings()
            settings_dict = settings.model_dump()
            # Check if llm.providers exists and has at least one provider configured
            llm_config = settings_dict.get('llm', {})
            providers = llm_config.get('providers', {})
            llm_configured = bool(providers)
            logger.info(f"LLM configuration check: {len(providers)} providers found")
        except Exception as e:
            logger.error(f"Error checking LLM configuration: {e}")
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
            job_requirements=job_info
        )
        
        # Tailor if requested
        if use_tailoring:
            try:
                from core.data_manager import DataManager
                data_manager = DataManager()
                settings = data_manager.load_settings()
                
                llm_manager = LLMManager(settings.model_dump())
                llm = llm_manager.get_provider()  # Uses default provider from settings
                
                tailor = CVTailoringEngine(llm)
                tailored_cv = tailor.tailor_cv(
                    selected_content=selected_content,
                    job_requirements=job_info
                )
                
                summary = tailored_cv.summary
                experiences = tailored_cv.experiences
                
                # Store tailored content in session for PDF download
                session['tailored_summary'] = summary
                session['tailored_experiences'] = experiences
                
                flash('CV content tailored with LLM', 'success')
            
            except Exception as e:
                logger.error(f"Error tailoring CV: {e}")
                flash(f'LLM tailoring failed, using selected content: {str(e)}', 'warning')
                summary = cv_data.summary
                experiences = selected_content.experiences
                
                # Store non-tailored content in session
                session['tailored_summary'] = summary
                session['tailored_experiences'] = experiences
        else:
            summary = cv_data.summary
            experiences = selected_content.experiences
            
            # Store non-tailored content in session
            session['tailored_summary'] = summary
            session['tailored_experiences'] = experiences
        
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
            job_requirements=job_info
        )
        
        # Use already-tailored content from session (set during preview)
        summary = session.get('tailored_summary')
        experiences = session.get('tailored_experiences')
        
        # Fallback if session data is missing
        if not summary or not experiences:
            logger.warning("Tailored content not found in session, regenerating...")
            flash('Session data missing, regenerating content...', 'warning')
            
            if use_tailoring:
                try:
                    from core.data_manager import DataManager
                    data_manager = DataManager()
                    settings = data_manager.load_settings()
                    
                    llm_manager = LLMManager(settings.model_dump())
                    llm = llm_manager.get_provider()
                    
                    tailor = CVTailoringEngine(llm)
                    tailored_cv = tailor.tailor_cv(
                        selected_content=selected_content,
                        job_requirements=job_info
                    )
                    
                    summary = tailored_cv.summary
                    experiences = tailored_cv.experiences
                except Exception as e:
                    logger.error(f"Error tailoring CV: {e}")
                    summary = cv_data.summary
                    experiences = selected_content.experiences
            else:
                summary = cv_data.summary
                experiences = selected_content.experiences
        
        # Generate PDF
        generator = PDFGenerator()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_slug = cv_data.personal.name.lower().replace(" ", "_")
        
        # Use absolute path from project root
        from pathlib import Path
        project_root = Path(current_app.root_path).parent
        output_dir = project_root / 'output'
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{name_slug}_cv_{timestamp}.pdf"
        
        logger.info(f"Generating PDF to: {output_path}")
        
        generator.generate_pdf_from_selected_content(
            personal_info=cv_data.personal.model_dump(),
            summary=summary,
            experiences=experiences,
            skills=cv_data.skills.model_dump() if cv_data.skills else None,
            education=cv_data.education,
            certifications=cv_data.certifications,
            projects=cv_data.projects,
            output_path=output_path
        )
        
        if not output_path.exists():
            raise FileNotFoundError(f"PDF was not created at {output_path}")
        
        logger.info(f"PDF successfully created at: {output_path}")
        
        return send_file(
            str(output_path),
            as_attachment=True,
            download_name=f"{name_slug}_cv.pdf",
            mimetype='application/pdf'
        )
    
    except Exception as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        flash(f'Error generating PDF: {str(e)}', 'danger')
        # Don't redirect to preview (which would re-tailor), stay on current page
        return redirect(url_for('generate.job_input'))

