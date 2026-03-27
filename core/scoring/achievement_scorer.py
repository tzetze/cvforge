"""
Achievement scoring system for ranking CV achievements by relevance.

This module implements a multi-factor scoring system that evaluates how well
each achievement matches a job description.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import re

from core.models import Achievement, Experience, CVData
from core.job.parser import JobRequirements


@dataclass
class ScoredAchievement:
    """Achievement with relevance score."""
    achievement: Achievement
    experience: Experience
    total_score: float
    score_breakdown: Dict[str, float]
    
    def __lt__(self, other):
        """Allow sorting by score."""
        return self.total_score < other.total_score


class AchievementScorer:
    """
    Scores achievements based on relevance to job requirements.
    
    Uses a multi-factor scoring system:
    - Keyword matching (30%)
    - Skill matching (25%)
    - Impact level (20%)
    - Recency (15%)
    - Semantic similarity (10%) - requires LLM
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize the scorer.
        
        Args:
            weights: Optional custom scoring weights
        """
        # Default weights (must sum to 1.0)
        self.weights = weights or {
            "keyword_match": 0.30,
            "skill_match": 0.25,
            "impact_level": 0.20,
            "recency": 0.15,
            "semantic_similarity": 0.10,
        }
        
        # Validate weights
        total = sum(self.weights.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    
    def llm_score_achievements_batch(
        self,
        achievements: List[Achievement],
        experiences: List[Experience],
        job_requirements: JobRequirements,
        job_description: str,
        llm,
    ) -> List[float]:
        """
        Score multiple achievements using LLM in a single batch call.
        
        This is more cost-efficient than scoring individually.
        
        Args:
            achievements: List of achievements to score
            experiences: Corresponding experiences (same length as achievements)
            job_requirements: Parsed job requirements
            job_description: Full job description text
            llm: LLM provider instance
            
        Returns:
            List of scores (0.0-1.0) for each achievement
        """
        if not achievements:
            return []
        
        # Build achievements text for prompt
        achievements_text = ""
        for i, (ach, exp) in enumerate(zip(achievements, experiences), 1):
            skills_str = ", ".join(ach.skills) if ach.skills else "None"
            achievements_text += f"{i}. {ach.text}\n   Skills: {skills_str}\n   Impact: {ach.impact.value}\n\n"
        
        # Get key requirements
        required_skills = ", ".join(job_requirements.required_skills[:10]) if job_requirements.required_skills else "Not specified"
        preferred_skills = ", ".join(job_requirements.preferred_skills[:10]) if job_requirements.preferred_skills else "Not specified"
        
        # Truncate job description if too long
        job_desc_preview = job_description[:800] + "..." if len(job_description) > 800 else job_description
        
        prompt = f"""Score each achievement's relevance to this job position (0.0 to 1.0).

Job Title: {job_requirements.title}
Company: {job_requirements.company or "Not specified"}

Required Skills: {required_skills}
Preferred Skills: {preferred_skills}

Job Description Summary:
{job_desc_preview}

Achievements to Score:
{achievements_text}

Instructions:
1. Consider semantic similarity, not just exact keyword matching
2. Recognize abbreviations and variations (e.g., "JS" = "JavaScript", "K8s" = "Kubernetes")
3. Evaluate if the achievement demonstrates relevant experience for this role
4. Consider the impact level and quantifiable results
5. Higher scores for achievements that directly relate to job requirements
6. Lower scores for generic or unrelated achievements

Output format (one score per line, ONLY the number):
1. 0.85
2. 0.62
3. 0.91
...

