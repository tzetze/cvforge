"""
Test cases for the achievement scoring system.
"""

import pytest
from datetime import datetime

from core.models import Achievement, Experience, PersonalInfo, CVData, ImpactLevel
from core.job.parser import JobRequirements
from core.scoring.achievement_scorer import AchievementScorer, ScoredAchievement


@pytest.fixture
def sample_achievement_high():
    """Create a high-impact achievement."""
    return Achievement(
        text="Built microservices architecture using Python and Kubernetes, reducing deployment time by 80%",
        skills=["Python", "Kubernetes", "Docker", "Microservices"],
        impact=ImpactLevel.HIGH,
        metrics={"deployment_time": "80% reduction"},
        keywords=["architecture", "deployment", "scalability"]
    )


@pytest.fixture
def sample_achievement_medium():
    """Create a medium-impact achievement."""
    return Achievement(
        text="Implemented REST API with Node.js and MongoDB for user management",
        skills=["Node.js", "MongoDB", "REST API", "JavaScript"],
        impact=ImpactLevel.MEDIUM,
        metrics={"users": "10K+"},
    )


@pytest.fixture
def sample_achievement_low():
    """Create a low-impact achievement."""
    return Achievement(
        text="Fixed bugs in legacy PHP codebase",
        skills=["PHP", "Debugging"],
        impact=ImpactLevel.LOW,
    )


@pytest.fixture
def recent_experience(sample_achievement_high):
    """Create a recent experience (current job)."""
    return Experience(
        company="TechCorp",
        position="Senior Engineer",
        start_date="2023-01",
        end_date="present",
        achievements=[sample_achievement_high]
    )


@pytest.fixture
def old_experience(sample_achievement_low):
    """Create an old experience (5 years ago)."""
    return Experience(
        company="OldCorp",
        position="Junior Developer",
        start_date="2017-01",
        end_date="2019-12",
        achievements=[sample_achievement_low]
    )


@pytest.fixture
def job_requirements():
    """Create sample job requirements."""
    return JobRequirements(
        title="Senior Backend Engineer",
        company="AwesomeCo",
        required_skills=["Python", "Kubernetes", "Docker", "Microservices", "AWS"],
        preferred_skills=["Go", "Terraform"],
        technologies={"python", "kubernetes", "docker", "aws", "postgresql"},
        keywords={"architecture", "scalability", "deployment", "backend", "api"},
        action_verbs={"build", "design", "implement", "optimize"},
        years_experience=5,
    )


@pytest.fixture
def scorer():
    """Create a scorer with default weights."""
    return AchievementScorer()


