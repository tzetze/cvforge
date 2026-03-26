# Scoring Algorithm Improvement Plan

## Current Issues

### 1. Low Keyword/Skill Match Scores (Often 0%)
**Root Causes:**
- **Exact matching only** - "JavaScript" won't match "JS" or "javascript"
- **No fuzzy matching** - "developed" won't match "development" or "developer"
- **Case sensitivity issues** - Already lowercased but may have edge cases
- **Strict intersection logic** - Requires exact word boundaries
- **No synonym recognition** - "Python" won't match "Python3" or "Python 3.x"

### 2. Redundant Metrics
- **Keyword match (30%)** and **Skill match (25%)** overlap significantly
- Both essentially measure term matching, just from different sources
- Combined weight of 55% for similar functionality

## Proposed Solution: LLM-Driven Scoring (RECOMMENDED)

### Why LLM-Based Scoring?

**Advantages:**
- ✅ **Semantic understanding** - Understands context, not just keywords
- ✅ **Handles variations** - Automatically recognizes "JS" = "JavaScript"
- ✅ **No dictionary maintenance** - No need for synonym lists
- ✅ **Contextual relevance** - Understands if "Python" means programming or snake
- ✅ **Simpler codebase** - Replace complex matching logic with single LLM call
- ✅ **Better accuracy** - LLM can reason about relevance holistically

**Disadvantages:**
- ⚠️ **Cost** - API calls for each achievement (mitigated by batch processing)
- ⚠️ **Latency** - Slower than rule-based (mitigated by async/parallel calls)
- ⚠️ **Consistency** - May vary slightly between runs (use temperature=0)

### LLM Scoring Architecture

```python
def llm_score_achievement(
    achievement: Achievement,
    job_requirements: JobRequirements,
    job_description: str,
    llm: LLMProvider
) -> float:
    """
    Use LLM to score achievement relevance.
    
    Returns: Float between 0.0 and 1.0
    """
    prompt = f"""Score how relevant this achievement is to the job requirements.

Job Requirements:
- Title: {job_requirements.title}
- Required Skills: {', '.join(job_requirements.required_skills[:10])}
- Preferred Skills: {', '.join(job_requirements.preferred_skills[:10])}
- Key Responsibilities: {job_description[:500]}

Achievement:
Text: {achievement.text}
Skills: {', '.join(achievement.skills)}
Impact: {achievement.impact.value}

Instructions:
1. Consider semantic similarity, not just keyword matching
2. Recognize abbreviations and variations (e.g., "JS" = "JavaScript")
3. Evaluate if the achievement demonstrates relevant experience
4. Consider the impact level and quantifiable results
5. Output ONLY a single float between 0.0 and 1.0

Score (0.0-1.0):"""

    response = llm.generate(prompt, temperature=0.0, max_tokens=10)
    
    try:
        score = float(response.content.strip())
        return max(0.0, min(1.0, score))  # Clamp to 0-1
    except ValueError:
        return 0.5  # Fallback to neutral score
```

### Batch Processing for Efficiency

```python
def llm_score_achievements_batch(
    achievements: List[Achievement],
    job_requirements: JobRequirements,
    job_description: str,
    llm: LLMProvider
) -> List[float]:
    """
    Score multiple achievements in a single LLM call.
    
    More efficient than individual calls.
    """
    achievements_text = "\n".join([
        f"{i+1}. {ach.text} (Skills: {', '.join(ach.skills)})"
        for i, ach in enumerate(achievements)
    ])
    
    prompt = f"""Score each achievement's relevance to this job (0.0-1.0).

Job: {job_requirements.title}
Required Skills: {', '.join(job_requirements.required_skills[:10])}

Achievements:
{achievements_text}

Output format (one score per line):
1. 0.85
2. 0.62
3. 0.91
...

Scores:"""

    response = llm.generate(prompt, temperature=0.0, max_tokens=len(achievements) * 10)
    
    # Parse scores
    scores = []
    for line in response.content.strip().split('\n'):
        try:
            # Extract number from "1. 0.85" format
            score = float(line.split('.')[-1].strip())
            scores.append(max(0.0, min(1.0, score)))
        except (ValueError, IndexError):
            scores.append(0.5)
    
    # Ensure we have enough scores
    while len(scores) < len(achievements):
        scores.append(0.5)
    
    return scores[:len(achievements)]
```

### Hybrid Approach (Best of Both Worlds)

Combine LLM scoring with fast rule-based metrics:

