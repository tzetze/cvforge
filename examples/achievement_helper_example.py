"""
Example: Achievement Memory Helper

Demonstrates the interactive achievement documentation tool.

Usage:
    python examples/achievement_helper_example.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.helpers import AchievementMemoryHelper, interactive_achievement_session
from core.llm.factory import LLMManager
import yaml


def example_with_llm():
    """Example using LLM for enhanced questioning."""
    print("=" * 60)
    print("Achievement Memory Helper - With LLM")
    print("=" * 60)
    
    # Initialize LLM
    try:
        settings_path = project_root / "config" / "settings.yaml"
        with open(settings_path) as f:
            settings = yaml.safe_load(f)
        
        llm_manager = LLMManager(settings)
        llm = llm_manager.get_provider("default")
        print("✓ LLM initialized\n")
    except Exception as e:
        print(f"⚠ Could not initialize LLM: {e}")
        print("Continuing without LLM support\n")
        llm = None
    
    # Run interactive session
    achievement = interactive_achievement_session(
        role="Senior Software Engineer",
        company="Tech Corp",
        llm_provider=llm
    )
    
    print("\n" + "=" * 60)
    print("Achievement documented successfully!")
    print("=" * 60)
    print("\nYou can now add this to your CV data YAML file.")


def example_programmatic():
    """Example using the helper programmatically."""
    print("=" * 60)
    print("Achievement Memory Helper - Programmatic Usage")
    print("=" * 60)
    
    helper = AchievementMemoryHelper()
    
    # Start session
    draft = helper.start_session(
        role="Data Scientist",
        company="Analytics Inc"
    )
    
    # Simulate answering questions
    print("\nSimulating achievement documentation...\n")
    
    # Question 1: Main accomplishment
    helper.process_answer(
        draft,
        "main",
        "Built a machine learning model to predict customer churn"
    )
    
    # Question 2: Challenge
    helper.process_answer(
        draft,
        "challenge",
        "Had to work with imbalanced dataset and achieve 85% accuracy"
    )
    
    # Question 3: Result
    helper.process_answer(
        draft,
        "result",
        "Reduced customer churn by 30% and saved company $2M annually"
    )
    
    # Check what's missing
    suggestions = helper.get_completion_suggestions(draft)
    if suggestions:
        print("Suggestions for improvement:")
        for sugg in suggestions:
            print(f"  - {sugg}")
        print()
    
    # Finalize achievement
    achievement = helper.finalize_achievement(draft, use_llm=False)
    
    print("Final Achievement:")
    print(f"  Text: {achievement.text}")
    print(f"  Skills: {', '.join(achievement.skills) if achievement.skills else 'None'}")
    print(f"  Metrics: {', '.join(achievement.metrics) if achievement.metrics else 'None'}")
    print(f"  Impact: {achievement.impact}")
    
    print("\n" + "=" * 60)
    print("Achievement created programmatically!")
    print("=" * 60)


def example_question_flow():
    """Example showing the question flow."""
    print("=" * 60)
    print("Achievement Memory Helper - Question Flow")
    print("=" * 60)
    
    helper = AchievementMemoryHelper()
    
    # Get initial questions
    print("\nInitial Questions:")
    questions = helper.get_initial_questions()
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. {q.text}")
        if q.examples:
            print(f"   Examples: {', '.join(q.examples)}")
    
    # Simulate an answer and get follow-ups
    print("\n" + "-" * 60)
    print("After answering: 'Led migration to microservices architecture'")
    print("-" * 60)
    
    draft = helper.start_session("DevOps Engineer", "Cloud Systems")
    follow_ups = helper.get_follow_up_questions(
        draft,
        "Led migration to microservices architecture",
        "result"
    )
    
    print("\nFollow-up Questions:")
    for i, q in enumerate(follow_ups, 1):
        print(f"\n{i}. {q.text}")
    
    print("\n" + "=" * 60)


def main():
    """Run examples."""
    print("\nChoose an example:")
    print("1. Interactive session (with LLM if available)")
    print("2. Programmatic usage")
    print("3. Question flow demonstration")
    print("4. Run all examples")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        example_with_llm()
    elif choice == "2":
        example_programmatic()
    elif choice == "3":
        example_question_flow()
    elif choice == "4":
        example_question_flow()
        print("\n\n")
        example_programmatic()
        print("\n\n")
        example_with_llm()
    else:
        print("Invalid choice. Running question flow demo...")
        example_question_flow()


if __name__ == "__main__":
    main()

