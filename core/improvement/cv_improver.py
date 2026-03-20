"""
CV Improvement Suggester

Uses LLM to analyze CV content and provide actionable improvement suggestions.
Helps enhance achievements, summary, and overall CV quality.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from core.models import CVData, Experience, Achievement
from core.llm.base import LLMProvider
from core.validation.cv_validator import ValidationReport

logger = logging.getLogger(__name__)


@dataclass
class ImprovementSuggestion:
    """A single improvement suggestion."""
    category: str  # "achievement", "summary", "skills", "general"
    target: str  # What to improve (e.g., "experience[0].achievements[1]")
    current_text: str
    suggestion: str
    reasoning: str
    priority: str  # "high", "medium", "low"


@dataclass
class ImprovementReport:
    """Report containing all improvement suggestions."""
    suggestions: List[ImprovementSuggestion]
    overall_assessment: str
    strengths: List[str]
    areas_for_improvement: List[str]
    
    def get_high_priority(self) -> List[ImprovementSuggestion]:
        """Get high priority suggestions."""
        return [s for s in self.suggestions if s.priority == "high"]
    
    def get_by_category(self, category: str) -> List[ImprovementSuggestion]:
        """Get suggestions by category."""
        return [s for s in self.suggestions if s.category == category]
    
    def __str__(self) -> str:
        """String representation of the report."""
        lines = [
            "=" * 60,
            "CV Improvement Report",
            "=" * 60,
            "",
            "Overall Assessment:",
            self.overall_assessment,
            "",
            "Strengths:",
        ]
        
        for strength in self.strengths:
            lines.append(f"  + {strength}")
        
        lines.extend([
            "",
            "Areas for Improvement:",
        ])
        
        for area in self.areas_for_improvement:
            lines.append(f"  - {area}")
        
        lines.extend([
            "",
            f"Suggestions ({len(self.suggestions)} total):",
            ""
        ])
        
        # Group by priority
        for priority in ["high", "medium", "low"]:
            priority_suggestions = [s for s in self.suggestions if s.priority == priority]
            if priority_suggestions:
                lines.append(f"{priority.upper()} PRIORITY ({len(priority_suggestions)}):")
                for sugg in priority_suggestions:
                    lines.append(f"  [{sugg.category}] {sugg.target}")
                    lines.append(f"  Current: {sugg.current_text[:80]}...")
                    lines.append(f"  Suggestion: {sugg.suggestion}")
                    lines.append(f"  Reasoning: {sugg.reasoning}")
                    lines.append("")
        
        return "\n".join(lines)


class CVImprover:
    """
    Analyzes CV content and provides LLM-powered improvement suggestions.
    
    Features:
    - Achievement enhancement suggestions
    - Summary improvement recommendations
    - Skills presentation optimization
    - Overall CV quality assessment
    """
    
    def __init__(self, llm_provider: LLMProvider):
        """
        Initialize CV improver with LLM provider.
        
        Args:
            llm_provider: LLM provider for generating suggestions
        """
        self.llm = llm_provider
    
    def analyze_cv(
        self,
        cv_data: CVData,
        validation_report: Optional[ValidationReport] = None
    ) -> ImprovementReport:
        """
        Analyze CV and generate comprehensive improvement suggestions.
        
        Args:
            cv_data: CV data to analyze
            validation_report: Optional validation report for context
        
        Returns:
            ImprovementReport with suggestions
        """
        logger.info("Analyzing CV for improvements...")
        
        suggestions = []
        
        # Analyze summary
        if cv_data.summary:
            summary_suggestions = self._analyze_summary(cv_data.summary, cv_data)
            suggestions.extend(summary_suggestions)
        
        # Analyze achievements
        for exp_idx, experience in enumerate(cv_data.experience):
            for ach_idx, achievement in enumerate(experience.achievements):
                ach_suggestions = self._analyze_achievement(
                    achievement,
                    experience,
                    exp_idx,
                    ach_idx
                )
                suggestions.extend(ach_suggestions)
        
        # Get overall assessment
        overall_assessment, strengths, areas = self._get_overall_assessment(
            cv_data,
            validation_report
        )
        
        report = ImprovementReport(
            suggestions=suggestions,
            overall_assessment=overall_assessment,
            strengths=strengths,
            areas_for_improvement=areas
        )
        
        logger.info(f"Analysis complete: {len(suggestions)} suggestions generated")
        return report
    
    def _analyze_summary(
        self,
        summary: str,
        cv_data: CVData
    ) -> List[ImprovementSuggestion]:
        """Analyze professional summary and suggest improvements."""
        
        # Extract key info for context
        years_experience = len(cv_data.experience)
        top_skills = []
        if cv_data.skills and cv_data.skills.technical:
            top_skills = [s.name for s in cv_data.skills.technical[:5]]
        
        prompt = f"""Analyze this professional summary and suggest improvements:

