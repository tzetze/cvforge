# Tailor-First Workflow Design Document

## Overview

This document describes the new "Tailor-First" workflow for CV generation, which reverses the current pipeline to tailor achievements before scoring and selection.

## Current Workflow (To Be Replaced)

```
Job Input → Parse Job → Score Original → Select Best → Tailor Selected → Preview → Generate PDF
```

**Issues with current approach:**
- Scoring happens on original achievements
- Tailoring happens after selection
- User doesn't see tailored content until preview
- Selected achievements might not be the best after tailoring

## New Workflow (Tailor-First)

```
Job Input → Parse Job → Tailor All → Review Tailored → Score Tailored → Select Best → Preview → Generate PDF
```

**Benefits:**
- Scoring happens on tailored (more relevant) achievements
- User reviews tailored content early
- Better selection based on actual tailored relevance
- More transparent process

## Detailed Flow

### 1. Job Input (`/generate/job-input`)
**Status:** No changes needed
- User enters job description or LinkedIn URL
- Store in session: `job_description`, `job_title`, `job_company`
- Redirect to: `/generate/tailor-all`

### 2. Tailor All Achievements (`/generate/tailor-all`)
**Status:** NEW ROUTE

**Purpose:** Tailor ALL achievements from CV based on job requirements

**Process:**
1. Load CV data
2. Parse job requirements
3. Load settings (for tailoring config)
4. Initialize LLM provider
5. Tailor all experiences and achievements in batches
6. Store tailored CV in session
7. Redirect to: `/generate/review-tailored`

**Key Implementation:**
```python
@generate_bp.route('/tailor-all')
def tailor_all():
    # Load CV and job
    cv_data = load_cv_data()
    job_description = session.get('job_description')
    job_info = parse_job(job_description)
    
    # Tailor ALL achievements
    tailor = CVTailoringEngine(llm, config)
    tailored_cv_data = tailor.tailor_all_achievements(
        cv_data=cv_data,
        job_requirements=job_info,
        job_description=job_description
    )
    
    # Store in session
    session['tailored_cv_data'] = serialize(tailored_cv_data)
    
    return redirect(url_for('generate.review_tailored'))
```

**New Method Needed:**
```python
class CVTailoringEngine:
    def tailor_all_achievements(
        self,
        cv_data: CVData,
        job_requirements: JobRequirements,
        job_description: Optional[str] = None
    ) -> CVData:
        """
        Tailor all achievements in the CV for a job.
        Returns a new CVData with tailored achievements.
        """
```

### 3. Review Tailored Content (`/generate/review-tailored`)
**Status:** NEW ROUTE & TEMPLATE

**Purpose:** Show user all tailored achievements for review

**UI Features:**
- Side-by-side comparison: Original vs Tailored
- Grouped by experience
- Highlight changes
- Edit capability (optional)
- Continue button to proceed

**Template:** `templates/web/generate/review_tailored.html`

**Layout:**
```html
<h2>Review Tailored Achievements</h2>

<div class="alert alert-info">
  All achievements have been tailored for: <strong>{{ job_title }}</strong>
  Review the changes below and click Continue when ready.
</div>

{% for exp in experiences %}
<div class="card mb-4">
  <div class="card-header">
    <h5>{{ exp.position }} at {{ exp.company }}</h5>
  </div>
  <div class="card-body">
    {% for i, ach in enumerate(exp.achievements) %}
    <div class="achievement-comparison mb-3">
      <div class="row">
        <div class="col-md-6">
          <strong>Original:</strong>
          <p class="text-muted">{{ ach.original_text }}</p>
        </div>
        <div class="col-md-6">
          <strong>Tailored:</strong>
          <p class="text-success">{{ ach.tailored_text }}</p>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>
</div>
{% endfor %}

<div class="d-grid gap-2">
  <a href="{{ url_for('generate.analyze') }}" class="btn btn-primary btn-lg">
    Continue to Analysis
  </a>
  <a href="{{ url_for('generate.job_input') }}" class="btn btn-secondary">
    Back to Job Input
  </a>
</div>
```

### 4. Analyze & Score (`/generate/analyze`)
**Status:** MODIFIED

**Changes:**
- Load tailored CV data from session (not original)
- Score tailored achievements
- Select best tailored achievements
- Show verbose analysis with tailored scores

**Key Changes:**
```python
@generate_bp.route('/analyze')
def analyze():
    # Load TAILORED CV data from session
    tailored_cv_data = deserialize(session.get('tailored_cv_data'))
    
    # Score TAILORED achievements
    scorer = AchievementScorer(weights=scorer_weights)
    selector = CVContentSelector(scorer, config=selector_config)
    
    selected_content = selector.select_content(
        cv_data=tailored_cv_data,  # Use tailored version
        job_requirements=job_info,
        verbose=True
    )
    
    # Store selected content
    session['selected_content'] = serialize(selected_content)
    
    return render_template('generate/analyze.html', ...)
```

### 5. Preview (`/generate/preview`)
**Status:** SIMPLIFIED

**Changes:**
- No tailoring step needed (already done)
- Just render selected tailored content
- Remove tailoring option

### 6. Download PDF (`/generate/download`)
**Status:** SIMPLIFIED

**Changes:**
- Use selected tailored content from session
- No re-tailoring needed

## Data Flow

### Session Data Structure

```python
session = {
    # Job data (from job-input)
    'job_description': str,
    'job_title': str,
    'job_company': str,
    'job_source': 'manual' | 'linkedin',
    
    # Tailored CV (from tailor-all)
    'tailored_cv_data': {
        'personal': {...},
        'summary': str,
        'experiences': [
            {
                'company': str,
                'position': str,
                'achievements': [
                    {
                        'original_text': str,
                        'tailored_text': str,
                        'skills': [...],
                        'impact': str,
                        'metrics': [...]
                    }
                ]
            }
        ],
        'skills': {...},
        'education': [...],
        ...
    },
    
    # Selected content (from analyze)
    'selected_content': {
        'experiences': [...],  # Subset of tailored
        'skills': {...},
        'selection_analysis': {...}
    }
}
```