Scores:"""

        try:
            response = llm.generate(
                prompt=prompt,
                temperature=0.0,  # Deterministic scoring
                max_tokens=len(achievements) * 15
            )
            
            # Parse scores from response
            scores = []
            lines = response.content.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    # Try to extract number from various formats
                    # "1. 0.85" or "0.85" or "1: 0.85"
                    parts = re.split(r'[.:\s]+', line)
                    for part in parts:
                        try:
                            score = float(part)
                            if 0.0 <= score <= 1.0:
                                scores.append(score)
                                break
                        except ValueError:
                            continue
                except Exception:
                    continue
            
            # Ensure we have enough scores (fallback to 0.5 if parsing failed)
            while len(scores) < len(achievements):
                scores.append(0.5)
            
            # Return only the number of scores we need
            return scores[:len(achievements)]
            
        except Exception as e:
            # Fallback to neutral scores if LLM fails
            print(f"Warning: LLM batch scoring failed: {e}")
            return [0.5] * len(achievements)
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    
    def score_achievements(
        self,
        cv_data: CVData,
        job_requirements: JobRequirements,
        use_semantic: bool = False,
    ) -> List[ScoredAchievement]:
        """
        Score all achievements in CV data against job requirements.
        
        Args:
            cv_data: CV data with experiences and achievements
            job_requirements: Parsed job requirements
            use_semantic: Whether to use semantic similarity (requires LLM)
            
        Returns:
            List of ScoredAchievement objects, sorted by score (highest first)
        """
        scored_achievements = []
        
        for experience in cv_data.experience:
            for achievement in experience.achievements:
                score = self.score_achievement(
                    achievement,
                    experience,
                    job_requirements,
                    use_semantic=use_semantic,
                )
                scored_achievements.append(score)
        
        # Sort by total score (highest first)
        scored_achievements.sort(reverse=True)
        
        return scored_achievements
    
    def score_achievement(
        self,
        achievement: Achievement,
        experience: Experience,
        job_requirements: JobRequirements,
        use_semantic: bool = False,
    ) -> ScoredAchievement:
        """
        Score a single achievement.
        
        Args:
            achievement: Achievement to score
            experience: Experience containing the achievement
            job_requirements: Job requirements
            use_semantic: Whether to use semantic similarity
            
        Returns:
            ScoredAchievement object
        """
        breakdown = {}
        
        # 1. Keyword matching (30%)
        breakdown["keyword_match"] = self._score_keyword_match(
            achievement, job_requirements
        )
        
        # 2. Skill matching (25%)
        breakdown["skill_match"] = self._score_skill_match(
            achievement, job_requirements
        )
        
        # 3. Impact level (20%)
        breakdown["impact_level"] = self._score_impact_level(achievement)
        
        # 4. Recency (15%)
        breakdown["recency"] = self._score_recency(experience)
        
        # 5. Semantic similarity (10%)
        if use_semantic:
            breakdown["semantic_similarity"] = self._score_semantic_similarity(
                achievement, job_requirements
            )
        else:
            breakdown["semantic_similarity"] = 0.5  # Neutral score
        
        # Calculate weighted total
        total_score = sum(
            breakdown[key] * self.weights[key]
            for key in breakdown.keys()
        )
        
        return ScoredAchievement(
            achievement=achievement,
            experience=experience,
            total_score=total_score,
            score_breakdown=breakdown,
        )
    
    def _score_keyword_match(
        self,
        achievement: Achievement,
        job_requirements: JobRequirements,
    ) -> float:
        """
        Score based on keyword matching.
        
        Returns score between 0.0 and 1.0.
        """
        if not job_requirements.keywords:
            return 0.5  # Neutral score if no keywords
        
        # Get achievement text and keywords
        achievement_text = achievement.text.lower()
        achievement_keywords = set()
        
        if achievement.keywords:
            achievement_keywords.update(k.lower() for k in achievement.keywords)
        
        # Extract words from achievement text
        words = set(re.findall(r'\b\w+\b', achievement_text))
        achievement_keywords.update(words)
        
        # Count matches
        job_keywords = {k.lower() for k in job_requirements.keywords}
        matches = achievement_keywords.intersection(job_keywords)
        
        if not job_keywords:
            return 0.5
        
        # Calculate match ratio
        match_ratio = len(matches) / len(job_keywords)
        
        # Scale to 0-1 range (cap at 50% match = 1.0 score)
        score = min(match_ratio * 2.0, 1.0)
        
        return score
    
    def _score_skill_match(
        self,
        achievement: Achievement,
        job_requirements: JobRequirements,
    ) -> float:
        """
        Score based on skill matching.
        
        Returns score between 0.0 and 1.0.
        """
        # Get required skills from job
        required_skills = set()
        if job_requirements.required_skills:
            required_skills.update(s.lower() for s in job_requirements.required_skills)
        if job_requirements.technologies:
            required_skills.update(t.lower() for t in job_requirements.technologies)
        
        if not required_skills:
            return 0.5  # Neutral score if no required skills
        
        # Get achievement skills
        achievement_skills = {s.lower() for s in achievement.skills}
        
        # Count matches
        matches = achievement_skills.intersection(required_skills)
        
        if not achievement_skills:
            return 0.0
        
        # Calculate match ratio
        match_ratio = len(matches) / len(required_skills)
        
        # Scale to 0-1 range (cap at 40% match = 1.0 score)
        score = min(match_ratio * 2.5, 1.0)
        
        return score
    
    def _score_impact_level(self, achievement: Achievement) -> float:
        """
        Score based on impact level.
        
        Returns score between 0.0 and 1.0.
        """
        impact_scores = {
            "high": 1.0,
            "medium": 0.6,
            "low": 0.3,
        }
        
        return impact_scores.get(achievement.impact.value, 0.5)
    
    def _score_recency(self, experience: Experience) -> float:
        """
        Score based on how recent the experience is.
        
        Returns score between 0.0 and 1.0.
        """
        try:
            # Parse end date
            if experience.end_date and experience.end_date.lower() == "present":
                # Current job gets highest score
                return 1.0
            
            if experience.end_date:
                end_year, end_month = map(int, experience.end_date.split('-'))
            else:
                # If no end date, use start date
                end_year, end_month = map(int, experience.start_date.split('-'))
            
            # Calculate years ago
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            years_ago = current_year - end_year
            months_ago = current_month - end_month
            total_years_ago = years_ago + (months_ago / 12.0)
            
            # Score decreases with age
            # 0 years ago = 1.0
            # 2 years ago = 0.8
            # 5 years ago = 0.5
            # 10+ years ago = 0.2
            if total_years_ago <= 0:
                return 1.0
            elif total_years_ago <= 2:
                return 1.0 - (total_years_ago * 0.1)
            elif total_years_ago <= 5:
                return 0.8 - ((total_years_ago - 2) * 0.1)
            elif total_years_ago <= 10:
                return 0.5 - ((total_years_ago - 5) * 0.06)
            else:
                return 0.2
                
        except Exception:
            # If date parsing fails, return neutral score
            return 0.5
    
    def _score_semantic_similarity(
        self,
        achievement: Achievement,
        job_requirements: JobRequirements,
    ) -> float:
        """
        Score based on semantic similarity.
        
        This is a placeholder that returns a neutral score.
        In a full implementation, this would use an LLM to compare
        the semantic meaning of the achievement with job requirements.
        
        Returns score between 0.0 and 1.0.
        """
        # TODO: Implement LLM-based semantic similarity
        # For now, return neutral score
        return 0.5
    
    def filter_top_achievements(
        self,
        scored_achievements: List[ScoredAchievement],
        max_per_job: int = 5,
        min_score: float = 0.3,
    ) -> List[ScoredAchievement]:
        """
        Filter achievements to keep only the most relevant ones.
        
        Args:
            scored_achievements: List of scored achievements
            max_per_job: Maximum achievements per job
            min_score: Minimum score threshold
            
        Returns:
            Filtered list of achievements
        """
        # Filter by minimum score
        filtered = [
            sa for sa in scored_achievements
            if sa.total_score >= min_score
        ]
        
        # Group by experience
        by_experience: Dict[str, List[ScoredAchievement]] = {}
        for sa in filtered:
            key = f"{sa.experience.company}_{sa.experience.position}"
            if key not in by_experience:
                by_experience[key] = []
            by_experience[key].append(sa)
        
        # Keep top N per experience
        result = []
        for achievements in by_experience.values():
            # Sort by score
            achievements.sort(reverse=True)
            # Take top N
            result.extend(achievements[:max_per_job])
        
        # Sort final result by score
        result.sort(reverse=True)
        
        return result
    
    def get_score_summary(
        self,
        scored_achievements: List[ScoredAchievement]
    ) -> Dict[str, Any]:
        """
        Get summary statistics for scored achievements.
        
        Args:
            scored_achievements: List of scored achievements
            
        Returns:
            Dict with summary statistics
        """
        if not scored_achievements:
            return {
                "total_achievements": 0,
                "average_score": 0.0,
                "max_score": 0.0,
                "min_score": 0.0,
                "score_distribution": {},
            }
        
        scores = [sa.total_score for sa in scored_achievements]
        
        # Calculate distribution
        distribution = {
            "high (>0.7)": sum(1 for s in scores if s > 0.7),
            "medium (0.4-0.7)": sum(1 for s in scores if 0.4 <= s <= 0.7),
            "low (<0.4)": sum(1 for s in scores if s < 0.4),
        }
        
        return {
            "total_achievements": len(scored_achievements),
            "average_score": sum(scores) / len(scores),
            "max_score": max(scores),
            "min_score": min(scores),
            "score_distribution": distribution,
        }

