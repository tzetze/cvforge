"""
CV Generation routes.

Handles job input, CV generation workflow, and PDF download.
"""

import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, session, jsonify
from pathlib import Path
from datetime import datetime
import yaml

from core.data_manager import load_cv_data
from core.job.parser import JobDescriptionParser, JobRequirements
from core.job.ai_parser import AIJobDescriptionParser
from core.job.scraper import LinkedInJobScraper
from core.scoring.achievement_scorer import AchievementScorer
from core.generation import CVContentSelector, CVTailoringEngine, PDFGenerator
from core.generation.cv_selector import SelectedContent
from core.llm.factory import LLMManager
from core.models import Experience, Achievement, ImpactLevel

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
            # Redirect to tailor-all instead of analyze
            return redirect(url_for('generate.tailor_all'))
        
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
                return redirect(url_for('generate.tailor_all'))
            
            except Exception as e:
                logger.error(f"Error scraping LinkedIn job: {e}")
                flash(f'Error scraping job: {str(e)}', 'danger')
                return redirect(url_for('generate.job_input'))
    
    # GET request - show the form
    return render_template('generate/job_input.html')
    

@generate_bp.route('/tailor-all')
def tailor_all():
    """Tailor all achievements upfront before scoring/selection."""
    try:
        # Get job description from session
        job_description = session.get('job_description')
        
        if not job_description:
            flash('No job description found. Please input a job first.', 'warning')
            return redirect(url_for('generate.job_input'))
        
        # Load CV data
        cv_data_path = current_app.config['CV_DATA_PATH']
        cv_data = load_cv_data(str(cv_data_path))
        
        # Parse job description with AI (with fallback to traditional parser)
        try:
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
            
        except Exception as e:
            # Fall back to traditional parser
            logger.warning(f"AI parser failed, falling back to traditional parser: {e}")
            parser = JobDescriptionParser()
            job_info = parser.parse({'description': job_description})
        
        # Store job info in session
        session['job_info'] = {
            'title': job_info.title,
            'company': job_info.company,
            'required_skills': job_info.required_skills,
            'preferred_skills': job_info.preferred_skills,
            'keywords': list(job_info.keywords) if job_info.keywords else []
        }
        
        # Load settings for tailoring config
        from core.data_manager import DataManager
        data_manager = DataManager()
        settings = data_manager.load_settings()
        
        # Initialize LLM for tailoring
        llm_manager = LLMManager(settings.model_dump())
        llm = llm_manager.get_provider()
        
        # Pass cv_generation config to tailoring engine
        cv_gen = settings.cv_generation
        tailor_config = {
            'max_achievement_words': cv_gen.get('max_achievement_words', 25),
            'rewrite_achievements': cv_gen.get('rewrite_achievements', True),
            'rewrite_summary': cv_gen.get('rewrite_summary', True),
            'max_summary_length': cv_gen.get('max_summary_length', 150)
        }
        
        # Tailor ALL achievements
        tailor = CVTailoringEngine(llm, config=tailor_config)
        tailored_cv_data = tailor.tailor_all_achievements(
            cv_data=cv_data,
            job_requirements=job_info,
            job_description=job_description
        )
        
        # Serialize tailored CV data to session
        # Convert CVData to dict for session storage
        tailored_cv_dict = tailored_cv_data.model_dump(mode='json')
        session['tailored_cv_data'] = tailored_cv_dict
        
        flash('All achievements tailored successfully', 'success')
        return redirect(url_for('generate.review_tailored'))
    
    except Exception as e:
        logger.error(f"Error tailoring achievements: {e}", exc_info=True)
        flash(f'Error tailoring CV: {str(e)}', 'danger')
        return redirect(url_for('generate.job_input'))


