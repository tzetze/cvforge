#!/usr/bin/env python3
"""
Quick test script to verify verbose selection analysis works.
"""

from core.data_manager import load_cv_data
from core.job.parser import JobDescriptionParser
from core.generation.cv_selector import CVContentSelector
from core.scoring.achievement_scorer import AchievementScorer

# Load sample CV
cv_data = load_cv_data('tests/fixtures/sample_cv.yaml')

# Create a simple job description
job_description = """
Senior Software Engineer position requiring:
- Python programming
- Cloud infrastructure (AWS, Azure)
- Microservices architecture
- Team leadership
- 5+ years experience
"""

# Parse job
parser = JobDescriptionParser()
job_info = parser.parse({'description': job_description})

# Create selector with verbose analysis
scorer = AchievementScorer()
selector = CVContentSelector(scorer)

# Select content with verbose analysis enabled
selected_content = selector.select_content(
    cv_data=cv_data,
    job_requirements=job_info,
    verbose=True
)

# Print results
print("=" * 80)
print("VERBOSE SELECTION ANALYSIS TEST")
print("=" * 80)

if selected_content.selection_analysis:
    analysis = selected_content.selection_analysis
    
    print("\n📊 SUMMARY:")
    print(f"  Total Experiences: {analysis['summary']['total_experiences']}")
    print(f"  Included: {analysis['summary']['included_experiences']}")
    print(f"  Excluded: {analysis['summary']['excluded_experiences']}")
    print(f"  Total Achievements: {analysis['summary']['total_achievements']}")
    print(f"  Selected: {analysis['summary']['selected_achievements']}")
    print(f"  Excluded: {analysis['summary']['excluded_achievements']}")
    print(f"  Avg Selected Score: {analysis['summary']['average_selected_score']:.3f}")
    print(f"  Avg Excluded Score: {analysis['summary']['average_excluded_score']:.3f}")
    
    print("\n⚙️  CONFIGURATION:")
    print(f"  Max achievements per job: {analysis['configuration']['max_achievements_per_job']}")
    print(f"  Min achievement score: {analysis['configuration']['min_achievement_score']}")
    
    print("\n💼 EXPERIENCE ANALYSIS:")
    for exp in analysis['experiences']:
        status = "✅ INCLUDED" if exp['included'] else "❌ EXCLUDED"
        print(f"\n  {status}: {exp['position']} at {exp['company']}")
        print(f"    Reason: {exp['reason']}")
        print(f"    Achievements: {exp['selected_achievements']} selected, {exp['excluded_achievements']} excluded")
        
        if exp['achievements']:
            print(f"    Achievement scores:")
            for ach in exp['achievements'][:3]:  # Show first 3
                status_icon = "✓" if ach['selected'] else "✗"
                print(f"      [{status_icon}] {ach['total_score']:.3f} - {ach['text'][:60]}...")
    
    print("\n" + "=" * 80)
    print("✅ Verbose analysis feature is working!")
    print("=" * 80)
else:
    print("\n❌ ERROR: No selection analysis found!")
    print("The verbose parameter may not be working correctly.")

