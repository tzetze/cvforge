"""
AI-powered job description parser using LLM providers.

This module uses AI to analyze job descriptions and extract requirements,
providing more accurate and context-aware parsing than regex-based approaches.
"""

import json
import logging
from typing import Dict, Any, Optional
from core.job.parser import JobRequirements
from core.llm.base import LLMProvider, LLMError

logger = logging.getLogger(__name__)


class AIJobDescriptionParser:
    """
    AI-powered parser for job descriptions.
    
    Uses LLM providers to intelligently extract skills, requirements,
    and other relevant information from job descriptions.
    """
    
    SYSTEM_PROMPT = """You are an expert job description analyzer. Your task is to extract structured information from job postings.

Analyze the job description and extract:
1. Required skills (technical and non-technical)
2. Preferred/nice-to-have skills
3. Key responsibilities
4. Qualifications and requirements
5. Technologies mentioned
6. Action verbs used
7. Important keywords
8. Seniority level indicators
9. Years of experience required

Be thorough and accurate. Extract specific skills and technologies, not generic terms.
For skills, separate technical skills (programming languages, tools, frameworks) from soft skills (leadership, communication).
"""

    EXTRACTION_PROMPT = """Analyze this job description and extract structured information in JSON format.

Job Title: {title}
Company: {company}
Location: {location}

Job Description:
{description}

Extract the following information and return ONLY a valid JSON object with these exact keys:
{{
  "required_skills": ["skill1", "skill2", ...],
  "preferred_skills": ["skill1", "skill2", ...],
  "responsibilities": ["responsibility1", "responsibility2", ...],
  "qualifications": ["qualification1", "qualification2", ...],
  "technologies": ["tech1", "tech2", ...],
  "action_verbs": ["verb1", "verb2", ...],
  "keywords": ["keyword1", "keyword2", ...],
  "seniority_level": "junior|mid|senior|lead|principal|null",
  "employment_type": "full-time|part-time|contract|null",
  "years_experience": number or null
}}

Guidelines:
- required_skills: Skills explicitly marked as required or must-have
- preferred_skills: Skills marked as preferred, nice-to-have, or bonus
- responsibilities: Main duties and what the person will do
- qualifications: Education, certifications, experience requirements
- technologies: Specific tools, languages, frameworks, platforms
- action_verbs: Key action words describing the role (develop, lead, manage, etc.)
- keywords: Important domain-specific terms and concepts
- seniority_level: Inferred from title and requirements
- years_experience: Minimum years mentioned, or null if not specified

Return ONLY the JSON object, no additional text or explanation."""

    def __init__(self, llm_provider: LLMProvider):
        """
        Initialize the AI parser.
        
        Args:
            llm_provider: LLM provider instance to use for parsing
        """
        self.llm_provider = llm_provider
    
    def parse(self, job_data: Dict[str, Any]) -> JobRequirements:
        """
        Parse job data using AI and extract requirements.
        
        Args:
            job_data: Dict with job information (from scraper or manual input)
            
        Returns:
            JobRequirements object with extracted information
            
        Raises:
            LLMError: If AI parsing fails
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
            logger.warning("Empty job description provided")
            return requirements
        
        # Use AI to extract information
        try:
            extracted_data = self._extract_with_ai(
                description=description,
                title=requirements.title or "Not specified",
                company=requirements.company or "Not specified",
                location=requirements.location or "Not specified"
            )
            
            # Populate requirements from AI extraction
            self._populate_requirements(requirements, extracted_data)
            
        except Exception as e:
            logger.error(f"AI parsing failed: {e}")
            # Fall back to basic extraction if AI fails
            logger.info("Falling back to basic extraction")
            self._basic_extraction(description, requirements)
        
        return requirements
    
    def _extract_with_ai(
        self,
        description: str,
        title: str,
        company: str,
        location: str
    ) -> Dict[str, Any]:
        """
        Use AI to extract structured information from job description.
        
        Args:
            description: Job description text
            title: Job title
            company: Company name
            location: Job location
            
        Returns:
            Dict with extracted information
            
        Raises:
            LLMError: If AI extraction fails
        """
        # Format the prompt
        prompt = self.EXTRACTION_PROMPT.format(
            title=title,
            company=company,
            location=location,
            description=description[:8000]  # Limit description length
        )
        
        # Generate response
        response = self.llm_provider.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.3,  # Lower temperature for more consistent extraction
            max_tokens=4096
        )
        
        # Parse JSON response
        try:
            # Extract JSON from response (handle cases where LLM adds extra text)
            content = response.content.strip()
            
            # Find JSON object in response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON object found in response")
            
            json_str = content[start_idx:end_idx]
            extracted_data = json.loads(json_str)
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Response content: {response.content[:500]}")
            raise LLMError(f"Invalid JSON response from AI: {e}")
    
    def _populate_requirements(
        self,
        requirements: JobRequirements,
        extracted_data: Dict[str, Any]
    ) -> None:
        """
        Populate JobRequirements object from extracted data.
        
        Args:
            requirements: JobRequirements object to populate
            extracted_data: Dict with extracted information from AI
        """
        # Skills
        requirements.required_skills = extracted_data.get("required_skills", [])
        requirements.preferred_skills = extracted_data.get("preferred_skills", [])
        
        # Responsibilities and qualifications
        requirements.responsibilities = extracted_data.get("responsibilities", [])
        requirements.qualifications = extracted_data.get("qualifications", [])
        
        # Technologies and keywords
        requirements.technologies = set(extracted_data.get("technologies", []))
        requirements.action_verbs = set(extracted_data.get("action_verbs", []))
        requirements.keywords = set(extracted_data.get("keywords", []))
        
        # Metadata
        if extracted_data.get("seniority_level"):
            requirements.seniority_level = extracted_data["seniority_level"]
        
        if extracted_data.get("employment_type"):
            requirements.employment_type = extracted_data["employment_type"]
        
        if extracted_data.get("years_experience"):
            requirements.years_experience = extracted_data["years_experience"]
    
    def _basic_extraction(
        self,
        description: str,
        requirements: JobRequirements
    ) -> None:
        """
        Fallback basic extraction if AI fails.
        
        Args:
            description: Job description text
            requirements: JobRequirements object to populate
        """
        # Simple keyword extraction as fallback
        import re
        
        # Extract common technologies
        tech_keywords = [
            "python", "javascript", "java", "react", "node.js", "aws",
            "docker", "kubernetes", "sql", "mongodb", "git"
        ]
        
        description_lower = description.lower()
        for tech in tech_keywords:
            if tech in description_lower:
                requirements.technologies.add(tech)
        
        # Extract years of experience
        years_match = re.search(r'(\d+)\+?\s*years?\s+(?:of\s+)?experience', description, re.IGNORECASE)
        if years_match:
            requirements.years_experience = int(years_match.group(1))
        
        logger.info("Basic extraction completed as fallback")
    
    def parse_from_text(
        self,
        description: str,
        title: Optional[str] = None,
        company: Optional[str] = None,
        location: Optional[str] = None
    ) -> JobRequirements:
        """
        Parse job description from plain text.
        
        Args:
            description: Job description text
            title: Optional job title
            company: Optional company name
            location: Optional location
            
        Returns:
            JobRequirements object
        """
        job_data = {
            "description": description,
            "title": title,
            "company": company,
            "location": location,
        }
        return self.parse(job_data)


def create_ai_parser(llm_provider: LLMProvider) -> AIJobDescriptionParser:
    """
    Create an AI job description parser.
    
    Args:
        llm_provider: LLM provider instance
        
    Returns:
        AIJobDescriptionParser instance
    """
    return AIJobDescriptionParser(llm_provider)


def parse_job_description_with_ai(
    job_data: Dict[str, Any],
    llm_provider: LLMProvider
) -> JobRequirements:
    """
    Convenience function to parse a job description with AI.
    
    Args:
        job_data: Dict with job information
        llm_provider: LLM provider instance
        
    Returns:
        JobRequirements object
    """
    parser = AIJobDescriptionParser(llm_provider)
    return parser.parse(job_data)