@generate_bp.route('/review-tailored')
def review_tailored():
    """Review tailored achievements before scoring/selection."""
    try:
        # Get tailored CV data from session
        tailored_cv_dict = session.get('tailored_cv_data')
        job_info_dict = session.get('job_info', {})
        
        if not tailored_cv_dict:
            flash('No tailored CV found. Please start the workflow again.', 'warning')
            return redirect(url_for('generate.job_input'))
        
        # Load original CV data for comparison
        cv_data_path = current_app.config['CV_DATA_PATH']
        from core.models import CVData
        original_cv_data = load_cv_data(str(cv_data_path))
        
        # Reconstruct tailored CV data from dict
        tailored_cv_data = CVData(**tailored_cv_dict)
        
        # Extract original summary from first achievement's keywords
        original_summary = original_cv_data.summary
        tailored_summary = tailored_cv_data.summary
        if tailored_cv_data.experience and tailored_cv_data.experience[0].achievements:
            first_ach = tailored_cv_data.experience[0].achievements[0]
            for keyword in (first_ach.keywords or []):
                if isinstance(keyword, str) and keyword.startswith("__original_summary__:"):
                    original_summary = keyword[len("__original_summary__:"):]
                    break
        
        summary_comparison = {
            'original': original_summary,
            'tailored': tailored_summary
        } if original_summary and tailored_summary else None
        
        # Prepare comparison data for template
        experiences_comparison = []
        for i, tailored_exp in enumerate(tailored_cv_data.experience):
            original_exp = original_cv_data.experience[i] if i < len(original_cv_data.experience) else None
            
            if original_exp:
                # Extract original description from first achievement's keywords
                original_description = original_exp.description
                tailored_description = tailored_exp.description
                if tailored_exp.achievements:
                    first_ach = tailored_exp.achievements[0]
                    for keyword in (first_ach.keywords or []):
                        if isinstance(keyword, str) and keyword.startswith("__original_description__:"):
                            original_description = keyword[len("__original_description__:"):]
                            break
                
                description_comparison = {
                    'original': original_description,
                    'tailored': tailored_description
                } if original_description and tailored_description else None
                
                achievements_comparison = []
                for j, tailored_ach in enumerate(tailored_exp.achievements):
                    original_ach = original_exp.achievements[j] if j < len(original_exp.achievements) else None
                    
                    # Extract original text from keywords metadata
                    original_text = None
                    if tailored_ach.keywords:
                        for keyword in tailored_ach.keywords:
                            if isinstance(keyword, str) and keyword.startswith("__original__:"):
                                original_text = keyword[len("__original__:"):]
                                break
                    
                    # Fallback to original achievement if metadata not found
                    if not original_text and original_ach:
                        original_text = original_ach.text
                    
                    achievements_comparison.append({
                        'original': original_text or tailored_ach.text,
                        'tailored': tailored_ach.text,
                        'skills': tailored_ach.skills
                    })
                
                experiences_comparison.append({
                    'company': tailored_exp.company,
                    'position': tailored_exp.position,
                    'description': description_comparison,
                    'achievements': achievements_comparison
                })
        
        return render_template(
            'generate/review_tailored.html',
            summary=summary_comparison,
            experiences=experiences_comparison,
            job_title=job_info_dict.get('title') or session.get('job_title'),
            job_company=job_info_dict.get('company') or session.get('job_company'),
            job_info=job_info_dict
        )
    
    except Exception as e:
        logger.error(f"Error reviewing tailored content: {e}", exc_info=True)

