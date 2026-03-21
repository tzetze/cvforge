"""
Job description parser for extracting requirements, skills, and keywords.

This module analyzes job descriptions to extract key information that can be
used for CV tailoring and achievement scoring.
"""

import re
from typing import List, Set, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class JobRequirements:
    """Parsed job requirements and information."""
    
    # Basic info
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    
    # Extracted information
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    responsibilities: List[str] = field(default_factory=list)
    qualifications: List[str] = field(default_factory=list)
    
    # Keywords and phrases
    keywords: Set[str] = field(default_factory=set)
    action_verbs: Set[str] = field(default_factory=set)
    technologies: Set[str] = field(default_factory=set)
    
    # Metadata
    seniority_level: Optional[str] = None
    employment_type: Optional[str] = None
    years_experience: Optional[int] = None
    
    # Raw data
    raw_description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "responsibilities": self.responsibilities,
            "qualifications": self.qualifications,
            "keywords": list(self.keywords),
            "action_verbs": list(self.action_verbs),
            "technologies": list(self.technologies),
            "seniority_level": self.seniority_level,
            "employment_type": self.employment_type,
            "years_experience": self.years_experience,
        }


class JobDescriptionParser:
    """
    Parser for job descriptions.
    
    Extracts skills, requirements, keywords, and other relevant information
    from job descriptions to enable intelligent CV tailoring.
    """
    
    # Common technical skills and technologies
    TECH_KEYWORDS = {
        # Programming languages
        "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
        "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
        
        # Web technologies
        "react", "angular", "vue", "node.js", "express", "django", "flask",
        "spring", "asp.net", "html", "css", "sass", "webpack", "babel",
        
        # Databases
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "cassandra", "dynamodb", "oracle", "sql server",
        
        # Cloud & DevOps
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
        "jenkins", "gitlab", "github actions", "ci/cd", "devops",
        
        # Data & ML
        "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
        "pandas", "numpy", "spark", "hadoop", "kafka", "airflow",
        
        # Tools & Frameworks
        "git", "jira", "agile", "scrum", "rest api", "graphql", "microservices",
        "linux", "unix", "bash", "powershell",
    }
    
    # Common action verbs in job descriptions
    ACTION_VERBS = {
        "develop", "build", "design", "implement", "create", "maintain",
        "lead", "manage", "coordinate", "collaborate", "work", "support",
        "analyze", "optimize", "improve", "enhance", "troubleshoot", "debug",
        "deploy", "integrate", "test", "document", "review", "mentor",
        "architect", "scale", "automate", "monitor", "ensure", "deliver",
    }
    
    def __init__(self):
        """Initialize the parser."""
        self.tech_pattern = self._build_tech_pattern()
    
    def _build_tech_pattern(self) -> re.Pattern:
        """Build regex pattern for matching technologies."""
        # Escape special regex characters and sort by length (longest first)
        techs = sorted(self.TECH_KEYWORDS, key=len, reverse=True)
        escaped = [re.escape(tech) for tech in techs]
        pattern = r'\b(' + '|'.join(escaped) + r')\b'
        return re.compile(pattern, re.IGNORECASE)
    
    def parse(self, job_data: Dict[str, Any]) -> JobRequirements:
        """
        Parse job data and extract requirements.
        
        Args:
            job_data: Dict with job information (from scraper or manual input)
            
        Returns:
            JobRequirements object with extracted information
        """
        requirements = JobRequirements()
        
        # Extract basic info
        requirements.title = job_data.get("title")
        requirements.company = job_data.get("company")
        requirements.location = job_data.get("location")
        requirements.seniority_level = job_data.get("seniority_level")
        requirements.employment_type = job_data.get("employment_type")
        
        # Get description
        description = job_data.get("description", "")
        requirements.raw_description = description
        
        if not description:
            return requirements
        
        # Clean description (remove benefits/legal sections)
        cleaned_description = self._clean_description(description)
        
        # Extract sections
        self._extract_sections(description, requirements)
        
        # Extract skills from cleaned description
        self._extract_skills(cleaned_description, requirements)
        
        # Extract technologies from cleaned description
        self._extract_technologies(cleaned_description, requirements)
        
        # Extract action verbs from cleaned description
        self._extract_action_verbs(cleaned_description, requirements)
        
        # Extract keywords from cleaned description
        self._extract_keywords(cleaned_description, requirements)
        
        # Extract years of experience from cleaned description
        self._extract_years_experience(cleaned_description, requirements)
        
        return requirements
    
    def _clean_description(self, description: str) -> str:
        """Remove benefits, legal, and other non-job-requirement sections."""
        lines = description.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_lower = line.lower()
            # Stop at benefits/legal sections
            if any(keyword in line_lower for keyword in [
                "additional information", "we take care", "benefits", "compensation",
                "equal opportunity", "diversity", "applicants have rights",
                "privacy statement", "salary range", "total rewards", "different people approach"
            ]):
                break
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_sections(self, description: str, requirements: JobRequirements) -> None:
        """Extract different sections from job description."""
        
        # Split into lines
        lines = description.split('\n')
        
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for section headers
            line_lower = line.lower()
            
            # Skip non-job-requirement sections (benefits, legal, etc.)
            if any(keyword in line_lower for keyword in [
                "additional information", "we take care", "benefits", "compensation",
                "equal opportunity", "diversity", "applicants have rights",
                "privacy statement", "salary range", "total rewards"
            ]):
                # Save current section and stop processing
                if current_section and section_content:
                    self._save_section(current_section, section_content, requirements)
                current_section = None
                section_content = []
            elif any(keyword in line_lower for keyword in ["responsibilities", "what you'll do", "role"]):
                if current_section and section_content:
                    self._save_section(current_section, section_content, requirements)
                current_section = "responsibilities"
                section_content = []
            elif any(keyword in line_lower for keyword in ["requirements", "qualifications", "what we're looking for"]):
                if current_section and section_content:
                    self._save_section(current_section, section_content, requirements)
                current_section = "qualifications"
                section_content = []
            elif any(keyword in line_lower for keyword in ["required skills", "must have"]):
                if current_section and section_content:
                    self._save_section(current_section, section_content, requirements)
                current_section = "required_skills"
                section_content = []
            elif any(keyword in line_lower for keyword in ["preferred", "nice to have", "bonus"]):
                if current_section and section_content:
                    self._save_section(current_section, section_content, requirements)
                current_section = "preferred_skills"
                section_content = []
            else:
                # Add to current section
                if current_section:
                    # Check if it's a bullet point
                    if line.startswith(('•', '-', '*', '·')) or re.match(r'^\d+\.', line):
                        # Remove bullet point
                        line = re.sub(r'^[•\-*·\d]+\.?\s*', '', line)
                        if line:
                            section_content.append(line)
                    elif len(line) > 20:  # Likely a full sentence
                        section_content.append(line)
        
        # Save last section
        if current_section and section_content:
            self._save_section(current_section, section_content, requirements)
    
    def _save_section(self, section: str, content: List[str], requirements: JobRequirements) -> None:
        """Save extracted section content."""
        if section == "responsibilities":
            requirements.responsibilities.extend(content)
        elif section == "qualifications":
            requirements.qualifications.extend(content)
        elif section == "required_skills":
            # Filter out long sentences, keep only actual skills (< 100 chars)
            skills = [item for item in content if len(item) < 100]
            requirements.required_skills.extend(skills)
        elif section == "preferred_skills":
            # Filter out long sentences, keep only actual skills (< 100 chars)
            skills = [item for item in content if len(item) < 100]
            requirements.preferred_skills.extend(skills)
    
    def _extract_skills(self, description: str, requirements: JobRequirements) -> None:
        """Extract skills from description."""
        # Look for common skill patterns
        skill_patterns = [
            r'experience (?:with|in) ([^.,\n]+)',
            r'proficiency in ([^.,\n]+)',
            r'knowledge of ([^.,\n]+)',
            r'expertise in ([^.,\n]+)',
            r'skilled in ([^.,\n]+)',
            r'familiar with ([^.,\n]+)',
        ]
        
        for pattern in skill_patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                skills_text = match.group(1).strip()
                # Split by 'and', 'or', commas
                skills = re.split(r'\s+(?:and|or)\s+|,\s*', skills_text)
                for skill in skills:
                    skill = skill.strip()
                    if skill and len(skill) > 2:
                        if not requirements.required_skills or skill not in requirements.required_skills:
                            requirements.required_skills.append(skill)
    
    def _extract_technologies(self, description: str, requirements: JobRequirements) -> None:
        """Extract technology keywords."""
        matches = self.tech_pattern.finditer(description)
        for match in matches:
            tech = match.group(1).lower()
            requirements.technologies.add(tech)
    
    def _extract_action_verbs(self, description: str, requirements: JobRequirements) -> None:
        """Extract action verbs."""
        words = re.findall(r'\b\w+\b', description.lower())
        for word in words:
            if word in self.ACTION_VERBS:
                requirements.action_verbs.add(word)
    
    def _extract_keywords(self, description: str, requirements: JobRequirements) -> None:
        """Extract important keywords."""
        # Expanded stop words list
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "should", "could", "may", "might", "must", "can", "this",
            "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
            "our", "your", "their", "all", "any", "each", "every", "some", "many",
            "more", "most", "other", "such", "only", "own", "same", "than", "too",
            "very", "just", "where", "when", "who", "what", "which", "how", "why",
            "about", "into", "through", "during", "before", "after", "above", "below",
            "between", "under", "again", "further", "then", "once", "here", "there",
            "whether", "both", "few", "more", "most", "other", "some", "such", "not",
            "only", "own", "same", "so", "than", "too", "very", "can", "will", "just"
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', description.lower())
        
        # Count frequency
        word_freq = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords (appearing 2+ times, limit to top 50 by frequency)
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        for word, freq in sorted_keywords[:50]:
            if freq >= 2:
                requirements.keywords.add(word)
    
    def _extract_years_experience(self, description: str, requirements: JobRequirements) -> None:
        """Extract years of experience requirement."""
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'(\d+)\+?\s*years?\s+(?:of\s+)?(?:professional\s+)?experience',
            r'minimum\s+(?:of\s+)?(\d+)\s+years?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                years = int(match.group(1))
                if requirements.years_experience is None or years > requirements.years_experience:
                    requirements.years_experience = years
    
    def parse_from_text(self, description: str, title: Optional[str] = None,
                       company: Optional[str] = None) -> JobRequirements:
        """
        Parse job description from plain text.
        
        Args:
            description: Job description text
            title: Optional job title
            company: Optional company name
            
        Returns:
            JobRequirements object
        """
        job_data = {
            "description": description,
            "title": title,
            "company": company,
        }
        return self.parse(job_data)


def parse_job_description(job_data: Dict[str, Any]) -> JobRequirements:
    """
    Convenience function to parse a job description.
    
    Args:
        job_data: Dict with job information
        
    Returns:
        JobRequirements object
    """
    parser = JobDescriptionParser()
    return parser.parse(job_data)