## Implementation Plan

### Phase 1: Core Tailoring Method
- [ ] Create `tailor_all_achievements()` method in `CVTailoringEngine`
- [ ] Handle batch tailoring for all experiences
- [ ] Return new `CVData` object with tailored achievements
- [ ] Preserve original text for comparison

### Phase 2: New Routes
- [ ] Create `/generate/tailor-all` route
- [ ] Create `/generate/review-tailored` route
- [ ] Modify `/generate/analyze` to use tailored data
- [ ] Update redirect flow in `/generate/job-input`

### Phase 3: Templates
- [ ] Create `review_tailored.html` template
- [ ] Add side-by-side comparison UI
- [ ] Add highlighting for changes
- [ ] Update navigation flow

### Phase 4: Session Management
- [ ] Update session data structure
- [ ] Add serialization for `CVData` objects
- [ ] Handle session expiration gracefully
- [ ] Add session size monitoring

### Phase 5: Integration
- [ ] Update `analyze.html` to show tailored scores
- [ ] Simplify `preview.html` (remove tailoring option)
- [ ] Update `download` route
- [ ] Remove old tailoring code path

### Phase 6: Testing
- [ ] Test full workflow end-to-end
- [ ] Test with different CV sizes
- [ ] Test session persistence
- [ ] Test error handling
- [ ] Performance testing (tailoring all achievements)

### Phase 7: Documentation
- [ ] Update user documentation
- [ ] Update API documentation
- [ ] Add workflow diagrams
- [ ] Update README

## Technical Considerations

### Performance

**Challenge:** Tailoring all achievements upfront may be slow

**Solutions:**
1. Show progress indicator during tailoring
2. Use async processing if needed
3. Cache tailored results per job description
4. Batch process efficiently

### Session Size

**Challenge:** Storing full tailored CV in session

**Solutions:**
1. Use server-side session storage (Redis/database)
2. Compress session data
3. Store only essential data
4. Add session cleanup

### Error Handling

**Scenarios:**
1. LLM API failure during tailoring
2. Session expiration
3. Invalid CV data
4. Timeout during batch processing

**Handling:**
- Graceful fallback to original text
- Clear error messages
- Ability to retry
- Save progress

### Backward Compatibility

**During Transition:**
- Keep old workflow as fallback
- Add feature flag to switch workflows
- Gradual migration path

**After Transition:**
- Remove old tailoring code
- Clean up unused routes
- Update all documentation

## Configuration

### New Settings

Add to `settings.yaml`:

```yaml
cv_generation:
  # Existing settings...
  
  # Tailor-first workflow settings
  tailor_all_achievements: true  # Enable new workflow
  show_tailoring_progress: true  # Show progress bar
  cache_tailored_results: true   # Cache by job description hash
  max_tailoring_time: 120        # Timeout in seconds
```

## Migration Strategy

### Step 1: Implement Alongside
- Build new workflow without removing old
- Use feature flag to enable/disable
- Test thoroughly with real users

### Step 2: Gradual Rollout
- Enable for subset of users
- Monitor performance and feedback
- Fix issues as they arise

### Step 3: Full Migration
- Enable for all users
- Keep old code for 1-2 releases
- Monitor for issues

### Step 4: Cleanup
- Remove old workflow code
- Remove feature flags
- Update all documentation

## Benefits Summary

### For Users
- See tailored content early in process
- Better understanding of what will be in CV
- More accurate selection based on tailored relevance
- Transparent process with review step

### For System
- More logical flow (tailor → score → select)
- Better scoring accuracy on tailored content
- Cleaner separation of concerns
- Easier to maintain and extend

### For Quality
- Achievements scored on actual tailored text
- Selection based on real relevance
- User can verify tailoring quality
- Better final CV quality

## Open Questions

1. **Should users be able to edit tailored achievements in review step?**
   - Pro: More control
   - Con: More complexity
   - Decision: Start without editing, add later if needed

2. **How to handle very large CVs (many achievements)?**
   - Option A: Limit number of achievements tailored
   - Option B: Show progress, allow cancellation
   - Decision: Show progress, optimize batching

3. **Should we cache tailored results?**
   - Pro: Faster for same job description
   - Con: Storage overhead
   - Decision: Yes, with TTL and size limits

4. **What if tailoring fails mid-process?**
   - Fallback to original text
   - Allow retry
   - Show which achievements failed

## Success Metrics

- Time to complete workflow
- User satisfaction with tailored content
- Quality of final CV (user feedback)
- System performance (response times)
- Error rates
- Session management efficiency

## Timeline Estimate

- Phase 1 (Core Method): 2-3 days
- Phase 2 (Routes): 1-2 days
- Phase 3 (Templates): 2-3 days
- Phase 4 (Session): 1-2 days
- Phase 5 (Integration): 2-3 days
- Phase 6 (Testing): 2-3 days
- Phase 7 (Documentation): 1-2 days

**Total: 11-18 days** (depending on complexity and issues)

## Conclusion

The Tailor-First workflow represents a significant improvement in the CV generation process. By tailoring achievements before scoring and selection, we ensure that the most relevant content is selected based on its actual tailored form, not the original. The addition of a review step gives users transparency and confidence in the process.

This design maintains all the improvements we've made (verbose analysis, settings respect, batch tailoring, word variety) while providing a more logical and effective workflow.