@generate_bp.route('/reroll-achievement', methods=['POST'])
def reroll_achievement():
    """Re-tailor a single achievement via AJAX."""
    try:
        data = request.get_json()
        exp_index = data.get('exp_index')
        ach_index = data.get('ach_index')
        
        if exp_index is None or ach_index is None:
            return jsonify({'success': False, 'error': 'Missing indices'}), 400
        
        # Get tailored CV data and job info from session
        tailored_cv_dict = session.get('tailored_cv_data')
        job_info_dict = session.get('job_info', {})
        job_description = session.get('job_description')
        
        if not tailored_cv_dict or not job_description:
            return jsonify({'success': False, 'error': 'Session data missing'}), 400
        
        # Reconstruct CVData and JobRequirements
        from core.models import CVData
        tailored_cv_data = CVData(**tailored_cv_dict)
        
        from core.job.parser import JobRequirements
        job_requirements = JobRequirements(
            title=job_info_dict.get('title', 'Position'),
            company=job_info_dict.get('company'),
            required_skills=job_info_dict.get('required_skills', []),
            preferred_skills=job_info_dict.get('preferred_skills', []),
            keywords=set(job_info_dict.get('keywords', []))
        )
        
        # Get the experience
        if exp_index >= len(tailored_cv_data.experience):
            return jsonify({'success': False, 'error': 'Experience index out of range'}), 400
        
        experience = tailored_cv_data.experience[exp_index]
        
        if ach_index >= len(experience.achievements):
            return jsonify({'success': False, 'error': 'Achievement index out of range'}), 400
        
        # Load settings and initialize LLM
        from core.data_manager import DataManager
        data_manager = DataManager()
        settings = data_manager.load_settings()
        
        llm_manager = LLMManager(settings.model_dump())
        llm = llm_manager.get_provider()
        
        # Initialize tailoring engine
        cv_gen = settings.cv_generation
        tailor_config = {
            'max_achievement_words': cv_gen.get('max_achievement_words', 25),
            'rewrite_achievements': cv_gen.get('rewrite_achievements', True),
        }
        
        from core.generation.cv_tailor import CVTailoringEngine
        tailor = CVTailoringEngine(llm, config=tailor_config)
        
        # Convert achievements to dicts for the method
        achievements_dicts = [ach.model_dump() for ach in experience.achievements]
        
        # Re-tailor the single achievement
        new_text = tailor.retailor_single_achievement(
            experience_achievements=achievements_dicts,
            achievement_index=ach_index,
            job_requirements=job_requirements,
            job_description=job_description
        )
        
        # Update the achievement in the CV data
        experience.achievements[ach_index].text = new_text
        
        # Update session with modified CV data
        tailored_cv_dict = tailored_cv_data.model_dump(mode='json')
        session['tailored_cv_data'] = tailored_cv_dict
        session.modified = True
        
        logger.info(f"Re-rolled achievement {ach_index} in experience {exp_index}")
        
        return jsonify({
            'success': True,
            'new_text': new_text
        })
        
    except Exception as e:
        logger.error(f"Error re-rolling achievement: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@generate_bp.route('/reroll-summary', methods=['POST'])
def reroll_summary():
    """Re-tailor the professional summary via AJAX."""
    try:
        # Get tailored CV data and job info from session
        tailored_cv_dict = session.get('tailored_cv_data')
        job_info_dict = session.get('job_info', {})
        job_description = session.get('job_description')
        
        if not tailored_cv_dict or not job_description:
            return jsonify({'success': False, 'error': 'Session data missing'}), 400
        
        # Reconstruct CVData and JobRequirements
        from core.models import CVData
        tailored_cv_data = CVData(**tailored_cv_dict)
        
        from core.job.parser import JobRequirements
        job_requirements = JobRequirements(
            title=job_info_dict.get('title', 'Position'),
            company=job_info_dict.get('company'),
            required_skills=job_info_dict.get('required_skills', []),
            preferred_skills=job_info_dict.get('preferred_skills', []),
            keywords=set(job_info_dict.get('keywords', []))
        )
        
        # Get original summary from first achievement's keywords
        original_summary = tailored_cv_data.summary
        if tailored_cv_data.experience and tailored_cv_data.experience[0].achievements:
            first_ach = tailored_cv_data.experience[0].achievements[0]
            for keyword in (first_ach.keywords or []):
                if isinstance(keyword, str) and keyword.startswith("__original_summary__:"):
                    original_summary = keyword[len("__original_summary__:"):]
                    break
        
        # Load settings and initialize LLM
        from core.data_manager import DataManager
        data_manager = DataManager()
        settings = data_manager.load_settings()
        
        llm_manager = LLMManager(settings.model_dump())
        llm = llm_manager.get_provider()
        
        # Initialize tailoring engine
        cv_gen = settings.cv_generation
        tailor_config = {
            'max_summary_length': cv_gen.get('max_summary_length', 150),
            'rewrite_summary': cv_gen.get('rewrite_summary', True),
        }
        
        from core.generation.cv_tailor import CVTailoringEngine
        tailor = CVTailoringEngine(llm, config=tailor_config)
        
        # Re-tailor the summary
        new_summary = tailor.retailor_summary(
            original_summary=original_summary,
            job_requirements=job_requirements,
            job_description=job_description
        )
        
        # Update the summary in CV data
        tailored_cv_data.summary = new_summary
        
        # Update session with modified CV data
        tailored_cv_dict = tailored_cv_data.model_dump(mode='json')
        session['tailored_cv_data'] = tailored_cv_dict
        session.modified = True
        
        logger.info("Re-rolled professional summary")
        
        return jsonify({
            'success': True,
            'new_text': new_summary
        })
        
    except Exception as e:
        logger.error(f"Error re-rolling summary: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@generate_bp.route('/reroll-description', methods=['POST'])
def reroll_description():
    """Re-tailor an experience description via AJAX."""
    try:
        data = request.get_json()
        exp_index = data.get('exp_index')
        
        if exp_index is None:
            return jsonify({'success': False, 'error': 'Missing experience index'}), 400
        
        # Get tailored CV data and job info from session
        tailored_cv_dict = session.get('tailored_cv_data')
        job_info_dict = session.get('job_info', {})
        job_description = session.get('job_description')
        
        if not tailored_cv_dict or not job_description:
            return jsonify({'success': False, 'error': 'Session data missing'}), 400
        
        # Reconstruct CVData and JobRequirements
        from core.models import CVData
        tailored_cv_data = CVData(**tailored_cv_dict)
        
        from core.job.parser import JobRequirements
        job_requirements = JobRequirements(
            title=job_info_dict.get('title', 'Position'),
            company=job_info_dict.get('company'),
            required_skills=job_info_dict.get('required_skills', []),
            preferred_skills=job_info_dict.get('preferred_skills', []),
            keywords=set(job_info_dict.get('keywords', []))
        )
        
        # Get the experience
        if exp_index >= len(tailored_cv_data.experience):
            return jsonify({'success': False, 'error': 'Experience index out of range'}), 400
        
        experience = tailored_cv_data.experience[exp_index]
        
        # Get original description from first achievement's keywords
        original_description = experience.description
        if experience.achievements:
            first_ach = experience.achievements[0]
            for keyword in (first_ach.keywords or []):
                if isinstance(keyword, str) and keyword.startswith("__original_description__:"):
                    original_description = keyword[len("__original_description__:"):]
                    break
        
        # Load settings and initialize LLM
        from core.data_manager import DataManager
        data_manager = DataManager()
        settings = data_manager.load_settings()
        
        llm_manager = LLMManager(settings.model_dump())
        llm = llm_manager.get_provider()
        
        # Initialize tailoring engine
        cv_gen = settings.cv_generation
        tailor_config = {
            'rewrite_achievements': cv_gen.get('rewrite_achievements', True),
        }
        
        from core.generation.cv_tailor import CVTailoringEngine
        tailor = CVTailoringEngine(llm, config=tailor_config)
        
        # Re-tailor the description
        new_description = tailor.retailor_experience_description(
            original_description=original_description,
            position=experience.position,
            company=experience.company,
            job_requirements=job_requirements,
            job_description=job_description
        )
        
        # Update the description in the experience
        experience.description = new_description
        
        # Update session with modified CV data
        tailored_cv_dict = tailored_cv_data.model_dump(mode='json')
        session['tailored_cv_data'] = tailored_cv_dict
        session.modified = True
        
        logger.info(f"Re-rolled description for experience {exp_index}")
        
        return jsonify({
            'success': True,
            'new_text': new_description
        })
        
    except Exception as e:
        logger.error(f"Error re-rolling description: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@generate_bp.route('/analyze')
def analyze():
    """Analyze job requirements and show match score (using TAILORED CV data)."""
    try:
        # Get tailored CV data from session
        tailored_cv_dict = session.get('tailored_cv_data')
        job_info_dict = session.get('job_info', {})
        
        if not tailored_cv_dict:
            flash('No tailored CV found. Please start the workflow again.', 'warning')
            return redirect(url_for('generate.job_input'))
        
        # Load original CV data for personal info
        cv_data_path = current_app.config['CV_DATA_PATH']
        original_cv_data = load_cv_data(str(cv_data_path))
        
        # Reconstruct tailored CV data from session
        from core.models import CVData
        tailored_cv_data = CVData(**tailored_cv_dict)
        
        # Reconstruct job_info from session
        job_info = JobRequirements(
            title=job_info_dict.get('title'),
            company=job_info_dict.get('company'),
            required_skills=job_info_dict.get('required_skills', []),
            preferred_skills=job_info_dict.get('preferred_skills', []),
            keywords=set(job_info_dict.get('keywords', []))
        )
        
        # Load settings to get configuration
        from core.data_manager import DataManager
        data_manager = DataManager()
        settings = data_manager.load_settings()
        
        # Build selector config from settings
        cv_gen = settings.cv_generation
        selector_config = {
            'max_achievements_per_job': cv_gen.get('max_achievements_per_job', 5),
            'min_achievement_score': cv_gen.get('min_achievement_score', 0.3),
            'include_volunteer': cv_gen.get('include_volunteer', True),
            'include_projects': cv_gen.get('include_projects', True),
            'include_publications': cv_gen.get('include_publications', True),
            'include_awards': cv_gen.get('include_awards', True),
            'max_pages': cv_gen.get('max_pages', 2)
        }
        
        # Score achievements with settings-based weights
        scorer_weights = {
            'llm_relevance': settings.scoring.llm_relevance,
            'impact_level': settings.scoring.impact_level,
            'recency': settings.scoring.recency
        }
        scorer = AchievementScorer(weights=scorer_weights)
        selector = CVContentSelector(scorer, config=selector_config)
        
        # Initialize LLM for scoring
        llm_manager = LLMManager(settings.model_dump())
        llm = llm_manager.get_provider()
        
        # Get job description from session
        job_description = session.get('job_description', '')
        
        # Score and select from TAILORED CV data (not original)
        logger.info("Scoring tailored achievements with LLM")
        selected_content = selector.select_content(
            cv_data=tailored_cv_data,  # Use tailored version
            job_requirements=job_info,
            job_description=job_description,
            llm=llm,
            verbose=True
        )
        
        # Store selected content in session (already in dict format from selector)
        session['selected_experiences'] = selected_content.experiences
        session['selected_summary'] = selected_content.summary
        session['selected_skills'] = selected_content.skills
        session['selected_education'] = selected_content.education
        session['selected_certifications'] = selected_content.certifications
        session['selected_projects'] = selected_content.projects
        
        # Calculate overall CV match using LLM (includes summary, descriptions, achievements)
        logger.info("Calculating overall CV match with LLM")
        overall_match_score = selector.calculate_overall_cv_match(
            cv_data=tailored_cv_data,
            job_requirements=job_info,
            job_description=job_description,
            llm=llm
        )
        overall_match = overall_match_score * 100  # Convert to percentage
        
        # Store match data
        match_summary = selected_content.job_match_summary
        if match_summary:
            match_summary['overall_cv_match'] = overall_match_score
        
        session['match_score'] = overall_match
        session['job_match_summary'] = match_summary
        
        # Prepare data for PDF download (store in session)
        summary = selected_content.summary or tailored_cv_data.summary
        experiences = selected_content.experiences
        
        session['tailored_summary'] = summary
        session['tailored_experiences'] = experiences
        
        return render_template(
            'generate/analyze.html',
            job_info=job_info,
            selected_content=selected_content,
            cv_data=tailored_cv_data  # Pass tailored CV data to template
        )
    
    except Exception as e:
        logger.error(f"Error analyzing job: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('generate.job_input'))


# OLD TAILOR ROUTE - DEPRECATED IN TAILOR-FIRST WORKFLOW
# Tailoring now happens upfront in /generate/tailor-all
@generate_bp.route('/tailor', methods=['GET', 'POST'])
def tailor():
    """Tailor CV content with LLM (optional step) - DEPRECATED in tailor-first workflow."""
    flash('Tailoring now happens automatically. Proceeding to download.', 'info')
    return redirect(url_for('generate.download'))


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
        
        # Load settings to get configuration
        from core.data_manager import DataManager
        data_manager = DataManager()
        settings = data_manager.load_settings()
        
        # Build selector config from settings
        cv_gen = settings.cv_generation
        selector_config = {
            'max_achievements_per_job': cv_gen.get('max_achievements_per_job', 5),
            'min_achievement_score': cv_gen.get('min_achievement_score', 0.3),
            'include_volunteer': cv_gen.get('include_volunteer', True),
            'include_projects': cv_gen.get('include_projects', True),
            'include_publications': cv_gen.get('include_publications', True),
            'include_awards': cv_gen.get('include_awards', True),
            'max_pages': cv_gen.get('max_pages', 2)
        }
        
        # Score achievements with settings-based weights
        scorer_weights = {
            'llm_relevance': settings.scoring.llm_relevance,
            'impact_level': settings.scoring.impact_level,
            'recency': settings.scoring.recency
        }
        scorer = AchievementScorer(weights=scorer_weights)
        selector = CVContentSelector(scorer, config=selector_config)
        
        # Initialize LLM for scoring
        llm_manager = LLMManager(settings.model_dump())
        llm = llm_manager.get_provider()
        
        # Get job description from session
        job_description = session.get('job_description', '')
        
        selected_content = selector.select_content(
            cv_data=cv_data,
            job_requirements=job_info,
            job_description=job_description,
            llm=llm
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
            volunteer=cv_data.volunteer,
            publications=cv_data.publications,
            awards=cv_data.awards,
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

