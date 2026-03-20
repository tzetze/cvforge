"""
Unit tests for core.generation.cv_selector module
"""
import pytest
from core.generation.cv_selector import CVSelector
from core.generation.achievement_scorer import AchievementScorer
from core.data_manager import load_cv_data
from core.models import JobRequirements


class TestCVSelector:
    """Tests for CVSelector class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.selector = CVSelector()
        self.cv_data = load_cv_data("tests/fixtures/sample_cv.yaml")
    
    def test_select_content_basic(self):
        """Test basic content selection"""
        job_reqs = JobRequirements(
            title="Senior Python Developer",
            company="Tech Corp",
            description="Looking for Python and AWS experience",
            required_skills=["Python", "AWS", "Docker"],
            preferred_skills=["PostgreSQL"],
            keywords=["microservices", "API", "cloud"]
        )
        
        result = self.selector.select_content(
            cv_data=self.cv_data,
            job_requirements=job_reqs,
            max_achievements_per_role=3
        )
        
        assert result is not None
        assert len(result.experiences) > 0
        assert result.personal_info is not None
    
    def test_select_content_filters_by_relevance(self):
        """Test that selector filters achievements by relevance"""
        job_reqs = JobRequirements(
            title="Python Developer",
            description="Python backend development",
            required_skills=["Python", "PostgreSQL"],
            preferred_skills=[],
            keywords=["backend", "API"]
        )
        
        result = self.selector.select_content(
            cv_data=self.cv_data,
            job_requirements=job_reqs,
            max_achievements_per_role=2,
            min_score_threshold=0.3
        )
        
        # Should have selected experiences
        assert len(result.experiences) > 0
        
        # Each experience should have achievements
        for exp in result.experiences:
            assert len(exp.achievements) > 0
            assert len(exp.achievements) <= 2  # Respects max_achievements_per_role
    
    def test_select_content_respects_max_achievements(self):
        """Test that selector respects max achievements per role"""
        job_reqs = JobRequirements(
            title="Software Engineer",
            description="General software development",
            required_skills=["Python"],
            preferred_skills=[],
            keywords=[]
        )
        
        max_achievements = 2
        result = self.selector.select_content(
            cv_data=self.cv_data,
            job_requirements=job_reqs,
            max_achievements_per_role=max_achievements
        )
        
        for exp in result.experiences:
            assert len(exp.achievements) <= max_achievements
    
    def test_select_content_with_high_threshold(self):
        """Test content selection with high relevance threshold"""
        job_reqs = JobRequirements(
            title="DevOps Engineer",
            description="Looking for DevOps expertise",
            required_skills=["Docker", "Kubernetes", "AWS"],
            preferred_skills=["Terraform"],
            keywords=["CI/CD", "automation"]
        )
        
        result = self.selector.select_content(
            cv_data=self.cv_data,
            job_requirements=job_reqs,
            min_score_threshold=0.5  # High threshold
        )
        
        # Should still return some content even with high threshold
        assert result is not None
        assert result.personal_info is not None
    
    def test_select_content_preserves_personal_info(self):
        """Test that personal info is always preserved"""
        job_reqs = JobRequirements(
            title="Any Position",
            description="Any description",
            required_skills=[],
            preferred_skills=[],
            keywords=[]
        )
        
        result = self.selector.select_content(
            cv_data=self.cv_data,
            job_requirements=job_reqs
        )
        
        assert result.personal_info["name"] == self.cv_data.personal.name
        assert result.personal_info["email"] == self.cv_data.personal.email
    
    def test_select_content_includes_skills(self):
        """Test that relevant skills are included"""
        job_reqs = JobRequirements(
            title="Python Developer",
            description="Python development",
            required_skills=["Python", "AWS"],
            preferred_skills=[],
            keywords=[]
        )
        
        result = self.selector.select_content(
            cv_data=self.cv_data,
            job_requirements=job_reqs
        )
        
        assert result.skills is not None
        # Should include technical skills
        assert "technical" in result.skills or len(result.skills) > 0


class TestCVSelectorWithCustomScorer:
    """Tests for CVSelector with custom scorer"""
    
    def test_select_content_with_custom_scorer(self):
        """Test using custom achievement scorer"""
        custom_scorer = AchievementScorer(
            keyword_weight=0.4,
            skill_weight=0.3,
            impact_weight=0.2,
            recency_weight=0.1,
            semantic_weight=0.0
        )
        
        selector = CVSelector(scorer=custom_scorer)
        cv_data = load_cv_data("tests/fixtures/sample_cv.yaml")
        
        job_reqs = JobRequirements(
            title="Python Developer",
            description="Python development",
            required_skills=["Python"],
            preferred_skills=[],
            keywords=["API"]
        )
        
        result = selector.select_content(
            cv_data=cv_data,
            job_requirements=job_reqs
        )
        
        assert result is not None
        assert len(result.experiences) > 0


class TestCVSelectorEdgeCases:
    """Tests for edge cases in CV selection"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.selector = CVSelector()
        self.cv_data = load_cv_data("tests/fixtures/sample_cv.yaml")
    
    def test_select_content_no_matching_skills(self):
        """Test selection when no skills match"""
        job_reqs = JobRequirements(
            title="COBOL Developer",
            description="Looking for COBOL expertise",
            required_skills=["COBOL", "Mainframe"],
            preferred_skills=[],
            keywords=["legacy"]
        )
        
        result = self.selector.select_content(
            cv_data=self.cv_data,
            job_requirements=job_reqs,
            min_score_threshold=0.0  # Low threshold to get some results
        )
        
        # Should still return structure even with no matches
        assert result is not None
        assert result.personal_info is not None
    
    def test_select_content_empty_job_requirements(self):
        """Test selection with minimal job requirements"""
        job_reqs = JobRequirements(
            title="Developer",
            description="",
            required_skills=[],
            preferred_skills=[],
            keywords=[]
        )
        
        result = self.selector.select_content(
            cv_data=self.cv_data,
            job_requirements=job_reqs
        )
        
        assert result is not None
        assert result.personal_info is not None
    
    def test_select_content_zero_max_achievements(self):
        """Test selection with zero max achievements"""
        job_reqs = JobRequirements(
            title="Developer",
            description="Python",
            required_skills=["Python"],
            preferred_skills=[],
            keywords=[]
        )
        
        result = self.selector.select_content(
            cv_data=self.cv_data,
            job_requirements=job_reqs,
            max_achievements_per_role=0
        )
        
        # Should handle gracefully
        assert result is not None

