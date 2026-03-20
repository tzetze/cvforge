"""
Pydantic models for CV data validation and type safety.

These models define the structure and validation rules for all CV data,
ensuring data integrity and providing type hints throughout the application.
"""

from datetime import date
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, HttpUrl, Field, field_validator, model_validator


# Enums for constrained values
class ImpactLevel(str, Enum):
    """Achievement impact level."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SkillLevel(str, Enum):
    """Technical skill proficiency level."""
    EXPERT = "expert"
    ADVANCED = "advanced"
    INTERMEDIATE = "intermediate"
    BEGINNER = "beginner"


class EducationStatus(str, Enum):
    """Education completion status."""
    COMPLETED = "completed"
    IN_PROGRESS = "in-progress"
    INCOMPLETE = "incomplete"


class VolunteerType(str, Enum):
    """Type of volunteer work."""
    OPEN_SOURCE = "open-source"
    CONFERENCE = "conference"
    MEETUP = "meetup"
    COMMUNITY = "community"


# Achievement and Experience Models
class Achievement(BaseModel):
    """Individual achievement within a job role."""
    text: str = Field(..., min_length=10, description="Achievement description")
    skills: List[str] = Field(..., min_length=1, description="Related skills/technologies")
    impact: ImpactLevel = Field(..., description="Impact level of achievement")
    metrics: Optional[Dict[str, Any]] = Field(default=None, description="Quantifiable metrics")
    keywords: Optional[List[str]] = Field(default=None, description="Additional ATS keywords")

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Ensure achievement text is meaningful."""
        if len(v.strip()) < 10:
            raise ValueError("Achievement text must be at least 10 characters")
        return v.strip()

    @field_validator('skills')
    @classmethod
    def validate_skills(cls, v: List[str]) -> List[str]:
        """Ensure skills are not empty strings."""
        skills = [s.strip() for s in v if s.strip()]
        if not skills:
            raise ValueError("At least one skill must be provided")
        return skills


class Experience(BaseModel):
    """Work experience entry."""
    company: str = Field(..., min_length=1, description="Company name")
    position: str = Field(..., min_length=1, description="Job position/title")
    location: Optional[str] = Field(default=None, description="Job location")
    start_date: str = Field(..., pattern=r'^\d{4}-\d{2}$', description="Start date (YYYY-MM)")
    end_date: Optional[str] = Field(
        default=None,
        description="End date (YYYY-MM or 'present')"
    )
    description: Optional[str] = Field(default=None, description="Brief role overview")
    achievements: List[Achievement] = Field(..., min_length=1, description="List of achievements")

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate end date format."""
        if v is None:
            return v
        if v.lower() == 'present':
            return 'present'
        if not v or len(v) != 7 or v[4] != '-':
            raise ValueError("End date must be in YYYY-MM format or 'present'")
        return v

    @model_validator(mode='after')
    def validate_dates(self) -> 'Experience':
        """Ensure end date is after start date."""
        if self.end_date and self.end_date != 'present':
            start_year, start_month = map(int, self.start_date.split('-'))
            end_year, end_month = map(int, self.end_date.split('-'))
            if (end_year, end_month) < (start_year, start_month):
                raise ValueError("End date must be after start date")
        return self


# Personal Information Models
class PersonalInfo(BaseModel):
    """Personal contact information."""
    name: str = Field(..., min_length=1, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: Optional[str] = Field(default=None, description="City, State/Country")
    linkedin: Optional[HttpUrl] = Field(default=None, description="LinkedIn profile URL")
    github: Optional[HttpUrl] = Field(default=None, description="GitHub profile URL")
    website: Optional[HttpUrl] = Field(default=None, description="Personal website URL")


# Skills Models
class TechnicalSkill(BaseModel):
    """Technical skill with proficiency level."""
    name: str = Field(..., min_length=1, description="Skill/technology name")
    level: Optional[SkillLevel] = Field(default=None, description="Proficiency level")
    years: Optional[int] = Field(default=None, ge=0, description="Years of experience")


class Language(BaseModel):
    """Language proficiency."""
    language: str = Field(..., min_length=1, description="Language name")
    proficiency: str = Field(..., min_length=1, description="Proficiency level")


class Skills(BaseModel):
    """All skills categories."""
    technical: Optional[List[TechnicalSkill]] = Field(default=None, description="Technical skills")
    soft: Optional[List[str]] = Field(default=None, description="Soft skills")
    languages: Optional[List[Language]] = Field(default=None, description="Language proficiencies")


# Education Models
class Education(BaseModel):
    """Educational background."""
    institution: str = Field(..., min_length=1, description="Institution name")
    degree: str = Field(..., min_length=1, description="Degree type")
    field: Optional[str] = Field(default=None, description="Field of study")
    location: Optional[str] = Field(default=None, description="Institution location")
    start_date: Optional[str] = Field(default=None, description="Start date (YYYY-MM or YYYY)")
    graduation_date: Optional[str] = Field(default=None, description="Graduation date (YYYY-MM or YYYY)")
    status: Optional[EducationStatus] = Field(default=None, description="Completion status")
    gpa: Optional[str] = Field(default=None, description="GPA")
    honors: Optional[List[str]] = Field(default=None, description="Honors and awards")
    relevant_coursework: Optional[List[str]] = Field(default=None, description="Relevant courses")

    @field_validator('start_date', 'graduation_date')
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate date format (YYYY-MM or YYYY)."""
        if v is None:
            return v
        if len(v) == 4 and v.isdigit():  # YYYY format
            return v
        if len(v) == 7 and v[4] == '-':  # YYYY-MM format
            return v
        raise ValueError("Date must be in YYYY or YYYY-MM format")