```python
weights = {
    "llm_relevance": 0.50,      # LLM semantic scoring
    "impact_level": 0.25,       # Fast rule-based
    "recency": 0.15,            # Fast rule-based
    "quantifiable": 0.10,       # Fast rule-based (has numbers?)
}
```

**Benefits:**
- LLM handles the hard part (semantic relevance)
- Rule-based handles objective metrics (impact, recency)
- Faster than pure LLM approach
- More accurate than pure rule-based

## Alternative: Traditional Improvements (Fallback)

### Phase 1: Enhanced Matching Logic (High Priority)

#### 1.1 Fuzzy String Matching
```python
# Use difflib or rapidfuzz for similarity matching
from difflib import SequenceMatcher

def fuzzy_match(term1: str, term2: str, threshold: float = 0.85) -> bool:
    """Return True if terms are similar enough."""
    ratio = SequenceMatcher(None, term1.lower(), term2.lower()).ratio()
    return ratio >= threshold
```

**Benefits:**
- Matches "JavaScript" with "Javascript" or "javascript"
- Matches "Python" with "Python3"
- Handles typos and variations

#### 1.2 Stemming/Lemmatization
```python
# Use NLTK or spaCy for word normalization
from nltk.stem import PorterStemmer

stemmer = PorterStemmer()

def normalize_term(term: str) -> str:
    """Reduce term to root form."""
    return stemmer.stem(term.lower())
```

**Benefits:**
- "developed", "developer", "development" → "develop"
- "managed", "managing", "manager" → "manag"
- Increases match likelihood significantly

#### 1.3 Synonym/Abbreviation Dictionary
```python
TECH_SYNONYMS = {
    'js': ['javascript', 'ecmascript'],
    'ts': ['typescript'],
    'py': ['python'],
    'k8s': ['kubernetes'],
    'ci/cd': ['continuous integration', 'continuous deployment'],
    'ml': ['machine learning'],
    'ai': ['artificial intelligence'],
    # ... expand as needed
}

def expand_terms(term: str) -> Set[str]:
    """Expand term to include synonyms."""
    normalized = term.lower()
    synonyms = {normalized}
    for abbrev, full_forms in TECH_SYNONYMS.items():
        if normalized == abbrev or normalized in full_forms:
            synonyms.add(abbrev)
            synonyms.update(full_forms)
    return synonyms
```

**Benefits:**
- Matches abbreviations with full forms
- Handles common tech terminology
- User-extensible dictionary

### Phase 2: Consolidated Scoring (Medium Priority)

#### 2.1 Merge Keyword + Skill Matching
**Current:**
- keyword_match: 30%
- skill_match: 25%
- Total: 55% for similar functionality

**Proposed:**
- **term_match: 40%** (consolidated)
- Combines keywords, skills, and technologies into single metric
- Uses enhanced matching (fuzzy + stemming + synonyms)

#### 2.2 New Weight Distribution
```python
weights = {
    "term_match": 0.40,      # Consolidated keyword+skill (was 55%)
    "impact_level": 0.25,    # Increased from 20%
    "recency": 0.20,         # Increased from 15%
    "semantic_similarity": 0.15,  # Increased from 10%
}
```

**Rationale:**
- Simplifies scoring logic
- Gives more weight to impact and recency
- Semantic similarity becomes more important

### Phase 3: Advanced Features (Low Priority)

#### 3.1 Context-Aware Matching
```python
def context_score(achievement_text: str, job_context: str) -> float:
    """Score based on contextual similarity."""
    # Use sentence embeddings (e.g., sentence-transformers)
    # Compare achievement context with job description context
    pass
```

#### 3.2 Industry-Specific Scoring
```python
def industry_boost(achievement: Achievement, job_industry: str) -> float:
    """Boost score for industry-relevant achievements."""
    # Healthcare, Finance, Tech, etc.
    pass
```

#### 3.3 Skill Level Matching
```python
def skill_level_match(cv_skill_level: str, job_skill_level: str) -> float:
    """Match skill proficiency levels."""
    # Expert, Advanced, Intermediate, Beginner
    pass
```

## Implementation Roadmap

### Option A: LLM-Driven Scoring (RECOMMENDED - 2-3 days)

#### Sprint 1: Core LLM Scoring (1 day)
- [ ] Create `llm_score_achievement()` method in `AchievementScorer`
- [ ] Create `llm_score_achievements_batch()` for efficiency
- [ ] Add configuration option: `scoring.use_llm: true`
- [ ] Update `score_achievement()` to use LLM when enabled
- [ ] Add fallback to rule-based if LLM fails
- [ ] Add unit tests with mocked LLM responses

