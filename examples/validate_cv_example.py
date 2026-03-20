"""
Example: CV Data Validation

Demonstrates how to validate CV data for completeness and quality.

Usage:
    python examples/validate_cv_example.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.data_manager import load_cv_data
from core.validation import CVValidator, validate_cv_data


def main():
    """Validate CV data and display report."""
    
    print("=" * 60)
    print("CV Data Validation Example")
    print("=" * 60)
    
    # Load CV data
    print("\n[1/2] Loading CV data...")
    cv_data_path = project_root / "config" / "cv_data.yaml"
    
    if not cv_data_path.exists():
        print(f"Error: CV data file not found: {cv_data_path}")
        print("\nPlease create your CV data file:")
        print(f"  cp config/cv_data.example.yaml config/cv_data.yaml")
        print(f"  # Edit config/cv_data.yaml with your information")
        return
    
    cv_data = load_cv_data(str(cv_data_path))
    print(f"✓ Loaded CV for {cv_data.personal.name}")
    
    # Validate CV data
    print("\n[2/2] Validating CV data...")
    print()
    
    # Option 1: Use convenience function with default settings
    report = validate_cv_data(cv_data)
    
    # Option 2: Use custom validator with specific thresholds
    # validator = CVValidator(
    #     min_experiences=2,
    #     min_achievements_per_role=3,
    #     min_achievement_length=40,
    #     max_achievement_length=180,
    #     min_summary_length=120,
    #     max_summary_length=400
    # )
    # report = validator.validate(cv_data)
    
    # Display report
    print(report)
    
    # Show summary
    print("=" * 60)
    if report.is_valid:
        print("✓ CV data is valid and ready for generation!")
    else:
        print("✗ CV data has issues that should be addressed")
    print("=" * 60)
    
    # Show breakdown by severity
    if report.error_count > 0:
        print(f"\nErrors ({report.error_count}):")
        for issue in report.get_issues_by_severity("error"):
            print(f"  - {issue.message}")
            if issue.suggestion:
                print(f"    → {issue.suggestion}")
    
    if report.warning_count > 0:
        print(f"\nWarnings ({report.warning_count}):")
        for issue in report.get_issues_by_severity("warning"):
            print(f"  - {issue.message}")
            if issue.suggestion:
                print(f"    → {issue.suggestion}")
    
    if report.info_count > 0:
        print(f"\nSuggestions ({report.info_count}):")
        for issue in report.get_issues_by_severity("info"):
            print(f"  - {issue.message}")
            if issue.suggestion:
                print(f"    → {issue.suggestion}")
    
    # Export report to JSON (optional)
    print("\n" + "=" * 60)
    print("Export Options:")
    print("  - JSON: report.to_dict()")
    print("  - String: str(report)")
    print("=" * 60)


if __name__ == "__main__":
    main()
