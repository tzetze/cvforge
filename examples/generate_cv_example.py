"""
Example: Complete CV Generation Pipeline

Demonstrates the full workflow:
1. Load CV data from YAML
2. Scrape job description from LinkedIn
3. Score and select relevant content
4. Tailor content with LLM
5. Generate PDF CV

Usage:
    python examples/generate_cv_example.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.data_manager import CVDataManager
from core.job.scraper import LinkedInJobScraper
from core.job.parser import JobDescriptionParser
from core.scoring.achievement_scorer import AchievementScorer
from core.generation.cv_selector import CVContentSelector
from core.generation.cv_tailor import CVTailoringEngine
from core.generation.pdf_generator import PDFGenerator
from core.llm.factory import LLMManager


def main():
    """Run complete CV generation pipeline."""
    
    print("=" * 60)
    print("CVForge - Intelligent CV Generation Pipeline")
    print("=" * 60)
    
    # Step 1: Load CV data
    print("\n[1/6] Loading CV data...")
    data_manager = CVDataManager()
    cv_data = data_manager.load_cv_data("config/cv_data.yaml")
    print(f"✓ Loaded CV for {cv_data.personal_info.name}")
    print(f"  - {len(cv_data.experiences)} experiences")
    print(f"  - {sum(len(exp.achievements) for exp in cv_data.experiences)} total achievements")
    
    # Step 2: Get job description
    print("\n[2/6] Getting job description...")
    
    # Option A: Scrape from LinkedIn (requires manual login)
    # job_url = "https://www.linkedin.com/jobs/view/1234567890"
    # scraper = LinkedInJobScraper()
    # job_data = scraper.scrape_job(job_url)
    
    # Option B: Use example job description
    job_description = """
    Senior Software Engineer - Python & Cloud Infrastructure
    
    We're looking for an experienced software engineer to join our platform team.
    
    Requirements:
    - 5+ years of Python development experience
    - Strong experience with AWS, Docker, and Kubernetes
    - Experience with microservices architecture
    - CI/CD pipeline development (Jenkins, GitLab CI)
    - Database design and optimization (PostgreSQL, Redis)
    - RESTful API design and development
    - Strong problem-solving and debugging skills
    - Experience with agile methodologies
    
    Nice to have:
    - Experience with FastAPI or Flask
    - Infrastructure as Code (Terraform, CloudFormation)
    - Monitoring and observability tools (Prometheus, Grafana)
    - Team leadership experience
    
    Responsibilities:
    - Design and implement scalable backend services
    - Optimize system performance and reliability
    - Mentor junior engineers
    - Collaborate with cross-functional teams
    """
    
    print("✓ Using example job description")
    print(f"  Job: Senior Software Engineer - Python & Cloud")
    
    # Step 3: Parse job requirements
    print("\n[3/6] Parsing job requirements...")
    parser = JobDescriptionParser()
    job_info = parser.parse(job_description)
    print(f"✓ Extracted {len(job_info.required_skills)} required skills")
    print(f"  Top skills: {', '.join(job_info.required_skills[:5])}")
    
    # Step 4: Score and select content
    print("\n[4/6] Scoring and selecting relevant content...")
    scorer = AchievementScorer()
    selector = CVContentSelector(scorer)
    
    selected_content = selector.select_content(
        cv_data=cv_data,
        job_info=job_info,
        max_achievements_per_role=4,
        min_score_threshold=0.3
    )
    
    print(f"✓ Selected content:")
    print(f"  - {len(selected_content.experiences)} experiences")
    print(f"  - {sum(len(exp.achievements) for exp in selected_content.experiences)} achievements")
    print(f"  - Match score: {selected_content.match_summary['overall_match']:.1%}")
    
    # Step 5: Tailor content with LLM
    print("\n[5/6] Tailoring content with LLM...")
    print("  (This step requires LLM configuration)")
    
    try:
        llm_manager = LLMManager()
        llm = llm_manager.get_provider("default")
        
        tailor = CVTailoringEngine(llm)
        tailored_cv = tailor.tailor_cv(
            selected_content=selected_content,
            job_info=job_info,
            cv_data=cv_data
        )
        
        print("✓ Content tailored successfully")
        print(f"  - Summary: {len(tailored_cv.summary)} characters")
        print(f"  - {len(tailored_cv.experiences)} experiences tailored")
        
        use_tailored = True
        
    except Exception as e:
        print(f"⚠ LLM tailoring skipped: {e}")
        print("  Using selected content without tailoring")
        use_tailored = False
    
    # Step 6: Generate PDF
    print("\n[6/6] Generating PDF...")
    generator = PDFGenerator()
    
    output_path = Path("output") / f"{cv_data.personal_info.name.lower().replace(' ', '_')}_cv.pdf"
    output_path.parent.mkdir(exist_ok=True)
    
    if use_tailored:
        # Use tailored content
        pdf_path = generator.generate_pdf_from_selected_content(
            personal_info=cv_data.personal_info.model_dump(),
            summary=tailored_cv.summary,
            experiences=tailored_cv.experiences,
            skills=cv_data.skills.model_dump() if cv_data.skills else None,
            education=cv_data.education,
            certifications=cv_data.certifications,
            projects=cv_data.projects,
            output_path=output_path
        )
    else:
        # Use selected content without tailoring
        pdf_path = generator.generate_pdf_from_selected_content(
            personal_info=cv_data.personal_info.model_dump(),
            summary=cv_data.summary,
            experiences=selected_content.experiences,
            skills=cv_data.skills.model_dump() if cv_data.skills else None,
            education=cv_data.education,
            certifications=cv_data.certifications,
            projects=cv_data.projects,
            output_path=output_path
        )
    
    print(f"✓ PDF generated: {pdf_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("✓ CV Generation Complete!")
    print("=" * 60)
    print(f"\nOutput: {pdf_path.absolute()}")
    print(f"Template: modern.html")
    print(f"Match Score: {selected_content.match_summary['overall_match']:.1%}")
    print("\nNext steps:")
    print("  1. Review the generated PDF")
    print("  2. Adjust cv_data.yaml if needed")
    print("  3. Configure LLM for content tailoring")
    print("  4. Try with real LinkedIn job URLs")


if __name__ == "__main__":
    main()
