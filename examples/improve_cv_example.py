"""
Example: CV Improvement Suggestions

Demonstrates how to use LLM to analyze CV and get improvement suggestions.

Usage:
    python examples/improve_cv_example.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.data_manager import load_cv_data
from core.validation import validate_cv_data
from core.improvement import CVImprover, analyze_and_improve_cv
from core.llm.factory import LLMManager


def main():
    """Analyze CV and get improvement suggestions."""
    
    print("=" * 60)
    print("CV Improvement Suggestions Example")
    print("=" * 60)
    
    # Load CV data
    print("\n[1/4] Loading CV data...")
    cv_data_path = project_root / "config" / "cv_data.yaml"
    
    if not cv_data_path.exists():
        print(f"Error: CV data file not found: {cv_data_path}")
        print("\nPlease create your CV data file:")
        print(f"  cp config/cv_data.example.yaml config/cv_data.yaml")
        print(f"  # Edit config/cv_data.yaml with your information")
        return
    
    cv_data = load_cv_data(str(cv_data_path))
    print(f"✓ Loaded CV for {cv_data.personal_info.name}")
    
    # Validate CV (optional but recommended)
    print("\n[2/4] Validating CV data...")
    validation_report = validate_cv_data(cv_data)
    print(f"✓ Validation complete: {validation_report.error_count} errors, {validation_report.warning_count} warnings")
    
    # Initialize LLM
    print("\n[3/4] Initializing LLM...")
    try:
        import yaml
        settings_path = project_root / "config" / "settings.yaml"
        
        with open(settings_path) as f:
            settings = yaml.safe_load(f)
        
        llm_manager = LLMManager(settings)
        llm = llm_manager.get_provider("default")
        print("✓ LLM initialized")
    except Exception as e:
        print(f"Error: Could not initialize LLM: {e}")
        print("\nPlease configure your LLM settings:")
        print("  1. Copy config/settings.example.yaml to config/settings.yaml")
        print("  2. Copy .env.example to .env")
        print("  3. Add your API keys to .env")
        return
    
    # Analyze CV and get suggestions
    print("\n[4/4] Analyzing CV and generating suggestions...")
    print("(This may take a minute...)")
    
    improver = CVImprover(llm)
    report = improver.analyze_cv(cv_data, validation_report)
    
    # Display report
    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)
    
    # Show specific examples
    if report.suggestions:
        print("\nExample: Improve a specific achievement")
        print("-" * 60)
        
        # Get first achievement
        first_exp = cv_data.experiences[0]
        first_ach = first_exp.achievements[0]
        
        print(f"\nOriginal achievement:")
        print(f"  {first_ach.text}")
        
        improved = improver.improve_achievement(
            first_ach.text,
            context={
                "role": first_exp.position,
                "company": first_exp.company
            }
        )
        
        print(f"\nImproved version:")
        print(f"  {improved}")
    
    if cv_data.summary:
        print("\n" + "-" * 60)
        print("Example: Improve professional summary")
        print("-" * 60)
        
        print(f"\nOriginal summary:")
        print(f"  {cv_data.summary}")
        
        improved_summary = improver.improve_summary(cv_data.summary)
        
        print(f"\nImproved version:")
        print(f"  {improved_summary}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)
    print(f"\nTotal suggestions: {len(report.suggestions)}")
    print(f"High priority: {len(report.get_high_priority())}")
    print(f"Strengths identified: {len(report.strengths)}")
    print(f"Areas for improvement: {len(report.areas_for_improvement)}")
    
    print("\nNext steps:")
    print("  1. Review high-priority suggestions")
    print("  2. Update your cv_data.yaml with improvements")
    print("  3. Re-validate to check progress")
    print("  4. Generate updated CV PDF")


if __name__ == "__main__":
    main()