SUMMARY:
{summary}

CONTEXT:
- Years of experience: {years_experience}
- Top skills: {', '.join(top_skills)}

Provide:
1. One specific improvement suggestion (max 100 words)
2. Brief reasoning (max 50 words)
3. Priority level (high/medium/low)

Format your response as:
SUGGESTION: [your suggestion]
REASONING: [your reasoning]
PRIORITY: [high/medium/low]"""
        
        try:
            response = self.llm.generate(prompt, max_tokens=300)
            
            # Parse response
            response_text = response.content
            suggestion_text = self._extract_field(response_text, "SUGGESTION")
            reasoning = self._extract_field(response_text, "REASONING")
            priority = self._extract_field(response_text, "PRIORITY").lower()
            
            if suggestion_text:
                return [ImprovementSuggestion(
                    category="summary",
                    target="summary",
                    current_text=summary,
                    suggestion=suggestion_text,
                    reasoning=reasoning or "LLM analysis",
                    priority=priority if priority in ["high", "medium", "low"] else "medium"
                )]
        
        except Exception as e:
            logger.error(f"Error analyzing summary: {e}")
        
        return []
    
    def _analyze_achievement(
        self,
        achievement: Achievement,
        experience: Experience,
        exp_idx: int,
        ach_idx: int
    ) -> List[ImprovementSuggestion]:
        """Analyze a single achievement and suggest improvements."""
        
        # Skip if achievement is already strong (has metrics and good length)
        if achievement.metrics and len(achievement.text) > 60:
            return []
        
        prompt = f"""Analyze this achievement and suggest ONE specific improvement:

ACHIEVEMENT:
{achievement.text}

CONTEXT:
- Role: {experience.position} at {experience.company}
- Current metrics: {', '.join(achievement.metrics) if achievement.metrics else 'None'}
- Skills used: {', '.join(achievement.skills) if achievement.skills else 'None'}

Focus on:
1. Adding quantifiable metrics if missing
2. Emphasizing impact and results
3. Using strong action verbs
4. Being specific and concrete

Provide:
SUGGESTION: [improved version or specific change, max 80 words]
REASONING: [why this improves it, max 40 words]
PRIORITY: [high if missing metrics, medium if good but could be better, low if minor]

