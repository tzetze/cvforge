# Verbose Selection Analysis

## Overview

The CV selector now includes a verbose analysis mode that provides detailed insights into how experiences and achievements are selected for a specific job. This helps users understand the selection process and fine-tune their CV or settings.

## Features

### 1. Experience-Level Analysis

For each experience in your CV, the analysis shows:
- **Inclusion Status**: Whether the experience was included or excluded
- **Reason**: Why the experience was included/excluded
- **Achievement Counts**: How many achievements were selected vs excluded
- **Date Range**: When you worked at that position

### 2. Achievement-Level Scoring

For each achievement, you can see:
- **Selection Status**: Whether it was selected (✓) or excluded (✗)
- **Total Score**: Overall relevance score (0.0 to 1.0)
- **Score Breakdown**: Individual scoring components:
  - `keyword_score`: Match with job keywords
  - `skill_score`: Match with required skills
  - `impact_score`: Impact level of the achievement
  - `recency_score`: How recent the experience is
  - `semantic_score`: Semantic similarity (if LLM is used)
- **Skills**: Skills mentioned in the achievement
- **Impact Level**: The impact level (low, medium, high, transformative)
- **Metrics**: Quantifiable metrics in the achievement

### 3. Summary Statistics

The analysis provides overall statistics:
- Total experiences vs included/excluded
- Total achievements vs selected/excluded
- Average score of selected achievements
- Average score of excluded achievements
- Configuration settings used

## How to Use

### In Code

```python
from core.generation.cv_selector import CVContentSelector
from core.scoring.achievement_scorer import AchievementScorer

scorer = AchievementScorer()
selector = CVContentSelector(scorer)

# Enable verbose analysis
selected_content = selector.select_content(
    cv_data=cv_data,
    job_requirements=job_info,
    verbose=True  # Enable verbose mode
)

# Access the analysis
if selected_content.selection_analysis:
    analysis = selected_content.selection_analysis
    
    # Summary statistics
    print(f"Included: {analysis['summary']['included_experiences']}")
    print(f"Excluded: {analysis['summary']['excluded_experiences']}")
    
    # Experience-by-experience details
    for exp in analysis['experiences']:
        print(f"{exp['position']} at {exp['company']}")
        print(f"Status: {exp['included']}")
        print(f"Reason: {exp['reason']}")
        
        # Achievement details
        for ach in exp['achievements']:
            print(f"  Score: {ach['total_score']:.3f}")
            print(f"  Text: {ach['text']}")
            print(f"  Breakdown: {ach['score_breakdown']}")
```

### In Web Interface

When you analyze a job in the web interface, the verbose analysis is automatically enabled. You'll see:

1. **Summary Card**: Overall statistics about selection
2. **Experience Cards**: Each experience with color-coded status
   - Green border = Included
   - Red border = Excluded
3. **Expandable Achievement Tables**: Click to see all achievements with scores

## Understanding the Selection Rules

### Why Experiences Are Excluded

An experience may be excluded for these reasons:

1. **No achievements defined**: The experience has no achievements listed
2. **All achievements below threshold**: All achievements scored below the minimum threshold (default: 0.3)
3. **Not in top achievements**: Achievements didn't make it into the top N selected (default: 5 total)

### Why Achievements Are Excluded

An achievement may be excluded because:

1. **Low relevance score**: Score below minimum threshold (default: 0.3)
2. **Not in top N**: Other achievements scored higher and filled the quota
3. **Missing key skills**: Doesn't mention skills required by the job
4. **Low impact**: Lacks measurable impact or metrics

## Configuration Options

You can adjust the selection behavior:

```python
config = {
    "max_achievements_per_job": 5,      # Max total achievements to select
    "min_achievement_score": 0.3,       # Minimum score threshold (0.0-1.0)
    "include_volunteer": True,          # Include volunteer work
    "include_projects": True,           # Include projects
    "include_publications": True,       # Include publications
    "include_awards": True,             # Include awards
    "max_pages": 2                      # Target page count
}

selector = CVContentSelector(scorer, config=config)
```

### Tuning Tips

**To include more experiences:**
- Lower `min_achievement_score` (e.g., 0.2 instead of 0.3)
- Increase `max_achievements_per_job` (e.g., 8 instead of 5)

**To be more selective:**
- Raise `min_achievement_score` (e.g., 0.4 or 0.5)
- Decrease `max_achievements_per_job` (e.g., 3 instead of 5)

**To improve scores:**
- Add relevant skills to achievements
- Include quantifiable metrics
- Use keywords from the job description
- Emphasize impact and results

## Score Breakdown Components

### Keyword Score (30% weight)
Measures how many job keywords appear in the achievement text.

### Skill Score (25% weight)
Measures overlap between achievement skills and required job skills.

### Impact Score (20% weight)
Based on the impact level:
- Low: 0.25
- Medium: 0.50
- High: 0.75
- Transformative: 1.00

### Recency Score (15% weight)
More recent experiences score higher:
- Last 2 years: 1.00
- 2-5 years: 0.75
- 5-10 years: 0.50
- 10+ years: 0.25

### Semantic Score (10% weight)
If LLM is available, measures semantic similarity between achievement and job description.

## Example Output

```
📊 SUMMARY:
  Total Experiences: 4
  Included: 2
  Excluded: 2
  Total Achievements: 15
  Selected: 5
  Excluded: 10
  Avg Selected Score: 0.650
  Avg Excluded Score: 0.245

💼 EXPERIENCE ANALYSIS:

✅ INCLUDED: Senior Software Engineer at TechCorp
  Reason: Included: 3 achievement(s) met relevance threshold
  Achievements: 3 selected, 2 excluded
  
  [✓] 0.800 - Architected microservices migration...
      keyword_score: 0.850
      skill_score: 0.900
      impact_score: 0.750
      recency_score: 1.000
      
  [✗] 0.280 - Participated in code reviews...
      keyword_score: 0.200
      skill_score: 0.300
      impact_score: 0.250
      recency_score: 1.000

❌ EXCLUDED: Junior Developer at StartupXYZ
  Reason: Excluded: All achievements below threshold (highest: 0.285, min: 0.300)
```

## Benefits

1. **Transparency**: Understand exactly why content was selected or excluded
2. **Optimization**: Identify which achievements need improvement
3. **Fine-tuning**: Adjust settings based on actual score distributions
4. **Quality Control**: Verify the selection logic is working as expected
5. **Learning**: Understand what makes achievements relevant to specific jobs

## Related Documentation

- [Achievement Scoring System](./achievement_scoring.md)
- [CV Selection Process](./cv_selection.md)
- [Job Analysis](./job_analysis.md)