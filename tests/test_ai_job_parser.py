"""
Tests for AI-powered job description parser.
"""

import pytest
from unittest.mock import Mock, MagicMock
from core.job.ai_parser import AIJobDescriptionParser, parse_job_description_with_ai
from core.job.parser import JobRequirements
from core.llm.base import LLMResponse, LLMError


class TestAIJobDescriptionParser:
    """Test AI job description parser."""
    
    @pytest.fixture
    def mock_llm_provider(self):
        """Create a mock LLM provider."""
        provider = Mock()
        provider.generate = MagicMock()
        return provider
    
    @pytest.fixture
    def sample_job_data(self):
        """Sample job data for testing."""
        return {
            "title": "Senior Python Developer",
            "company": "Tech Corp",
            "location": "San Francisco, CA",
            "description": """
We are looking for a Senior Python Developer to join our team.

Responsibilities:
- Develop and maintain Python applications
- Lead technical design discussions
- Mentor junior developers
- Deploy applications to AWS

Requirements:
- 5+ years of Python experience
- Experience with Django or Flask
- Strong knowledge of AWS services
- Experience with Docker and Kubernetes

Preferred:
- Experience with React
- Knowledge of machine learning
            """
        }
    
    @pytest.fixture
    def sample_ai_response(self):
        """Sample AI response with extracted data."""
        return LLMResponse(
            content='''
{
  "required_skills": ["Python", "Django", "Flask", "AWS", "Docker", "Kubernetes"],
  "preferred_skills": ["React", "Machine Learning"],
  "responsibilities": [
    "Develop and maintain Python applications",
    "Lead technical design discussions",
    "Mentor junior developers",
    "Deploy applications to AWS"
  ],
  "qualifications": [
    "5+ years of Python experience",
    "Experience with Django or Flask",
    "Strong knowledge of AWS services",
    "Experience with Docker and Kubernetes"
  ],
  "technologies": ["Python", "Django", "Flask", "AWS", "Docker", "Kubernetes", "React"],
  "action_verbs": ["develop", "maintain", "lead", "mentor", "deploy"],
  "keywords": ["applications", "technical", "design", "cloud", "containers"],
  "seniority_level": "senior",
  "employment_type": null,
  "years_experience": 5
}
            ''',
            model="claude-3-sonnet",
            usage={"input_tokens": 500, "output_tokens": 300}
        )
    
    def test_parse_with_ai_success(self, mock_llm_provider, sample_job_data, sample_ai_response):
        """Test successful AI parsing."""
        mock_llm_provider.generate.return_value = sample_ai_response
        
        parser = AIJobDescriptionParser(mock_llm_provider)
        requirements = parser.parse(sample_job_data)
        
        # Verify basic info
        assert requirements.title == "Senior Python Developer"
        assert requirements.company == "Tech Corp"
        assert requirements.location == "San Francisco, CA"
        
        # Verify extracted skills
        assert "Python" in requirements.required_skills
        assert "AWS" in requirements.required_skills
        assert "React" in requirements.preferred_skills
        
        # Verify responsibilities
        assert len(requirements.responsibilities) == 4
        assert any("Python applications" in r for r in requirements.responsibilities)
        
        # Verify metadata
        assert requirements.seniority_level == "senior"
        assert requirements.years_experience == 5
        
        # Verify technologies
        assert "Python" in requirements.technologies
        assert "Docker" in requirements.technologies
    
    def test_parse_with_empty_description(self, mock_llm_provider):
        """Test parsing with empty description."""
        parser = AIJobDescriptionParser(mock_llm_provider)
        requirements = parser.parse({"description": ""})
        
        assert requirements.raw_description == ""
        assert len(requirements.required_skills) == 0
        # LLM should not be called for empty description
        mock_llm_provider.generate.assert_not_called()
    
    def test_parse_with_ai_failure_fallback(self, mock_llm_provider, sample_job_data):
        """Test fallback to basic extraction when AI fails."""
        mock_llm_provider.generate.side_effect = LLMError("API error")
        
        parser = AIJobDescriptionParser(mock_llm_provider)
        requirements = parser.parse(sample_job_data)
        
        # Should still return a JobRequirements object
        assert isinstance(requirements, JobRequirements)
        assert requirements.title == "Senior Python Developer"
        
        # Basic extraction should find some technologies
        assert len(requirements.technologies) > 0
    
    def test_parse_from_text(self, mock_llm_provider, sample_ai_response):
        """Test parsing from plain text."""
        mock_llm_provider.generate.return_value = sample_ai_response
        
        parser = AIJobDescriptionParser(mock_llm_provider)
        requirements = parser.parse_from_text(
            description="Looking for Python developer with AWS experience",
            title="Python Developer",
            company="Tech Co"
        )
        
        assert requirements.title == "Python Developer"
        assert requirements.company == "Tech Co"
        assert len(requirements.required_skills) > 0
    
    def test_convenience_function(self, mock_llm_provider, sample_job_data, sample_ai_response):
        """Test convenience function."""
        mock_llm_provider.generate.return_value = sample_ai_response
        
        requirements = parse_job_description_with_ai(sample_job_data, mock_llm_provider)
        
        assert isinstance(requirements, JobRequirements)
        assert requirements.title == "Senior Python Developer"
        assert len(requirements.required_skills) > 0
    
    def test_invalid_json_response(self, mock_llm_provider, sample_job_data):
        """Test handling of invalid JSON response."""
        invalid_response = LLMResponse(
            content="This is not valid JSON",
            model="claude-3-sonnet"
        )
        mock_llm_provider.generate.return_value = invalid_response
        
        parser = AIJobDescriptionParser(mock_llm_provider)
        
        # Should fall back to basic extraction
        requirements = parser.parse(sample_job_data)
        assert isinstance(requirements, JobRequirements)
    
    def test_json_with_extra_text(self, mock_llm_provider, sample_job_data):
        """Test handling of JSON response with extra text."""
        response_with_text = LLMResponse(
            content='''
Here is the extracted information:

{
  "required_skills": ["Python", "AWS"],
  "preferred_skills": [],
  "responsibilities": ["Develop applications"],
  "qualifications": ["5 years experience"],
  "technologies": ["Python", "AWS"],
  "action_verbs": ["develop"],
  "keywords": ["applications"],
  "seniority_level": "senior",
  "employment_type": null,
  "years_experience": 5
}

Hope this helps!
            ''',
            model="claude-3-sonnet"
        )
        mock_llm_provider.generate.return_value = response_with_text
        
        parser = AIJobDescriptionParser(mock_llm_provider)
        requirements = parser.parse(sample_job_data)
        
        # Should successfully extract JSON despite extra text
        assert "Python" in requirements.required_skills
        assert requirements.years_experience == 5