# Certification Models
class Certification(BaseModel):
    """Professional certification."""
    name: str = Field(..., min_length=1, description="Certification name")
    issuer: str = Field(..., min_length=1, description="Issuing organization")
    date: str = Field(..., pattern=r'^\d{4}-\d{2}$', description="Issue date (YYYY-MM)")
    expiry: Optional[str] = Field(default=None, description="Expiry date (YYYY-MM)")
    credential_id: Optional[str] = Field(default=None, description="Credential ID")
    url: Optional[HttpUrl] = Field(default=None, description="Verification URL")


# Volunteer Work Models
class VolunteerWork(BaseModel):
    """Volunteer work and community involvement."""
    organization: str = Field(..., min_length=1, description="Organization name")
    role: str = Field(..., min_length=1, description="Role/position")
    start_date: str = Field(..., pattern=r'^\d{4}-\d{2}$', description="Start date (YYYY-MM)")
    end_date: Optional[str] = Field(default=None, description="End date (YYYY-MM or 'present')")
    description: Optional[str] = Field(default=None, description="Description of work")
    achievements: Optional[List[str]] = Field(default=None, description="Key achievements")
    type: Optional[VolunteerType] = Field(default=None, description="Type of volunteer work")

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate end date format."""
        if v is None:
            return v
        if v.lower() == 'present':
            return 'present'
        if not v or len(v) != 7 or v[4] != '-':
            raise ValueError("End date must be in YYYY-MM format or 'present'")
        return v


# Project Models
class Project(BaseModel):
    """Personal or side project."""
    name: str = Field(..., min_length=1, description="Project name")
    description: str = Field(..., min_length=10, description="Project description")
    technologies: List[str] = Field(..., min_length=1, description="Technologies used")
    url: Optional[HttpUrl] = Field(default=None, description="Project URL")
    github: Optional[HttpUrl] = Field(default=None, description="GitHub repository URL")
    achievements: Optional[List[str]] = Field(default=None, description="Key achievements")
    start_date: Optional[str] = Field(default=None, description="Start date (YYYY-MM)")
    end_date: Optional[str] = Field(default=None, description="End date (YYYY-MM or 'present')")


# Publication Models
class Publication(BaseModel):
    """Academic or professional publication."""
    title: str = Field(..., min_length=1, description="Publication title")
    venue: str = Field(..., min_length=1, description="Journal/conference name")
    date: str = Field(..., pattern=r'^\d{4}-\d{2}$', description="Publication date (YYYY-MM)")
    authors: Optional[List[str]] = Field(default=None, description="List of authors")
    url: Optional[HttpUrl] = Field(default=None, description="DOI or publication URL")
    description: Optional[str] = Field(default=None, description="Brief description")


# Award Models
class Award(BaseModel):
    """Professional award or recognition."""
    title: str = Field(..., min_length=1, description="Award title")
    issuer: str = Field(..., min_length=1, description="Issuing organization")
    date: str = Field(..., pattern=r'^\d{4}-\d{2}$', description="Award date (YYYY-MM)")
    description: Optional[str] = Field(default=None, description="Award description")


# Main CV Data Model
class CVData(BaseModel):
    """Complete CV data structure."""
    personal: PersonalInfo = Field(..., description="Personal information")
    summary: Optional[str] = Field(default=None, description="Professional summary")
    experience: List[Experience] = Field(..., min_length=1, description="Work experience")
    skills: Optional[Skills] = Field(default=None, description="Skills")
    education: Optional[List[Education]] = Field(default=None, description="Education")
    certifications: Optional[List[Certification]] = Field(default=None, description="Certifications")
    volunteer: Optional[List[VolunteerWork]] = Field(default=None, description="Volunteer work")
    projects: Optional[List[Project]] = Field(default=None, description="Projects")
    publications: Optional[List[Publication]] = Field(default=None, description="Publications")
    awards: Optional[List[Award]] = Field(default=None, description="Awards")

    @model_validator(mode='after')
    def validate_cv_data(self) -> 'CVData':
        """Perform cross-field validation."""
        # Ensure at least some content exists
        has_content = (
            len(self.experience) > 0 or
            (self.education and len(self.education) > 0) or
            (self.projects and len(self.projects) > 0)
        )
        if not has_content:
            raise ValueError("CV must have at least experience, education, or projects")
        return self

    def get_all_skills(self) -> List[str]:
        """Extract all skills from CV data."""
        skills = set()
        
        # Technical skills
        if self.skills and self.skills.technical:
            skills.update(skill.name for skill in self.skills.technical)
        
        # Skills from achievements
        for exp in self.experience:
            for achievement in exp.achievements:
                skills.update(achievement.skills)
        
        # Skills from projects
        if self.projects:
            for project in self.projects:
                skills.update(project.technologies)
        
        return sorted(list(skills))

    def get_total_achievements(self) -> int:
        """Get total number of achievements across all experiences."""
        return sum(len(exp.achievements) for exp in self.experience)


# Settings Models
class LLMProviderConfig(BaseModel):
    """Configuration for a single LLM provider."""
    type: str = Field(..., description="Provider type (claude, ollama)")
    api_key: Optional[str] = Field(default=None, description="API key (for Claude)")
    base_url: Optional[str] = Field(default=None, description="Base URL (for Ollama)")
    model: str = Field(..., description="Model name")
    max_tokens: Optional[int] = Field(default=4096, ge=1, description="Maximum tokens")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature")
    timeout: int = Field(default=60, ge=1, description="Request timeout in seconds")


class LLMConfig(BaseModel):
    """LLM configuration with multiple providers."""
    default_provider: str = Field(..., description="Default provider name to use")
    providers: Dict[str, LLMProviderConfig] = Field(..., description="Provider configurations")

    @model_validator(mode='after')
    def validate_default_provider(self) -> 'LLMConfig':
        """Ensure default provider exists in providers."""
        if self.default_provider not in self.providers:
            raise ValueError(f"Default provider '{self.default_provider}' not found in providers")
        return self


class ScoringWeights(BaseModel):
    """Weights for achievement scoring."""
    keyword_match: float = Field(default=0.30, ge=0.0, le=1.0)
    skill_match: float = Field(default=0.25, ge=0.0, le=1.0)
    impact_level: float = Field(default=0.20, ge=0.0, le=1.0)
    recency: float = Field(default=0.15, ge=0.0, le=1.0)
    semantic_similarity: float = Field(default=0.10, ge=0.0, le=1.0)

    @model_validator(mode='after')
    def validate_weights_sum(self) -> 'ScoringWeights':
        """Ensure weights sum to approximately 1.0."""
        total = (
            self.keyword_match +
            self.skill_match +
            self.impact_level +
            self.recency +
            self.semantic_similarity
        )
        if not (0.99 <= total <= 1.01):  # Allow small floating point errors
            raise ValueError(f"Scoring weights must sum to 1.0, got {total}")
        return self


class Settings(BaseModel):
    """Application settings."""
    app: Dict[str, Any] = Field(default_factory=dict, description="App settings")
    paths: Dict[str, str] = Field(default_factory=dict, description="File paths")
    llm: LLMConfig = Field(..., description="LLM configuration")
    cv_generation: Dict[str, Any] = Field(default_factory=dict, description="CV generation settings")
    scoring: ScoringWeights = Field(default_factory=ScoringWeights, description="Scoring weights")
    job_scraping: Dict[str, Any] = Field(default_factory=dict, description="Job scraping settings")
    pdf: Dict[str, Any] = Field(default_factory=dict, description="PDF generation settings")
    web: Dict[str, Any] = Field(default_factory=dict, description="Web UI settings")
    validation: Dict[str, Any] = Field(default_factory=dict, description="Validation settings")
    logging: Dict[str, Any] = Field(default_factory=dict, description="Logging settings")
    features: Dict[str, bool] = Field(default_factory=dict, description="Feature flags")
    cache: Dict[str, Any] = Field(default_factory=dict, description="Cache settings")

