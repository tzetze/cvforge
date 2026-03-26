"""
CV tailoring engine for rewriting content with LLM.

This module uses LLM to tailor CV content (summary, achievements) to match
specific job requirements while maintaining authenticity.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from copy import deepcopy

from core.llm.base import LLMProvider
from core.generation.cv_selector import SelectedContent
from core.job.parser import JobRequirements
from core.models import CVData


@dataclass
class TailoredCV:
    """Tailored CV content ready for rendering."""
    
    # Tailored content
    personal_info: Dict[str, Any]
    summary: str
    experiences: List[Dict[str, Any]]
    skills: Dict[str, Any]
    
    # Optional sections
    education: Optional[List[Dict[str, Any]]]
    certifications: Optional[List[Dict[str, Any]]]
    volunteer: Optional[List[Dict[str, Any]]]
    projects: Optional[List[Dict[str, Any]]]
    publications: Optional[List[Dict[str, Any]]]
    awards: Optional[List[Dict[str, Any]]]
    
    # Metadata
    job_title: Optional[str]
    company: Optional[str]
    tailoring_notes: List[str]


class CVTailoringEngine:
    """
    Tailors CV content using LLM to match job requirements.
    
    Takes selected content and rewrites it to emphasize relevant skills
    and experiences while maintaining authenticity and truthfulness.
    """
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the tailoring engine.
        
        Args:
            llm_provider: LLM provider for content generation
            config: Optional configuration dict
        """
        self.llm = llm_provider
        self.config = config or {}
        
        # Configuration
        self.rewrite_achievements = self.config.get("rewrite_achievements", True)
        self.rewrite_summary = self.config.get("rewrite_summary", True)
        self.max_summary_length = self.config.get("max_summary_length", 150)
    
    def tailor_cv(
        self,
        selected_content: SelectedContent,
        job_requirements: JobRequirements,
        job_description: Optional[str] = None
    ) -> TailoredCV:
        """
        Tailor CV content for a specific job.
        
        Args:
            selected_content: Pre-selected relevant content
            job_requirements: Job requirements
            job_description: Original job description text (optional, for better context)
            
        Returns:
            TailoredCV with rewritten content
        """
        tailoring_notes = []
        
        # Tailor summary
        if self.rewrite_summary and selected_content.summary:
            tailored_summary = self._tailor_summary(
                selected_content.summary,
                job_requirements,
                selected_content.job_match_summary,
                job_description
            )
            tailoring_notes.append("Summary tailored to job requirements")
        else:
            tailored_summary = selected_content.summary or self._generate_summary(
                selected_content,
                job_requirements,
                job_description
            )
            if not selected_content.summary:
                tailoring_notes.append("Summary generated from scratch")
        
        # Tailor achievements
        if self.rewrite_achievements:
            tailored_experiences = self._tailor_experiences(
                selected_content.experiences,
                job_requirements,
                job_description
            )
            tailoring_notes.append(f"Tailored {len(selected_content.experiences)} experiences")
        else:
            tailored_experiences = selected_content.experiences
        
        return TailoredCV(
            personal_info=selected_content.personal_info,
            summary=tailored_summary,
            experiences=tailored_experiences,
            skills=selected_content.skills,
            education=selected_content.education,
            certifications=selected_content.certifications,
            volunteer=selected_content.volunteer,
            projects=selected_content.projects,
            publications=selected_content.publications,
            awards=selected_content.awards,
            job_title=job_requirements.title,
            company=job_requirements.company,
            tailoring_notes=tailoring_notes
        )
    
    def tailor_all_achievements(
        self,
        cv_data: CVData,
        job_requirements: JobRequirements,
        job_description: Optional[str] = None
    ) -> CVData:
        """
        Tailor all achievements in the CV for a job.
        
        This method tailors ALL achievements upfront before scoring/selection,
        preserving original text for comparison. Returns a new CVData object
        with tailored achievements.
        
        Args:
            cv_data: Complete CV data
            job_requirements: Job requirements
            job_description: Original job description text (optional, for better context)
            
        Returns:
            New CVData with tailored achievements (original text preserved in metadata)
        """
        # Create a deep copy to avoid modifying original
        tailored_cv = deepcopy(cv_data)
        
        # Tailor summary if it exists
        if tailored_cv.summary and self.rewrite_summary:
            # Create a minimal job match summary for context
            job_match_summary = {
                "matched_skills": list(job_requirements.required_skills or [])[:5],
                "match_score": 0.0  # Not calculated yet
            }
            
            tailored_cv.summary = self._tailor_summary(
                tailored_cv.summary,
                job_requirements,
                job_match_summary,
                job_description
            )
        
        # Tailor all experiences and achievements
        if self.rewrite_achievements:
            tailored_experiences = []
            
            for exp in tailored_cv.experience:
                tailored_exp = exp.model_copy(deep=True)
                
                if exp.achievements:
                    # Convert achievements to dict format for tailoring
                    achievements_dicts = [
                        {
                            "text": ach.text,
                            "skills": ach.skills,
                            "impact": ach.impact,
                            "metrics": ach.metrics,
                            "keywords": ach.keywords
                        }
                        for ach in exp.achievements
                    ]
                    
                    # Tailor achievements for this experience as a batch
                    tailored_achievements_dicts = self._tailor_achievements_batch(
                        achievements_dicts,
                        job_requirements,
                        job_description
                    )
                    
                    # Update achievements with tailored text, preserving original
                    tailored_achievements = []
                    for i, ach in enumerate(exp.achievements):
                        tailored_ach = ach.model_copy(deep=True)
                        
                        # Store original text in keywords for comparison
                        # (we'll use a special format to identify it)
                        original_keywords = list(tailored_ach.keywords or [])
                        if not any(k.startswith("__original__:") for k in original_keywords):
                            original_keywords.append(f"__original__:{ach.text}")
                        
                        # Update with tailored text
                        tailored_ach.text = tailored_achievements_dicts[i]["text"]
                        tailored_ach.keywords = original_keywords
                        
                        tailored_achievements.append(tailored_ach)
                    
                    tailored_exp.achievements = tailored_achievements
                
                tailored_experiences.append(tailored_exp)
            
            tailored_cv.experience = tailored_experiences
        
        return tailored_cv
    
    def get_original_achievement_text(self, achievement: Dict[str, Any]) -> Optional[str]:
        """
        Extract original achievement text from keywords metadata.
        
        Args:
            achievement: Achievement dict with keywords
            
        Returns:
            Original text if found, None otherwise
        """
        keywords = achievement.get("keywords", [])
        for keyword in keywords:
            if isinstance(keyword, str) and keyword.startswith("__original__:"):
                return keyword[len("__original__:"):]
        return None
    
    def _tailor_summary(
        self,
        original_summary: str,
        job_requirements: JobRequirements,
        job_match: Dict[str, Any],
        job_description: Optional[str] = None
    ) -> str:
        """Tailor professional summary for the job."""
        
        # Build context
        matched_skills = ", ".join(job_match.get("matched_skills", [])[:5])
        
        # Include original job description if available
        job_context = ""
        if job_description:
            # Truncate if too long (keep first 500 chars for context)
            job_desc_preview = job_description[:500] + "..." if len(job_description) > 500 else job_description
            job_context = f"""

Original Job Posting:
{job_desc_preview}
"""
        
        prompt = f"""Rewrite this professional summary to emphasize relevance for a {job_requirements.title} position at {job_requirements.company or 'the company'}.

Original Summary:
{original_summary}

Job Requirements:
- Title: {job_requirements.title}
- Key Skills: {matched_skills}
- Seniority: {job_requirements.seniority_level or 'Not specified'}{job_context}

CRITICAL INSTRUCTIONS:
- Output ONLY the rewritten summary text
- Do NOT include explanations, notes, or commentary
- Do NOT use phrases like "Rewritten Summary:", "Note:", etc.
- Keep the summary truthful and authentic
- Emphasize skills and experiences relevant to this role
- Use keywords from the job description naturally
- Keep it concise (2-3 sentences, max {self.max_summary_length} words)
- Maintain professional tone
- Do NOT add false information or exaggerate

Output the rewritten summary text only:"""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=300
            )
            
            tailored = response.content.strip()
            
            # Clean up any commentary or formatting
            tailored = self._clean_llm_response(tailored)
            
            # Fallback to original if response is too short or seems invalid
            if len(tailored) < 50 or not tailored:
                return original_summary
            
            return tailored
            
        except Exception as e:
            # Fallback to original on error
            print(f"Warning: Failed to tailor summary: {e}")
            return original_summary
    
    def _generate_summary(
        self,
        selected_content: SelectedContent,
        job_requirements: JobRequirements,
        job_description: Optional[str] = None
    ) -> str:
        """Generate a professional summary from scratch."""
        
        # Extract key info
        experiences = selected_content.experiences
        skills = selected_content.skills.get("technical", [])[:5]
        skill_names = [s["name"] for s in skills] if skills else []
        
        # Get years of experience
        total_years = len(experiences) * 2  # Rough estimate
        
        # Include original job description if available
        job_context = ""
        if job_description:
            job_desc_preview = job_description[:500] + "..." if len(job_description) > 500 else job_description
            job_context = f"""

Job Posting Context:
{job_desc_preview}
"""
        
        prompt = f"""Generate a professional summary for a {job_requirements.title} position.

Candidate Background:
- {len(experiences)} relevant positions
- Approximately {total_years} years of experience
- Key skills: {", ".join(skill_names)}
- Target role: {job_requirements.title}{job_context}

Instructions:
1. Write a concise 2-3 sentence professional summary
2. Highlight relevant experience and skills
3. Use keywords: {", ".join(skill_names[:3])}
4. Keep it under {self.max_summary_length} words
5. Be specific and professional
6. Do NOT make up information

Professional Summary:"""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=300
            )
            
            return response.content.strip()
            
        except Exception as e:
            # Fallback to generic summary
            print(f"Warning: Failed to generate summary: {e}")
            return f"Experienced professional with expertise in {', '.join(skill_names[:3])}."
    
    def _tailor_experiences(
        self,
        experiences: List[Dict[str, Any]],
        job_requirements: JobRequirements,
        job_description: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Tailor experience descriptions and achievements."""
        
        tailored = []
        
        for exp in experiences:
            tailored_exp = exp.copy()
            
            # Tailor achievements for this experience as a batch
            if exp.get("achievements"):
                tailored_achievements = self._tailor_achievements_batch(
                    exp["achievements"],
                    job_requirements,
                    job_description
                )
                tailored_exp["achievements"] = tailored_achievements
            
            tailored.append(tailored_exp)
        
        return tailored
    
    def _tailor_achievements_batch(
        self,
        achievements: List[Dict[str, Any]],
        job_requirements: JobRequirements,
        job_description: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Tailor all achievements for an experience in a single LLM call to maintain consistency."""
        
        # Get relevant job skills
        job_skills = []
        if job_requirements.required_skills:
            job_skills.extend(job_requirements.required_skills[:5])
        if job_requirements.technologies:
            job_skills.extend(list(job_requirements.technologies)[:5])
        
        # Build achievements list for prompt
        achievements_text = ""
        for i, ach in enumerate(achievements, 1):
            skills_str = ", ".join(ach.get("skills", []))
            achievements_text += f"{i}. {ach['text']}\n   Skills: {skills_str}\n\n"
        
        # Include job context
        job_context = ""
        if job_description:
            job_desc_preview = job_description[:300] + "..." if len(job_description) > 300 else job_description
            job_context = f"""
Job Posting Context:
{job_desc_preview}
"""
        
        # Get max length from config
        max_words = self.config.get("max_achievement_words", 25)
        
        prompt = f"""Rewrite these {len(achievements)} achievements to emphasize relevance for a {job_requirements.title} position.

Original Achievements:
{achievements_text}

Job Requirements: {", ".join(job_skills[:5])}
{job_context}

CRITICAL INSTRUCTIONS:
- Output ONLY the rewritten achievements, numbered 1-{len(achievements)}
- Each achievement on its own line, starting with the number
- Do NOT include explanations, notes, or commentary
- Keep each achievement under {max_words} words
- Keep core accomplishments truthful and accurate
- Use action verbs and quantifiable results
- Incorporate relevant keywords naturally
- VARY your vocabulary across achievements to keep them distinct
- Common words (independently, successfully, effectively) can be used but LIMIT to once or twice total
- DISTINCTIVE words (spearheaded, orchestrated, pioneered) should be used ONLY ONCE across all achievements
- Use diverse action verbs - don't repeat the same verb across achievements
- Each achievement should sound unique while remaining professional
- Maintain the same level of impact as the original

Output format:
1. [First rewritten achievement]
2. [Second rewritten achievement]
etc."""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                temperature=0.7,  # Slightly higher for more variety
                max_tokens=len(achievements) * 100
            )
            
            # Parse the response
            lines = response.content.strip().split('\n')
            tailored_achievements = []
            
            for i, ach in enumerate(achievements, 1):
                # Find the line starting with this number
                tailored_text = None
                for line in lines:
                    line = line.strip()
                    if line.startswith(f"{i}."):
                        tailored_text = line[len(f"{i}."):].strip()
                        break
                
                # Fallback to original if parsing fails
                if not tailored_text or len(tailored_text) < 20:
                    tailored_text = ach["text"]
                
                tailored_ach = ach.copy()
                tailored_ach["text"] = tailored_text
                tailored_achievements.append(tailored_ach)
            
            return tailored_achievements
            
        except Exception as e:
            # Fallback to original on error
            print(f"Warning: Failed to tailor achievements batch: {e}")
            return achievements
    
    def _tailor_achievement(
        self,
        original_text: str,
        skills: List[str],
        job_requirements: JobRequirements,
        job_description: Optional[str] = None
    ) -> str:
        """Tailor a single achievement."""
        
        # Get relevant job skills
        job_skills = []
        if job_requirements.required_skills:
            job_skills.extend(job_requirements.required_skills[:5])
        if job_requirements.technologies:
            job_skills.extend(list(job_requirements.technologies)[:5])
        
        # Find matching skills
        matching_skills = [s for s in skills if s.lower() in [js.lower() for js in job_skills]]
        
        # Include original job description if available
        job_context = ""
        if job_description:
            # Truncate if too long (keep first 300 chars for context)
            job_desc_preview = job_description[:300] + "..." if len(job_description) > 300 else job_description
            job_context = f"""

Job Posting Context:
{job_desc_preview}
"""
        
        prompt = f"""Rewrite this achievement to emphasize relevance for a {job_requirements.title} position.

Original Achievement:
{original_text}

Achievement Skills: {", ".join(skills)}
Job Requirements: {", ".join(job_skills[:5])}
Matching Skills: {", ".join(matching_skills) if matching_skills else "None"}{job_context}

CRITICAL INSTRUCTIONS:
- Output ONLY the rewritten achievement text
- Do NOT include explanations, notes, or commentary
- Do NOT use phrases like "Rewritten Achievement:", "Key Changes:", "Note:", etc.
- Keep the core accomplishment truthful and accurate
- Emphasize skills relevant to the target role
- Use action verbs and quantifiable results
- Incorporate relevant keywords naturally
- Keep it concise (1-2 sentences)
- Do NOT add false metrics or exaggerate
- Maintain the same level of impact
- VARY your word choice - avoid repeating the same words across different achievements
- Use diverse vocabulary and phrasing to keep each achievement distinct
- Do NOT overuse words like "independently", "proactively", "successfully" etc.
- Each achievement should sound unique and professional

Output the rewritten achievement text only:"""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                temperature=0.6,  # Lower temperature for more consistency
                max_tokens=200
            )
            
            tailored = response.content.strip()
            
            # Clean up any commentary or formatting that Claude might add
            tailored = self._clean_llm_response(tailored)
            
            # Fallback to original if response seems invalid
            if len(tailored) < 20 or not tailored:
                return original_text
            
            return tailored
            
        except Exception as e:
            # Fallback to original on error
            print(f"Warning: Failed to tailor achievement: {e}")
            return original_text
    
    def _clean_llm_response(self, text: str) -> str:
        """Clean up LLM response to extract just the achievement text."""
        import re
        
        # Remove common prefixes
        prefixes_to_remove = [
            r'^Rewritten Achievement:\s*',
            r'^Achievement:\s*',
            r'^\*\*Rewritten Achievement:\*\*\s*',
            r'^\*\*Achievement:\*\*\s*',
            r'^Here\'s the rewritten achievement:\s*',
            r'^Here is the rewritten achievement:\s*',
        ]
        
        for prefix in prefixes_to_remove:
            text = re.sub(prefix, '', text, flags=re.IGNORECASE)
        
        # Split by common separators and take only the first part
        separators = [
            '\n\n---',
            '\n\n**',
            '\n\nKey Changes:',
            '\n\nNote:',
            '\n\n# ',
            '\n\nChanges made:',
            '\n\nAlternative version',
        ]
        
        for separator in separators:
            if separator in text:
                text = text.split(separator)[0]
        
        # Remove any trailing asterisks or formatting
        text = text.strip('*').strip()
        
        return text
    
    def tailor_cv_batch(
        self,
        selected_content: SelectedContent,
        job_requirements: JobRequirements
    ) -> TailoredCV:
        """
        Tailor CV using batch processing for efficiency.
        
        Sends all achievements in a single LLM call instead of individual calls.
        More efficient but less control over individual results.
        
        Args:
            selected_content: Pre-selected relevant content
            job_requirements: Job requirements
            
        Returns:
            TailoredCV with rewritten content
        """
        tailoring_notes = []
        
        # Collect all achievements
        all_achievements = []
        for exp in selected_content.experiences:
            for achievement in exp.get("achievements", []):
                all_achievements.append({
                    "company": exp["company"],
                    "position": exp["position"],
                    "text": achievement["text"],
                    "skills": achievement.get("skills", [])
                })
        
        # Tailor summary
        tailored_summary = self._tailor_summary(
            selected_content.summary or "",
            job_requirements,
            selected_content.job_match_summary
        )
        
        # Tailor all achievements in batch
        if all_achievements:
            tailored_achievements_map = self._tailor_achievements_batch(
                all_achievements,
                job_requirements
            )
            tailoring_notes.append(f"Batch tailored {len(all_achievements)} achievements")
        else:
            tailored_achievements_map = {}
        
        # Rebuild experiences with tailored achievements
        tailored_experiences = []
        achievement_index = 0
        
        for exp in selected_content.experiences:
            tailored_exp = exp.copy()
            tailored_exp_achievements = []
            
            for achievement in exp.get("achievements", []):
                if achievement_index < len(tailored_achievements_map):
                    tailored_achievement = achievement.copy()
                    tailored_achievement["text"] = tailored_achievements_map[achievement_index]["text"]
                    tailored_exp_achievements.append(tailored_achievement)
                    achievement_index += 1
            
            tailored_exp["achievements"] = tailored_exp_achievements
            tailored_experiences.append(tailored_exp)
        
        return TailoredCV(
            personal_info=selected_content.personal_info,
            summary=tailored_summary,
            experiences=tailored_experiences,
            skills=selected_content.skills,
            education=selected_content.education,
            certifications=selected_content.certifications,
            volunteer=selected_content.volunteer,
            projects=selected_content.projects,
            publications=selected_content.publications,
            awards=selected_content.awards,
            job_title=job_requirements.title,
            company=job_requirements.company,
            tailoring_notes=tailoring_notes
        )
    
