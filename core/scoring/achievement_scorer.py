"""
Achievement scoring system for ranking CV achievements by relevance.

This module implements a multi-factor scoring system that evaluates how well
each achievement matches a job description.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Union
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
    - LLM relevance score (50%) - semantic understanding of job match
    - Impact level (25%)
    - Recency (25%)
    """
    
    def __init__(self, weights: Optional[Dict[str, int]] = None):
        """
        Initialize the scorer.
        
        Args:
            weights: Optional custom scoring weights as integers (relative weights).
                     Will be normalized to ratios that sum to 1.0.
                     
        Examples:
            weights = {"llm_relevance": 2, "impact_level": 1, "recency": 1}
            # Normalized to: {"llm_relevance": 0.5, "impact_level": 0.25, "recency": 0.25}
            
            weights = {"llm_relevance": 3, "impact_level": 2, "recency": 1}
            # Normalized to: {"llm_relevance": 0.5, "impact_level": 0.333, "recency": 0.167}
        """
        # Default weights (as integers)
        default_weights = {
            "llm_relevance": 2,
            "impact_level": 1,
            "recency": 1,
        }
        
        if weights is None:
            weights = default_weights
        
        # Normalize integer weights to ratios
        self.weights = self._normalize_weights(weights)
    
    def _normalize_weights(self, weights: Dict[str, int]) -> Dict[str, float]:
        """
        Normalize integer weights to ratios that sum to 1.0.
        
        Args:
            weights: Dictionary of integer weight values
            
        Returns:
            Normalized weights that sum to 1.0
            
        Raises:
            ValueError: If weights are invalid
        """
        if not weights:
            raise ValueError("Weights dictionary cannot be empty")
        
        # Check if any weight is negative
        if any(w < 0 for w in weights.values()):
            raise ValueError("Weights cannot be negative")
        
        total = sum(weights.values())
        
        if total == 0:
            raise ValueError("Weights cannot all be zero")
        
        # Normalize to ratios
        normalized = {key: value / total for key, value in weights.items()}
        return normalized
    
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
            
            print(f"[DEBUG] LLM Response for {len(achievements)} achievements:")
            print(f"[DEBUG] {response.content[:500]}")
            
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
                                print(f"[DEBUG] Parsed score: {score}")
                                break
                        except ValueError:
                            continue
                except Exception:
                    continue
            
            # Ensure we have enough scores (fallback to 0.5 if parsing failed)
            while len(scores) < len(achievements):
                print(f"[DEBUG] Adding fallback score 0.5 (parsed {len(scores)}/{len(achievements)})")
                scores.append(0.5)
            
            print(f"[DEBUG] Final scores: {scores[:len(achievements)]}")
            
            # Return only the number of scores we need
            return scores[:len(achievements)]
            
        except Exception as e:
            # Fallback to neutral scores if LLM fails
            print(f"[ERROR] LLM batch scoring failed: {e}")
            import traceback
            traceback.print_exc()
            return [0.5] * len(achievements)
    
    def score_achievements(
        self,
        cv_data: CVData,
        job_requirements: JobRequirements,
        job_description: str = "",
        llm = None,
    ) -> List[ScoredAchievement]:
        """
        Score all achievements in CV data against job requirements.
        
        Args:
            cv_data: CV data with experiences and achievements
            job_requirements: Parsed job requirements
            job_description: Full job description text
            llm: LLM provider for semantic scoring (optional, falls back to rule-based)
            
        Returns:
            List of ScoredAchievement objects, sorted by score (highest first)
        """
        scored_achievements = []
        
        # Collect all achievements with their experiences
        all_achievements = []
        all_experiences = []
        for experience in cv_data.experience:
            for achievement in experience.achievements:
                all_achievements.append(achievement)
                all_experiences.append(experience)
        
        # Get LLM relevance scores in batch if LLM is provided
        llm_scores = []
        if llm and all_achievements:
            try:
                llm_scores = self.llm_score_achievements_batch(
                    achievements=all_achievements,
                    experiences=all_experiences,
                    job_requirements=job_requirements,
                    job_description=job_description,
                    llm=llm,
                )
            except Exception as e:
                print(f"Warning: LLM batch scoring failed, using fallback: {e}")
                llm_scores = [0.5] * len(all_achievements)
        else:
            # Fallback to neutral scores if no LLM
            llm_scores = [0.5] * len(all_achievements)
        
        # Score each achievement with its LLM score
        idx = 0
        for experience in cv_data.experience:
            for achievement in experience.achievements:
                score = self.score_achievement(
                    achievement=achievement,
                    experience=experience,
                    job_requirements=job_requirements,
                    llm_relevance_score=llm_scores[idx],
                )
                scored_achievements.append(score)
                idx += 1
        
        # Sort by total score (highest first)
        scored_achievements.sort(reverse=True)
        
        return scored_achievements
    
    def score_achievement(
        self,
        achievement: Achievement,
        experience: Experience,
        job_requirements: JobRequirements,
        llm_relevance_score: float = 0.5,
    ) -> ScoredAchievement:
        """
        Score a single achievement.
        
        Args:
            achievement: Achievement to score
            experience: Experience containing the achievement
            job_requirements: Job requirements
            llm_relevance_score: Pre-computed LLM relevance score (0.0-1.0)
            
        Returns:
            ScoredAchievement object
        """
        breakdown = {}
        
        # 1. LLM relevance (50%) - semantic understanding of job match
        breakdown["llm_relevance"] = llm_relevance_score
        
        # 2. Impact level (25%)
        breakdown["impact_level"] = self._score_impact_level(achievement)
        
        # 3. Recency (25%)
        breakdown["recency"] = self._score_recency(experience)
        
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