class TestAchievementScorer:
    """Test the AchievementScorer class."""
    
    def test_scorer_initialization(self):
        """Test scorer initialization with default weights."""
        scorer = AchievementScorer()
        assert scorer.weights["keyword_match"] == 0.30
        assert scorer.weights["skill_match"] == 0.25
        assert scorer.weights["impact_level"] == 0.20
        assert scorer.weights["recency"] == 0.15
        assert scorer.weights["semantic_similarity"] == 0.10
        
        # Check weights sum to 1.0
        assert abs(sum(scorer.weights.values()) - 1.0) < 0.01
    
    def test_scorer_custom_weights(self):
        """Test scorer with custom weights."""
        custom_weights = {
            "keyword_match": 0.40,
            "skill_match": 0.30,
            "impact_level": 0.15,
            "recency": 0.10,
            "semantic_similarity": 0.05,
        }
        scorer = AchievementScorer(weights=custom_weights)
        assert scorer.weights == custom_weights
    
    def test_scorer_invalid_weights(self):
        """Test that invalid weights raise an error."""
        invalid_weights = {
            "keyword_match": 0.50,
            "skill_match": 0.30,
            "impact_level": 0.10,
            "recency": 0.10,  # Total = 1.05, invalid
            "semantic_similarity": 0.05,
        }
        with pytest.raises(ValueError, match="must sum to 1.0"):
            AchievementScorer(weights=invalid_weights)
    
    def test_score_impact_level(self, scorer, sample_achievement_high, 
                                sample_achievement_medium, sample_achievement_low):
        """Test impact level scoring."""
        assert scorer._score_impact_level(sample_achievement_high) == 1.0
        assert scorer._score_impact_level(sample_achievement_medium) == 0.6
        assert scorer._score_impact_level(sample_achievement_low) == 0.3
    
    def test_score_recency_current_job(self, scorer, recent_experience):
        """Test recency scoring for current job."""
        score = scorer._score_recency(recent_experience)
        assert score == 1.0
    
    def test_score_recency_old_job(self, scorer, old_experience):
        """Test recency scoring for old job."""
        score = scorer._score_recency(old_experience)
        # 5 years ago should give a score around 0.5
        assert 0.4 <= score <= 0.6
    
    def test_score_skill_match_perfect(self, scorer, sample_achievement_high, job_requirements):
        """Test skill matching with perfect match."""
        score = scorer._score_skill_match(sample_achievement_high, job_requirements)
        # Should have high score due to Python, Kubernetes, Docker, Microservices match
        assert score > 0.7
    
    def test_score_skill_match_partial(self, scorer, sample_achievement_medium, job_requirements):
        """Test skill matching with partial match."""
        score = scorer._score_skill_match(sample_achievement_medium, job_requirements)
        # Should have lower score as Node.js and MongoDB are not in requirements
        assert score < 0.5
    
    def test_score_skill_match_no_match(self, scorer, sample_achievement_low, job_requirements):
        """Test skill matching with no match."""
        score = scorer._score_skill_match(sample_achievement_low, job_requirements)
        # PHP is not in requirements
        assert score < 0.3
    
    def test_score_keyword_match(self, scorer, sample_achievement_high, job_requirements):
        """Test keyword matching."""
        score = scorer._score_keyword_match(sample_achievement_high, job_requirements)
        # Should match keywords like "architecture", "deployment"
        assert score > 0.3
    
    def test_score_achievement_complete(self, scorer, sample_achievement_high, 
                                       recent_experience, job_requirements):
        """Test complete achievement scoring."""
        scored = scorer.score_achievement(
            sample_achievement_high,
            recent_experience,
            job_requirements
        )
        
        assert isinstance(scored, ScoredAchievement)
        assert scored.achievement == sample_achievement_high
        assert scored.experience == recent_experience
        assert 0.0 <= scored.total_score <= 1.0
        
        # Check breakdown exists
        assert "keyword_match" in scored.score_breakdown
        assert "skill_match" in scored.score_breakdown
        assert "impact_level" in scored.score_breakdown
        assert "recency" in scored.score_breakdown
        assert "semantic_similarity" in scored.score_breakdown
        
        # High impact + recent + good skill match should give high score
        assert scored.total_score > 0.6
    
    def test_score_achievements_sorting(self, scorer, sample_achievement_high,
                                       sample_achievement_medium, sample_achievement_low,
                                       recent_experience, job_requirements):
        """Test that achievements are sorted by score."""
        # Create CV data
        recent_experience.achievements = [
            sample_achievement_low,
            sample_achievement_high,
            sample_achievement_medium,
        ]
        
        cv_data = CVData(
            personal=PersonalInfo(name="Test User", email="test@example.com"),
            experience=[recent_experience]
        )
        
        scored = scorer.score_achievements(cv_data, job_requirements)
        
        assert len(scored) == 3
        # Should be sorted highest to lowest
        assert scored[0].total_score >= scored[1].total_score
        assert scored[1].total_score >= scored[2].total_score
        
        # High impact achievement should be first
        assert scored[0].achievement == sample_achievement_high
    
    def test_filter_top_achievements_by_score(self, scorer, sample_achievement_high,
                                             sample_achievement_medium, sample_achievement_low,
                                             recent_experience, job_requirements):
        """Test filtering achievements by minimum score."""
        recent_experience.achievements = [
            sample_achievement_high,
            sample_achievement_medium,
            sample_achievement_low,
        ]
        
        cv_data = CVData(
            personal=PersonalInfo(name="Test User", email="test@example.com"),
            experience=[recent_experience]
        )
        
        scored = scorer.score_achievements(cv_data, job_requirements)
        
        # Filter with high threshold
        filtered = scorer.filter_top_achievements(scored, min_score=0.6)
        
        # Should only include high-scoring achievements
        assert len(filtered) <= len(scored)
        assert all(sa.total_score >= 0.6 for sa in filtered)
    
    def test_filter_top_achievements_per_job(self, scorer, recent_experience, job_requirements):
        """Test limiting achievements per job."""
        # Create 10 achievements
        achievements = []
        for i in range(10):
            achievements.append(Achievement(
                text=f"Achievement {i} with Python and Kubernetes",
                skills=["Python", "Kubernetes"],
                impact=ImpactLevel.HIGH if i < 5 else ImpactLevel.MEDIUM,
            ))
        
        recent_experience.achievements = achievements
        
        cv_data = CVData(
            personal=PersonalInfo(name="Test User", email="test@example.com"),
            experience=[recent_experience]
        )
        
        scored = scorer.score_achievements(cv_data, job_requirements)
        
        # Filter to max 3 per job
        filtered = scorer.filter_top_achievements(scored, max_per_job=3, min_score=0.0)
        
        assert len(filtered) <= 3
    
    def test_get_score_summary(self, scorer, sample_achievement_high,
                               sample_achievement_medium, sample_achievement_low,
                               recent_experience, job_requirements):
        """Test score summary statistics."""
        recent_experience.achievements = [
            sample_achievement_high,
            sample_achievement_medium,
            sample_achievement_low,
        ]
        
        cv_data = CVData(
            personal=PersonalInfo(name="Test User", email="test@example.com"),
            experience=[recent_experience]
        )
        
        scored = scorer.score_achievements(cv_data, job_requirements)
        summary = scorer.get_score_summary(scored)
        
        assert summary["total_achievements"] == 3
        assert 0.0 <= summary["average_score"] <= 1.0
        assert 0.0 <= summary["max_score"] <= 1.0
        assert 0.0 <= summary["min_score"] <= 1.0
        assert summary["max_score"] >= summary["average_score"]
        assert summary["average_score"] >= summary["min_score"]
        
        # Check distribution
        dist = summary["score_distribution"]
        assert "high (>0.7)" in dist
        assert "medium (0.4-0.7)" in dist
        assert "low (<0.4)" in dist
        assert sum(dist.values()) == 3
    
    def test_get_score_summary_empty(self, scorer):
        """Test score summary with no achievements."""
        summary = scorer.get_score_summary([])
        
        assert summary["total_achievements"] == 0
        assert summary["average_score"] == 0.0
        assert summary["max_score"] == 0.0
        assert summary["min_score"] == 0.0
    
    def test_scored_achievement_sorting(self, sample_achievement_high, 
                                       sample_achievement_low, recent_experience):
        """Test that ScoredAchievement objects can be sorted."""
        scored_high = ScoredAchievement(
            achievement=sample_achievement_high,
            experience=recent_experience,
            total_score=0.8,
            score_breakdown={}
        )
        
        scored_low = ScoredAchievement(
            achievement=sample_achievement_low,
            experience=recent_experience,
            total_score=0.3,
            score_breakdown={}
        )
        
        # Test sorting
        sorted_list = sorted([scored_low, scored_high], reverse=True)
        assert sorted_list[0] == scored_high
        assert sorted_list[1] == scored_low


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