Keep the core truth of the achievement - don't fabricate details."""
        
        try:
            response = self.llm.generate(prompt, max_tokens=250)
            
            response_text = response.content
            suggestion_text = self._extract_field(response_text, "SUGGESTION")
            reasoning = self._extract_field(response_text, "REASONING")
            priority = self._extract_field(response_text, "PRIORITY").lower()
            
            if suggestion_text:
                return [ImprovementSuggestion(
                    category="achievement",
                    target=f"experiences[{exp_idx}].achievements[{ach_idx}]",
                    current_text=achievement.text,
                    suggestion=suggestion_text,
                    reasoning=reasoning or "LLM analysis",
                    priority=priority if priority in ["high", "medium", "low"] else "medium"
                )]
        
        except Exception as e:
            logger.error(f"Error analyzing achievement: {e}")
        
        return []
    
    def _get_overall_assessment(
        self,
        cv_data: CVData,
        validation_report: Optional[ValidationReport]
    ) -> tuple[str, List[str], List[str]]:
        """Get overall CV assessment with strengths and areas for improvement."""
        
        # Build context
        context_parts = [
            f"Name: {cv_data.personal.name}",
            f"Experiences: {len(cv_data.experience)}",
            f"Total achievements: {sum(len(exp.achievements) for exp in cv_data.experience)}",
        ]
        
        if cv_data.skills and cv_data.skills.technical:
            context_parts.append(f"Technical skills: {len(cv_data.skills.technical)}")
        
        if validation_report:
            context_parts.append(f"Validation: {validation_report.error_count} errors, {validation_report.warning_count} warnings")
        
        prompt = f"""Provide a brief overall assessment of this CV:

CONTEXT:
{chr(10).join(context_parts)}

SUMMARY:
{cv_data.summary[:200] if cv_data.summary else 'No summary provided'}

Provide:
1. Overall assessment (2-3 sentences)
2. Top 3 strengths (bullet points)
3. Top 3 areas for improvement (bullet points)

Format:
ASSESSMENT: [your assessment]
STRENGTHS:
- [strength 1]
- [strength 2]
- [strength 3]
AREAS:
- [area 1]
- [area 2]
- [area 3]"""
        
        try:
            response = self.llm.generate(prompt, max_tokens=400)
            
            response_text = response.content
            assessment = self._extract_field(response_text, "ASSESSMENT")
            strengths_text = self._extract_section(response_text, "STRENGTHS:", "AREAS:")
            areas_text = self._extract_section(response_text, "AREAS:", None)
            
            strengths = self._parse_bullet_points(strengths_text)
            areas = self._parse_bullet_points(areas_text)
            
            return (
                assessment or "CV shows professional experience and skills.",
                strengths or ["Professional experience documented", "Skills listed", "Education included"],
                areas or ["Add more quantifiable metrics", "Expand achievement descriptions", "Include more technical details"]
            )
        
        except Exception as e:
            logger.error(f"Error getting overall assessment: {e}")
            return (
                "Unable to generate assessment.",
                ["Professional experience documented"],
                ["Consider adding more details"]
            )
    
    def improve_achievement(
        self,
        achievement_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get improved version of a single achievement.
        
        Args:
            achievement_text: Current achievement text
            context: Optional context (role, company, skills, etc.)
        
        Returns:
            Improved achievement text
        """
        context_str = ""
        if context:
            context_str = f"\nContext: {context.get('role', '')} at {context.get('company', '')}"
        
        prompt = f"""Improve this achievement by adding metrics and emphasizing impact:

CURRENT:
{achievement_text}{context_str}

Provide an improved version that:
1. Adds quantifiable metrics if possible (percentages, numbers, time saved)
2. Uses strong action verbs
3. Emphasizes business impact
4. Stays truthful to the original meaning
5. Keeps it concise (max 150 characters)

IMPROVED: [your improved version]"""
        
        try:
            response = self.llm.generate(prompt, max_tokens=150)
            improved = self._extract_field(response.content, "IMPROVED")
            return improved if improved else achievement_text
        
        except Exception as e:
            logger.error(f"Error improving achievement: {e}")
            return achievement_text
    
    def improve_summary(
        self,
        current_summary: str,
        target_role: Optional[str] = None
    ) -> str:
        """
        Get improved version of professional summary.
        
        Args:
            current_summary: Current summary text
            target_role: Optional target role to tailor for
        
        Returns:
            Improved summary text
        """
        target_context = f"\nTarget role: {target_role}" if target_role else ""
        
        prompt = f"""Improve this professional summary:

CURRENT:
{current_summary}{target_context}

Provide an improved version that:
1. Starts with years of experience and key expertise
2. Highlights 2-3 major achievements or strengths
3. Mentions relevant technical skills
4. Is concise (2-3 sentences, max 300 characters)
5. Uses confident, professional language

IMPROVED: [your improved version]"""
        
        try:
            response = self.llm.generate(prompt, max_tokens=200)
            improved = self._extract_field(response.content, "IMPROVED")
            return improved if improved else current_summary
        
        except Exception as e:
            logger.error(f"Error improving summary: {e}")
            return current_summary
    
    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a field value from LLM response."""
        lines = text.split('\n')
        for line in lines:
            if line.strip().startswith(f"{field_name}:"):
                return line.split(':', 1)[1].strip()
        return ""
    
    def _extract_section(self, text: str, start_marker: str, end_marker: Optional[str]) -> str:
        """Extract a section between markers."""
        start_idx = text.find(start_marker)
        if start_idx == -1:
            return ""
        
        start_idx += len(start_marker)
        
        if end_marker:
            end_idx = text.find(end_marker, start_idx)
            if end_idx == -1:
                return text[start_idx:].strip()
            return text[start_idx:end_idx].strip()
        
        return text[start_idx:].strip()
    
    def _parse_bullet_points(self, text: str) -> List[str]:
        """Parse bullet points from text."""
        if not text:
            return []
        
        points = []
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                points.append(line[1:].strip())
            elif line and not line.endswith(':'):
                points.append(line)
        
        return points[:3]  # Return max 3 points


def analyze_and_improve_cv(
    cv_data: CVData,
    llm_provider: LLMProvider,
    validation_report: Optional[ValidationReport] = None
) -> ImprovementReport:
    """
    Convenience function to analyze CV and get improvement suggestions.
    
    Args:
        cv_data: CV data to analyze
        llm_provider: LLM provider
        validation_report: Optional validation report
    
    Returns:
        ImprovementReport
    """
    improver = CVImprover(llm_provider)
    return improver.analyze_cv(cv_data, validation_report)