#### Sprint 2: Hybrid Approach (1 day)
- [ ] Implement hybrid scoring (50% LLM + 50% traditional)
- [ ] Add caching for LLM scores (Redis or in-memory)
- [ ] Optimize batch size for API rate limits
- [ ] Add cost tracking and logging
- [ ] Test with various CV sizes

#### Sprint 3: Testing & Optimization (1 day)
- [ ] Test with real CVs and job descriptions
- [ ] Measure score improvements vs old algorithm
- [ ] Optimize prompt for better accuracy
- [ ] A/B test LLM vs rule-based
- [ ] Document cost implications

### Option B: Traditional Improvements (Fallback - 3-4 days)

#### Sprint 1: Core Matching Improvements (1-2 days)
- [ ] Implement fuzzy matching with configurable threshold
- [ ] Add stemming/lemmatization
- [ ] Create tech synonym dictionary (start with 50-100 common terms)
- [ ] Update `_score_keyword_match()` to use new logic
- [ ] Update `_score_skill_match()` to use new logic
- [ ] Add unit tests for matching functions

### Sprint 2: Consolidate Metrics (1 day)
- [ ] Create new `_score_term_match()` method
- [ ] Merge keyword and skill matching logic
- [ ] Update weight distribution
- [ ] Update UI to show "Term Match" instead of separate scores
- [ ] Update documentation

### Sprint 3: Testing & Tuning (1 day)
- [ ] Test with real job descriptions
- [ ] Tune fuzzy match threshold (0.80-0.90)
- [ ] Tune scoring multipliers
- [ ] Gather user feedback
- [ ] Adjust weights based on results

### Sprint 4: Advanced Features (Optional, 2-3 days)
- [ ] Implement semantic similarity with sentence embeddings
- [ ] Add industry-specific boosting
- [ ] Add skill level matching
- [ ] Create admin UI for synonym dictionary management

## Expected Outcomes

### Before Improvements:
- Keyword match: 0-10% (mostly 0%)
- Skill match: 0-15% (mostly 0%)
- Overall match: 25-30%

### After Phase 1:
- Term match: 30-50% (significant improvement)
- Overall match: 40-55%

### After Phase 2:
- Cleaner, more intuitive scoring
- Better weight distribution
- Overall match: 45-60%

## Dependencies

### Required Libraries:
```python
# requirements.txt additions
rapidfuzz>=3.0.0  # Fast fuzzy string matching
nltk>=3.8  # Natural language processing
# OR
spacy>=3.7  # Alternative NLP library

# Optional for Phase 3:
sentence-transformers>=2.2.0  # Semantic similarity
```

### Configuration:
```yaml
# settings.yaml additions
scoring:
  fuzzy_match_threshold: 0.85
  use_stemming: true
  use_synonyms: true
  synonym_dict_path: "config/tech_synonyms.yaml"
```

## Testing Strategy

### Unit Tests:
```python
def test_fuzzy_matching():
    assert fuzzy_match("JavaScript", "javascript") == True
    assert fuzzy_match("Python", "Python3") == True
    assert fuzzy_match("React", "Angular") == False

def test_stemming():
    assert normalize_term("developed") == normalize_term("development")
    assert normalize_term("managed") == normalize_term("manager")

def test_synonym_expansion():
    assert "javascript" in expand_terms("js")
    assert "kubernetes" in expand_terms("k8s")
```

### Integration Tests:
- Test with sample CVs and job descriptions
- Verify score improvements
- Ensure no regressions in other metrics

## Rollout Plan

1. **Feature flag**: Add `use_enhanced_matching` config option
2. **A/B testing**: Run both old and new scoring in parallel
3. **Gradual rollout**: Enable for subset of users first
4. **Monitor metrics**: Track score distributions and user feedback
5. **Full deployment**: Switch all users to new algorithm

## Success Metrics

- **Primary**: Keyword/skill match scores > 0% in 80%+ of cases
- **Secondary**: Overall match scores increase by 10-20 percentage points
- **User satisfaction**: Positive feedback on relevance of selected achievements
- **Performance**: Scoring time remains < 100ms per achievement

## Maintenance

- **Synonym dictionary**: Update quarterly with new tech terms
- **Threshold tuning**: Review and adjust based on user feedback
- **Algorithm updates**: Consider ML-based scoring in future

---

**Next Steps:**
1. Review and approve this plan
2. Set up development branch
3. Begin Sprint 1 implementation
4. Schedule testing with real data