"""
CV content selector for filtering relevant achievements.

This module selects the most relevant content from a CV based on job requirements,
using the achievement scoring system to rank and filter achievements.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from core.models import CVData, Experience, Achievement
from core.job.parser import JobRequirements
from core.scoring.achievement_scorer import AchievementScorer, ScoredAchievement


@dataclass
class SelectedContent:
    """Selected CV content for a specific job."""
    
    # Basic info (always included)
    personal_info: Dict[str, Any]
    summary: Optional[str]
    
    # Selected experiences with filtered achievements
    experiences: List[Dict[str, Any]]
    
    # Skills (filtered to relevant ones)
    skills: Dict[str, Any]
    
    # Optional sections (included if relevant)
    education: Optional[List[Dict[str, Any]]]
    certifications: Optional[List[Dict[str, Any]]]
    volunteer: Optional[List[Dict[str, Any]]]
    projects: Optional[List[Dict[str, Any]]]
    publications: Optional[List[Dict[str, Any]]]
    awards: Optional[List[Dict[str, Any]]]
    
    # Metadata
    total_achievements_selected: int
    average_relevance_score: float
    job_match_summary: Dict[str, Any]


class CVContentSelector:
    """
    Selects relevant CV content based on job requirements.
    
    Uses the achievement scoring system to intelligently filter and select
    the most relevant achievements, skills, and experiences for a specific job.
    """
    
    def __init__(
        self,
        scorer: Optional[AchievementScorer] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the content selector.
        
        Args:
            scorer: Optional AchievementScorer instance (creates default if not provided)
            config: Optional configuration dict
        """
        self.scorer = scorer or AchievementScorer()
        self.config = config or {}
        
        # Configuration options
        self.max_achievements_per_job = self.config.get("max_achievements_per_job", 5)
        self.min_achievement_score = self.config.get("min_achievement_score", 0.3)
        self.include_volunteer = self.config.get("include_volunteer", True)
        self.include_projects = self.config.get("include_projects", True)
        self.include_publications = self.config.get("include_publications", True)
        self.include_awards = self.config.get("include_awards", True)
        self.max_pages = self.config.get("max_pages", 2)
    
    def select_content(
        self,
        cv_data: CVData,
        job_requirements: JobRequirements
    ) -> SelectedContent:
        """
        Select relevant CV content for a job.
        
        Args:
            cv_data: Complete CV data
            job_requirements: Parsed job requirements
            
        Returns:
            SelectedContent with filtered and ranked content
        """
        # Score all achievements
        scored_achievements = self.scorer.score_achievements(
            cv_data,
            job_requirements
        )
        
        # Filter top achievements
        top_achievements = self.scorer.filter_top_achievements(
            scored_achievements,
            max_per_job=self.max_achievements_per_job,
            min_score=self.min_achievement_score
        )
        
        # Group achievements by experience
        achievements_by_exp = self._group_by_experience(top_achievements)
        
        # Build selected experiences
        selected_experiences = self._build_experiences(
            cv_data.experience,
            achievements_by_exp
        )
        
        # Select relevant skills
        selected_skills = self._select_skills(cv_data, job_requirements)
        
        # Calculate metadata
        avg_score = (
            sum(sa.total_score for sa in top_achievements) / len(top_achievements)
            if top_achievements else 0.0
        )
        
        job_match = self._calculate_job_match(
            cv_data,
            job_requirements,
            top_achievements
        )
        
        return SelectedContent(
            personal_info=self._export_personal_info(cv_data),
            summary=cv_data.summary,
            experiences=selected_experiences,
            skills=selected_skills,
            education=self._export_education(cv_data) if cv_data.education else None,
            certifications=self._export_certifications(cv_data) if cv_data.certifications else None,
            volunteer=self._export_volunteer(cv_data) if self.include_volunteer and cv_data.volunteer else None,
            projects=self._export_projects(cv_data, job_requirements) if self.include_projects and cv_data.projects else None,
            publications=self._export_publications(cv_data) if self.include_publications and cv_data.publications else None,
            awards=self._export_awards(cv_data) if self.include_awards and cv_data.awards else None,
            total_achievements_selected=len(top_achievements),
            average_relevance_score=avg_score,
            job_match_summary=job_match
        )
    
    def _group_by_experience(
        self,
        scored_achievements: List[ScoredAchievement]
    ) -> Dict[str, List[ScoredAchievement]]:
        """Group scored achievements by experience."""
        grouped = {}
        for sa in scored_achievements:
            key = f"{sa.experience.company}_{sa.experience.position}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(sa)
        return grouped
    
    def _build_experiences(
        self,
        all_experiences: List[Experience],
        achievements_by_exp: Dict[str, List[ScoredAchievement]]
    ) -> List[Dict[str, Any]]:
        """Build experience list with selected achievements."""
        selected = []
        
        for exp in all_experiences:
            key = f"{exp.company}_{exp.position}"
            
            # Skip experiences with no selected achievements
            if key not in achievements_by_exp:
                continue
            
            scored_achievements = achievements_by_exp[key]
            
            # Sort by score
            scored_achievements.sort(reverse=True)
            
            # Build experience dict
            exp_dict = {
                "company": exp.company,
                "position": exp.position,
                "location": exp.location,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "description": exp.description,
                "achievements": [
                    {
                        "text": sa.achievement.text,
                        "skills": sa.achievement.skills,
                        "impact": sa.achievement.impact.value,
                        "metrics": sa.achievement.metrics,
                        "relevance_score": sa.total_score
                    }
                    for sa in scored_achievements
                ]
            }
            
            selected.append(exp_dict)
        
        return selected
    
    def _select_skills(
        self,
        cv_data: CVData,
        job_requirements: JobRequirements
    ) -> Dict[str, Any]:
        """Select relevant skills based on job requirements."""
        if not cv_data.skills:
            return {}
        
        result = {}
        
        # Get required skills from job
        required_skills = set()
        if job_requirements.required_skills:
            required_skills.update(s.lower() for s in job_requirements.required_skills)
        if job_requirements.technologies:
            required_skills.update(t.lower() for t in job_requirements.technologies)
        
        # Filter technical skills
        if cv_data.skills.technical:
            relevant_tech = []
            for skill in cv_data.skills.technical:
                if skill.name.lower() in required_skills:
                    relevant_tech.append({
                        "name": skill.name,
                        "level": skill.level.value if skill.level else None,
                        "years": skill.years
                    })
            
            # Add remaining skills up to a limit
            remaining = [
                {
                    "name": skill.name,
                    "level": skill.level.value if skill.level else None,
                    "years": skill.years
                }
                for skill in cv_data.skills.technical
                if skill.name.lower() not in required_skills
            ]
            
            # Prioritize by years of experience
            remaining.sort(key=lambda x: x.get("years", 0) or 0, reverse=True)
            
            result["technical"] = relevant_tech + remaining[:10]  # Max 10 additional
        
        # Include all soft skills
        if cv_data.skills.soft:
            result["soft"] = cv_data.skills.soft
        
        # Include all languages
        if cv_data.skills.languages:
            result["languages"] = [
                {
                    "language": lang.language,
                    "proficiency": lang.proficiency
                }
                for lang in cv_data.skills.languages
            ]
        
        return result
    
    def _export_personal_info(self, cv_data: CVData) -> Dict[str, Any]:
        """Export personal information."""
        return {
            "name": cv_data.personal.name,
            "email": cv_data.personal.email,
            "phone": cv_data.personal.phone,
            "location": cv_data.personal.location,
            "linkedin": str(cv_data.personal.linkedin) if cv_data.personal.linkedin else None,
            "github": str(cv_data.personal.github) if cv_data.personal.github else None,
            "website": str(cv_data.personal.website) if cv_data.personal.website else None,
        }
    
    def _export_education(self, cv_data: CVData) -> List[Dict[str, Any]]:
        """Export education information."""
        return [
            {
                "institution": edu.institution,
                "degree": edu.degree,
                "field": edu.field,
                "location": edu.location,
                "start_date": edu.start_date,
                "graduation_date": edu.graduation_date,
                "status": edu.status.value if edu.status else None,
                "gpa": edu.gpa,
                "honors": edu.honors,
                "relevant_coursework": edu.relevant_coursework
            }
            for edu in cv_data.education
        ]
    
    def _export_certifications(self, cv_data: CVData) -> List[Dict[str, Any]]:
        """Export certifications."""
        return [
            {
                "name": cert.name,
                "issuer": cert.issuer,
                "date": cert.date,
                "expiry": cert.expiry,
                "credential_id": cert.credential_id,
                "url": str(cert.url) if cert.url else None
            }
            for cert in cv_data.certifications
        ]
    
    def _export_volunteer(self, cv_data: CVData) -> List[Dict[str, Any]]:
        """Export volunteer work."""
        return [
            {
                "organization": vol.organization,
                "role": vol.role,
                "start_date": vol.start_date,
                "end_date": vol.end_date,
                "description": vol.description,
                "achievements": vol.achievements,
                "type": vol.type.value if vol.type else None
            }
            for vol in cv_data.volunteer
        ]
    
    def _export_projects(
        self,
        cv_data: CVData,
        job_requirements: JobRequirements
    ) -> List[Dict[str, Any]]:
        """Export relevant projects."""
        if not cv_data.projects:
            return []
        
        # Get required technologies
        required_tech = set()
        if job_requirements.technologies:
            required_tech.update(t.lower() for t in job_requirements.technologies)
        
        # Score projects by technology match
        scored_projects = []
        for project in cv_data.projects:
            project_tech = {t.lower() for t in project.technologies}
            match_count = len(project_tech.intersection(required_tech))
            scored_projects.append((match_count, project))
        
        # Sort by match count
        scored_projects.sort(reverse=True, key=lambda x: x[0])
        
        # Take top 3-5 projects
        return [
            {
                "name": project.name,
                "description": project.description,
                "technologies": project.technologies,
                "url": str(project.url) if project.url else None,
                "github": str(project.github) if project.github else None,
                "achievements": project.achievements,
                "start_date": project.start_date,
                "end_date": project.end_date
            }
            for _, project in scored_projects[:5]
        ]
    
    def _export_publications(self, cv_data: CVData) -> List[Dict[str, Any]]:
        """Export publications."""
        return [
            {
                "title": pub.title,
                "venue": pub.venue,
                "date": pub.date,
                "authors": pub.authors,
                "url": str(pub.url) if pub.url else None,
                "description": pub.description
            }
            for pub in cv_data.publications
        ]
    
    def _export_awards(self, cv_data: CVData) -> List[Dict[str, Any]]:
        """Export awards."""
        return [
            {
                "title": award.title,
                "issuer": award.issuer,
                "date": award.date,
                "description": award.description
            }
            for award in cv_data.awards
        ]
    
    def _calculate_job_match(
        self,
        cv_data: CVData,
        job_requirements: JobRequirements,
        selected_achievements: List[ScoredAchievement]
    ) -> Dict[str, Any]:
        """Calculate job match summary."""
        # Get all CV skills
        cv_skills = set(cv_data.get_all_skills())
        cv_skills_lower = {s.lower() for s in cv_skills}
        
        # Get required skills
        required_skills = set()
        if job_requirements.required_skills:
            required_skills.update(s.lower() for s in job_requirements.required_skills)
        if job_requirements.technologies:
            required_skills.update(t.lower() for t in job_requirements.technologies)
        
        # Calculate matches
        matched_skills = cv_skills_lower.intersection(required_skills)
        missing_skills = required_skills - cv_skills_lower
        
        skill_match_rate = (
            len(matched_skills) / len(required_skills)
            if required_skills else 0.0
        )
        
        return {
            "skill_match_rate": skill_match_rate,
            "matched_skills": sorted(list(matched_skills)),
            "missing_skills": sorted(list(missing_skills)),
            "total_achievements": len(selected_achievements),
            "average_score": (
                sum(sa.total_score for sa in selected_achievements) / len(selected_achievements)
                if selected_achievements else 0.0
            ),
            "years_experience_required": job_requirements.years_experience,
            "seniority_level": job_requirements.seniority_level
        }
