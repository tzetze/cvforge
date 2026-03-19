#!/usr/bin/env python3
"""
Quick test script to verify data manager and models work correctly.
"""

from core.data_manager import DataManager
from core.models import CVData, Settings

def test_load_example_cv():
    """Test loading the example CV data."""
    print("Testing CV data loading...")
    manager = DataManager(cv_data_path="config/cv_data.example.yaml")
    
    try:
        cv_data = manager.load_cv_data()
        print(f"✓ Successfully loaded CV data for: {cv_data.personal.name}")
        print(f"  - Email: {cv_data.personal.email}")
        print(f"  - Total experiences: {len(cv_data.experience)}")
        print(f"  - Total achievements: {cv_data.get_total_achievements()}")
        print(f"  - Total skills: {len(cv_data.get_all_skills())}")
        
        # Test summary
        summary = manager.get_cv_summary()
        print(f"\nCV Summary:")
        for key, value in summary.items():
            print(f"  - {key}: {value}")
        
        return True
    except Exception as e:
        print(f"✗ Error loading CV data: {e}")
        return False

def test_load_example_settings():
    """Test loading the example settings."""
    print("\n\nTesting settings loading...")
    manager = DataManager(settings_path="config/settings.example.yaml")
    
    try:
        settings = manager.load_settings()
        print(f"✓ Successfully loaded settings")
        print(f"  - Default LLM provider: {settings.llm.default_provider}")
        print(f"  - Number of providers: {len(settings.llm.providers)}")
        print(f"  - Providers: {', '.join(settings.llm.providers.keys())}")
        
        # Test scoring weights
        print(f"\nScoring weights:")
        print(f"  - Keyword match: {settings.scoring.keyword_match}")
        print(f"  - Skill match: {settings.scoring.skill_match}")
        print(f"  - Impact level: {settings.scoring.impact_level}")
        print(f"  - Recency: {settings.scoring.recency}")
        print(f"  - Semantic similarity: {settings.scoring.semantic_similarity}")
        
        return True
    except Exception as e:
        print(f"✗ Error loading settings: {e}")
        return False

def test_validation():
    """Test data validation."""
    print("\n\nTesting validation...")
    manager = DataManager()
    
    # Test invalid CV data
    invalid_cv = {
        "personal": {
            "name": "Test",
            "email": "invalid-email"  # Invalid email
        },
        "experience": []  # Empty experience (should fail)
    }
    
    is_valid, error = manager.validate_cv_data(invalid_cv)
    if not is_valid:
        print(f"✓ Correctly rejected invalid CV data")
        print(f"  Error: {error[:100]}...")
    else:
        print(f"✗ Failed to reject invalid CV data")
        return False
    
    # Test valid CV data
    valid_cv = {
        "personal": {
            "name": "Test User",
            "email": "test@example.com"
        },
        "experience": [
            {
                "company": "Test Corp",
                "position": "Developer",
                "start_date": "2020-01",
                "achievements": [
                    {
                        "text": "Built amazing features",
                        "skills": ["Python", "JavaScript"],
                        "impact": "high"
                    }
                ]
            }
        ]
    }
    
    is_valid, error = manager.validate_cv_data(valid_cv)
    if is_valid:
        print(f"✓ Correctly accepted valid CV data")
    else:
        print(f"✗ Failed to accept valid CV data: {error}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("CVForge Data Manager Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(("Load Example CV", test_load_example_cv()))
    results.append(("Load Example Settings", test_load_example_settings()))
    results.append(("Validation", test_validation()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("=" * 60)
    if all_passed:
        print("All tests passed! ✓")
    else:
        print("Some tests failed! ✗")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
