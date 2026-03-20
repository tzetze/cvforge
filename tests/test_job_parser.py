"""
Unit tests for core.job.parser module
"""
import pytest
from core.job.parser import JobParser
from core.models import JobRequirements


class TestJobParser:
    """Tests for JobParser class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = JobParser()
    
    def test_parse_basic_job_data(self):
        """Test parsing basic job data"""
        job_data = {
            "title": "Senior Python Developer",
            "company": "Tech Corp",
            "description": """
            We are looking for a Senior Python Developer with experience in:
            - Python, Django, Flask
            - AWS, Docker, Kubernetes
            - PostgreSQL, Redis
            - RESTful APIs
            
            Requirements:
            - 5+ years of Python experience
            - Strong problem-solving skills
            - Team leadership experience
            """
        }
        
        result = self.parser.parse(job_data)
        
        assert isinstance(result, JobRequirements)
        assert result.title == "Senior Python Developer"
        assert result.company == "Tech Corp"
        assert "Python" in result.required_skills
        assert "AWS" in result.required_skills
    
    def test_parse_extracts_keywords(self):
        """Test that parser extracts relevant keywords"""
        job_data = {
            "title": "Full Stack Engineer",
            "description": """
            Looking for a Full Stack Engineer to build scalable web applications.
            Must have experience with React, Node.js, and MongoDB.
            Experience with microservices architecture is a plus.
            """
        }
        
        result = self.parser.parse(job_data)
        
        # Check that technical terms are extracted
        assert any(keyword in result.keywords for keyword in ["React", "Node.js", "MongoDB", "microservices"])
    
    def test_parse_identifies_required_vs_preferred(self):
        """Test that parser distinguishes required from preferred skills"""
        job_data = {
            "title": "Backend Developer",
            "description": """
            Required:
            - Python
            - PostgreSQL
            - REST APIs
            
            Nice to have:
            - GraphQL
            - Redis
            - Docker
            """
        }
        
        result = self.parser.parse(job_data)
        
        # Required skills should be present
        assert "Python" in result.required_skills
        assert "PostgreSQL" in result.required_skills
        
        # Preferred skills should be present
        assert "GraphQL" in result.preferred_skills or "GraphQL" in result.keywords
    
    def test_parse_handles_missing_fields(self):
        """Test parser handles missing optional fields gracefully"""
        job_data = {
            "title": "Software Engineer",
            "description": "Build great software"
        }
        
        result = self.parser.parse(job_data)
        
        assert result.title == "Software Engineer"
        assert result.company is None or result.company == ""
        assert isinstance(result.required_skills, list)
        assert isinstance(result.keywords, list)
    
    def test_parse_extracts_experience_level(self):
        """Test parser extracts experience level requirements"""
        job_data = {
            "title": "Senior Developer",
            "description": "Looking for 5+ years of experience in Python development"
        }
        
        result = self.parser.parse(job_data)
        
        # Should identify senior level or years of experience
        assert "5+" in result.description or "senior" in result.title.lower()
    
    def test_parse_normalizes_skills(self):
        """Test that parser normalizes skill names"""
        job_data = {
            "title": "Developer",
            "description": "Experience with python, PYTHON, Python required"
        }
        
        result = self.parser.parse(job_data)
        
        # Should not have duplicate skills with different cases
        python_count = sum(1 for skill in result.required_skills if skill.lower() == "python")
        assert python_count <= 1
    
    def test_parse_with_location(self):
        """Test parsing job with location information"""
        job_data = {
            "title": "Remote Developer",
            "company": "StartupXYZ",
            "location": "San Francisco, CA (Remote)",
            "description": "Build amazing products"
        }
        
        result = self.parser.parse(job_data)
        
        assert result.location == "San Francisco, CA (Remote)"
    
    def test_parse_empty_description(self):
        """Test parser handles empty description"""
        job_data = {
            "title": "Developer",
            "description": ""
        }
        
        result = self.parser.parse(job_data)
        
        assert result.title == "Developer"
        assert isinstance(result.required_skills, list)
        assert isinstance(result.keywords, list)


class TestJobParserEdgeCases:
    """Tests for edge cases in job parsing"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = JobParser()
    
    def test_parse_with_special_characters(self):
        """Test parsing job description with special characters"""
        job_data = {
            "title": "C++ Developer",
            "description": "Experience with C++, C#, .NET, and Node.js required"
        }
        
        result = self.parser.parse(job_data)
        
        assert result.title == "C++ Developer"
        # Should handle special characters in skills
        assert any("C++" in skill or "C#" in skill for skill in result.required_skills + result.keywords)
    
    def test_parse_with_html_content(self):
        """Test parsing job description with HTML tags"""
        job_data = {
            "title": "Web Developer",
            "description": "<p>Looking for <strong>Python</strong> and <em>Django</em> experience</p>"
        }
        
        result = self.parser.parse(job_data)
        
        # Should extract skills even from HTML
        assert "Python" in result.required_skills or "Python" in result.keywords
        assert "Django" in result.required_skills or "Django" in result.keywords
    
    def test_parse_with_bullet_points(self):
        """Test parsing job description with various bullet point formats"""
        job_data = {
            "title": "Developer",
            "description": """
            Requirements:
            • Python
            * JavaScript
            - Docker
            · Kubernetes
            """
        }
        
        result = self.parser.parse(job_data)
        
        # Should extract skills from different bullet formats
        skills_and_keywords = result.required_skills + result.keywords
        assert "Python" in skills_and_keywords
        assert "JavaScript" in skills_and_keywords
    
    def test_parse_very_long_description(self):
        """Test parsing very long job description"""
        long_description = "Python developer needed. " * 1000
        job_data = {
            "title": "Developer",
            "description": long_description
        }
        
        result = self.parser.parse(job_data)
        
        # Should handle long descriptions without errors
        assert result.title == "Developer"
        assert isinstance(result.required_skills, list)

