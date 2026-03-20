"""
CV Data Validator

Validates CV data for completeness, quality, and best practices.
Provides actionable feedback for improving CV content.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from core.models import CVData, Experience, Achievement

logger = logging.getLogger(__name__)


class ValidationIssue:
    """Represents a validation issue with severity and suggestions."""
    
    SEVERITY_ERROR = "error"
    SEVERITY_WARNING = "warning"
    SEVERITY_INFO = "info"
    
    def __init__(
        self,
        severity: str,
        category: str,
        message: str,
        field: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        self.severity = severity
        self.category = category
        self.message = message
        self.field = field
        self.suggestion = suggestion
    
    def __repr__(self) -> str:
        return f"ValidationIssue({self.severity}, {self.category}, {self.message})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "field": self.field,
            "suggestion": self.suggestion
        }


class ValidationReport:
    """Validation report containing all issues and summary."""
    
    def __init__(self):
        self.issues: List[ValidationIssue] = []
        self.timestamp = datetime.now()
    
    def add_issue(
        self,
        severity: str,
        category: str,
        message: str,
        field: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        """Add a validation issue."""
        issue = ValidationIssue(severity, category, message, field, suggestion)
        self.issues.append(issue)
    
    def add_error(self, category: str, message: str, field: Optional[str] = None, suggestion: Optional[str] = None):
        """Add an error-level issue."""
        self.add_issue(ValidationIssue.SEVERITY_ERROR, category, message, field, suggestion)
    
    def add_warning(self, category: str, message: str, field: Optional[str] = None, suggestion: Optional[str] = None):
        """Add a warning-level issue."""
        self.add_issue(ValidationIssue.SEVERITY_WARNING, category, message, field, suggestion)
    
    def add_info(self, category: str, message: str, field: Optional[str] = None, suggestion: Optional[str] = None):
        """Add an info-level issue."""
        self.add_issue(ValidationIssue.SEVERITY_INFO, category, message, field, suggestion)
    
    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return sum(1 for issue in self.issues if issue.severity == ValidationIssue.SEVERITY_ERROR)
    
    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return sum(1 for issue in self.issues if issue.severity == ValidationIssue.SEVERITY_WARNING)
    
    @property
    def info_count(self) -> int:
        """Count of info-level issues."""
        return sum(1 for issue in self.issues if issue.severity == ValidationIssue.SEVERITY_INFO)
    
    @property
    def is_valid(self) -> bool:
        """Check if CV data is valid (no errors)."""
        return self.error_count == 0
    
    def get_issues_by_severity(self, severity: str) -> List[ValidationIssue]:
        """Get all issues of a specific severity."""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_issues_by_category(self, category: str) -> List[ValidationIssue]:
        """Get all issues of a specific category."""
        return [issue for issue in self.issues if issue.category == category]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "is_valid": self.is_valid,
            "summary": {
                "errors": self.error_count,
                "warnings": self.warning_count,
                "info": self.info_count,
                "total": len(self.issues)
            },
            "issues": [issue.to_dict() for issue in self.issues]
        }
    
    def __str__(self) -> str:
        """String representation of the report."""
        lines = [
            f"CV Validation Report ({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})",
            f"Status: {'VALID' if self.is_valid else 'INVALID'}",
            f"Errors: {self.error_count}, Warnings: {self.warning_count}, Info: {self.info_count}",
            ""
        ]
        
        if self.issues:
            for issue in self.issues:
                prefix = {
                    ValidationIssue.SEVERITY_ERROR: "❌ ERROR",
                    ValidationIssue.SEVERITY_WARNING: "⚠️  WARNING",
                    ValidationIssue.SEVERITY_INFO: "ℹ️  INFO"
                }.get(issue.severity, "")
                
                lines.append(f"{prefix} [{issue.category}] {issue.message}")
                if issue.field:
                    lines.append(f"  Field: {issue.field}")
                if issue.suggestion:
                    lines.append(f"  Suggestion: {issue.suggestion}")
                lines.append("")
        
        return "\n".join(lines)


class CVValidator:
    """
    Validates CV data for completeness and quality.
    
    Checks:
    - Required fields presence
    - Data quality (length, format, etc.)
    - Best practices (achievement metrics, skill levels, etc.)
    - Consistency (dates, formatting)
    """
    
    def __init__(
        self,
        min_experiences: int = 1,
        min_achievements_per_role: int = 2,
        min_achievement_length: int = 30,
        max_achievement_length: int = 200,
        min_summary_length: int = 100,
        max_summary_length: int = 500
    ):
        """
        Initialize validator with configurable thresholds.
        
        Args:
            min_experiences: Minimum number of work experiences
            min_achievements_per_role: Minimum achievements per role
            min_achievement_length: Minimum achievement text length
            max_achievement_length: Maximum achievement text length
            min_summary_length: Minimum summary length
            max_summary_length: Maximum summary length
        """
        self.min_experiences = min_experiences
        self.min_achievements_per_role = min_achievements_per_role
        self.min_achievement_length = min_achievement_length
        self.max_achievement_length = max_achievement_length
        self.min_summary_length = min_summary_length
        self.max_summary_length = max_summary_length
    
    def validate(self, cv_data: CVData) -> ValidationReport:
        """
        Validate CV data and return comprehensive report.
        
        Args:
            cv_data: CV data to validate
        
        Returns:
            ValidationReport with all issues found
        """
        report = ValidationReport()
        
        # Validate each section
        self._validate_personal_info(cv_data, report)
        self._validate_summary(cv_data, report)
        self._validate_experiences(cv_data, report)
        self._validate_skills(cv_data, report)
        self._validate_education(cv_data, report)
        self._validate_optional_sections(cv_data, report)
        
        logger.info(f"Validation complete: {report.error_count} errors, {report.warning_count} warnings")
        
        return report
    
    def _validate_personal_info(self, cv_data: CVData, report: ValidationReport):
        """Validate personal information section."""
        pi = cv_data.personal
        
        # Required fields
        if not pi.name or len(pi.name.strip()) < 2:
            report.add_error(
                "personal_info",
                "Name is required and must be at least 2 characters",
                "personal_info.name",
                "Provide your full name"
            )
        
        if not pi.email:
            report.add_error(
                "personal_info",
                "Email is required",
                "personal_info.email",
                "Add a professional email address"
            )
        elif "@" not in pi.email:
            report.add_error(
                "personal_info",
                "Email format is invalid",
                "personal_info.email",
                "Use a valid email format (e.g., name@example.com)"
            )
        
        # Recommended fields
        if not pi.phone:
            report.add_warning(
                "personal_info",
                "Phone number is recommended",
                "personal_info.phone",
                "Add a contact phone number"
            )
        
        if not pi.location:
            report.add_warning(
                "personal_info",
                "Location is recommended",
                "personal_info.location",
                "Add your city and country/state"
            )
        
        if not pi.linkedin:
            report.add_info(
                "personal_info",
                "LinkedIn profile URL is recommended",
                "personal_info.linkedin",
                "Add your LinkedIn profile for better visibility"
            )
    
    def _validate_summary(self, cv_data: CVData, report: ValidationReport):
        """Validate professional summary."""
        if not cv_data.summary:
            report.add_warning(
                "summary",
                "Professional summary is missing",
                "summary",
                "Add a 2-3 sentence summary highlighting your key strengths"
            )
            return
        
        summary_len = len(cv_data.summary)
        
        if summary_len < self.min_summary_length:
            report.add_warning(
                "summary",
                f"Summary is too short ({summary_len} chars, recommended: {self.min_summary_length}+)",
                "summary",
                "Expand your summary to better showcase your experience and skills"
            )
        
        if summary_len > self.max_summary_length:
            report.add_info(
                "summary",
                f"Summary is quite long ({summary_len} chars, recommended: <{self.max_summary_length})",
                "summary",
                "Consider making your summary more concise"
            )
    
    def _validate_experiences(self, cv_data: CVData, report: ValidationReport):
        """Validate work experiences."""
        if not cv_data.experience:
            report.add_error(
                "experiences",
                "At least one work experience is required",
                "experiences",
                "Add your work history with achievements"
            )
            return
        
        if len(cv_data.experience) < self.min_experiences:
            report.add_warning(
                "experiences",
                f"Only {len(cv_data.experience)} experience(s) listed (recommended: {self.min_experiences}+)",
                "experiences",
                "Add more relevant work experiences"
            )
        
        for i, exp in enumerate(cv_data.experience):
            self._validate_experience(exp, i, report)
    
    def _validate_experience(self, exp: Experience, index: int, report: ValidationReport):
        """Validate a single work experience."""
        prefix = f"experiences[{index}]"
        
        # Required fields
        if not exp.company:
            report.add_error(
                "experiences",
                f"Company name is missing for experience #{index + 1}",
                f"{prefix}.company",
                "Add the company name"
            )
        
        if not exp.position:
            report.add_error(
                "experiences",
                f"Position/title is missing for experience #{index + 1}",
                f"{prefix}.position",
                "Add your job title"
            )
        
        if not exp.start_date:
            report.add_error(
                "experiences",
                f"Start date is missing for {exp.company or 'experience'}",
                f"{prefix}.start_date",
                "Add the start date (YYYY-MM format)"
            )
        
        # Achievements
        if not exp.achievements:
            report.add_error(
                "experiences",
                f"No achievements listed for {exp.position or 'position'} at {exp.company or 'company'}",
                f"{prefix}.achievements",
                "Add at least 2-3 key achievements with metrics"
            )
        elif len(exp.achievements) < self.min_achievements_per_role:
            report.add_warning(
                "experiences",
                f"Only {len(exp.achievements)} achievement(s) for {exp.position} (recommended: {self.min_achievements_per_role}+)",
                f"{prefix}.achievements",
                "Add more achievements to strengthen this experience"
            )
        
        # Validate each achievement
        for j, achievement in enumerate(exp.achievements or []):
            self._validate_achievement(achievement, exp, index, j, report)
    
    def _validate_achievement(
        self,
        achievement: Achievement,
        exp: Experience,
        exp_index: int,
        ach_index: int,
        report: ValidationReport
    ):
        """Validate a single achievement."""
        prefix = f"experiences[{exp_index}].achievements[{ach_index}]"
        
        if not achievement.text:
            report.add_error(
                "achievements",
                f"Achievement text is missing for {exp.position}",
                f"{prefix}.text",
                "Add a description of what you accomplished"
            )
            return
        
        text_len = len(achievement.text)
        
        if text_len < self.min_achievement_length:
            report.add_warning(
                "achievements",
                f"Achievement is too brief ({text_len} chars) for {exp.position}",
                f"{prefix}.text",
                "Expand with more details and impact"
            )
        
        if text_len > self.max_achievement_length:
            report.add_info(
                "achievements",
                f"Achievement is quite long ({text_len} chars) for {exp.position}",
                f"{prefix}.text",
                "Consider making it more concise"
            )
        
        # Check for metrics
        if not achievement.metrics:
            report.add_info(
                "achievements",
                f"No metrics provided for achievement in {exp.position}",
                f"{prefix}.metrics",
                "Add quantifiable results (e.g., '30% increase', '1M users')"
            )
        
        # Check for skills
        if not achievement.skills:
            report.add_info(
                "achievements",
                f"No skills tagged for achievement in {exp.position}",
                f"{prefix}.skills",
                "Tag relevant technical skills used"
            )
        
        # Check for impact level
        if not achievement.impact:
            report.add_info(
                "achievements",
                f"Impact level not specified for achievement in {exp.position}",
                f"{prefix}.impact",
                "Specify impact level (low/medium/high)"
            )
    
    def _validate_skills(self, cv_data: CVData, report: ValidationReport):
        """Validate skills section."""
        if not cv_data.skills:
            report.add_warning(
                "skills",
                "Skills section is missing",
                "skills",
                "Add your technical and soft skills"
            )
            return
        
        if not cv_data.skills.technical:
            report.add_warning(
                "skills",
                "No technical skills listed",
                "skills.technical",
                "Add your technical skills with proficiency levels"
            )
        elif len(cv_data.skills.technical) < 5:
            report.add_info(
                "skills",
                f"Only {len(cv_data.skills.technical)} technical skills listed",
                "skills.technical",
                "Consider adding more relevant technical skills"
            )
        
        # Check for skill levels
        skills_without_level = [
            skill.name for skill in cv_data.skills.technical
            if not skill.level
        ]
        
        if skills_without_level:
            report.add_info(
                "skills",
                f"{len(skills_without_level)} technical skills missing proficiency level",
                "skills.technical",
                f"Add proficiency levels for: {', '.join(skills_without_level[:3])}"
            )
    
    def _validate_education(self, cv_data: CVData, report: ValidationReport):
        """Validate education section."""
        if not cv_data.education:
            report.add_warning(
                "education",
                "Education section is missing",
                "education",
                "Add your educational background"
            )
            return
        
        for i, edu in enumerate(cv_data.education):
            prefix = f"education[{i}]"
            
            if not edu.degree:
                report.add_error(
                    "education",
                    f"Degree is missing for education entry #{i + 1}",
                    f"{prefix}.degree",
                    "Add the degree name"
                )
            
            if not edu.institution:
                report.add_error(
                    "education",
                    f"Institution is missing for education entry #{i + 1}",
                    f"{prefix}.institution",
                    "Add the institution name"
                )
    
    def _validate_optional_sections(self, cv_data: CVData, report: ValidationReport):
        """Validate optional sections and provide recommendations."""
        
        # Certifications
        if not cv_data.certifications:
            report.add_info(
                "certifications",
                "No certifications listed",
                "certifications",
                "Add relevant professional certifications if you have any"
            )
        
        # Projects
        if not cv_data.projects:
            report.add_info(
                "projects",
                "No projects listed",
                "projects",
                "Consider adding notable projects to showcase your work"
            )
        
        # Check overall CV completeness
        sections_present = sum([
            bool(cv_data.summary),
            bool(cv_data.experience),
            bool(cv_data.skills),
            bool(cv_data.education),
            bool(cv_data.certifications),
            bool(cv_data.projects)
        ])
        
        if sections_present < 4:
            report.add_info(
                "completeness",
                f"CV has {sections_present}/6 main sections filled",
                None,
                "Consider adding more sections for a comprehensive CV"
            )


def validate_cv_data(cv_data: CVData) -> ValidationReport:
    """
    Convenience function to validate CV data.
    
    Args:
        cv_data: CV data to validate
    
    Returns:
        ValidationReport
    """
    validator = CVValidator()
    return validator.validate(cv_data)

