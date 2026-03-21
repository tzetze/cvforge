# CV Data Editing Features

This document describes the new editing features for Experience, Skills, and Education sections in the CVForge web application.

## Overview

The CV data editing system allows users to manage their CV content through an intuitive web interface with dynamic add/remove functionality for all major sections.

## Features Implemented

### 1. Experience Section Editing
**Route:** `/cv/edit/experience`

**Capabilities:**
- Add/remove work experience entries
- Edit company, position, location, dates, and description
- Add/remove achievements within each experience
- For each achievement:
  - Description text
  - Skills/technologies (comma-separated)
  - Impact level (high/medium/low)
  - Metrics (JSON format or simple text)
  - Keywords (comma-separated, optional)

**Features:**
- Dynamic form fields with "Add Experience" and "Add Achievement" buttons
- Remove buttons with confirmation dialogs
- Automatic form field re-indexing after removal
- Client-side and server-side validation
- Date format validation (YYYY-MM or 'present')

### 2. Skills Section Editing
**Route:** `/cv/edit/skills`

**Capabilities:**
- **Technical Skills:**
  - Add/remove technical skills
  - Specify skill name, proficiency level, and years of experience
  - Proficiency levels: Expert, Advanced, Intermediate, Beginner
  
- **Soft Skills:**
  - Add/remove soft skills as simple text entries
  - Quick add functionality with inline buttons
  
- **Languages:**
  - Add/remove language proficiencies
  - Specify language name and proficiency level

**Features:**
- Three separate sub-sections for different skill types
- Dropdown menus for proficiency levels
- Number input validation for years of experience
- Simple text field management for soft skills

### 3. Education Section Editing
**Route:** `/cv/edit/education`

**Capabilities:**
- Add/remove education entries
- Edit all education fields:
  - Institution name (required)
  - Degree type (required)
  - Field of study
  - Location
  - Start date (YYYY or YYYY-MM)
  - Graduation date (YYYY or YYYY-MM)
  - Status (completed/in-progress/incomplete)
  - GPA
  - Honors & awards (comma-separated)
  - Relevant coursework (comma-separated)

**Features:**
- Comprehensive form with all education details
- Date format validation
- Status dropdown with predefined options
- Comma-separated list parsing for honors and coursework

## Technical Implementation

### Backend (Flask Routes)
**File:** `web/routes/cv_data.py`

Each section has dedicated route handlers:
- `edit_experience()` - Handles experience and nested achievements
- `edit_skills()` - Manages three skill categories
- `edit_education()` - Controls education entries

**Key Features:**
- Form data parsing with proper type conversion
- Enum validation (ImpactLevel, SkillLevel, EducationStatus)
- Pydantic model validation
- YAML file persistence
- Error handling with user-friendly flash messages

### Frontend (HTML Templates)

**Templates Created:**
- `templates/web/cv_data/edit_experience.html`
- `templates/web/cv_data/edit_skills.html`
- `templates/web/cv_data/edit_education.html`

**Features:**
- Bootstrap 5 styling for responsive design
- HTML5 form validation
- Template-based dynamic field generation
- Pre-populated forms with existing data
- Placeholder text and help text for user guidance

### JavaScript Module
**File:** `static/js/cv_form_manager.js`

**Reusable Functions:**
- `addItem()` - Add new form sections
- `removeItem()` - Remove sections with confirmation
- `addNestedItem()` - Add nested items (achievements)
- `removeNestedItem()` - Remove nested items
- `reindexItems()` - Re-index form fields after removal
- `addTextField()` - Add simple text fields
- `initValidation()` - Initialize form validation

## Usage Instructions

### Accessing Edit Pages

1. **Navigate to CV View:**
   - Go to `/cv` to view your CV data
   - Each section (Experience, Skills, Education) has an "Edit" button

2. **Edit Experience:**
   - Click "Edit" button in Experience section
   - Add new experiences with "Add Experience" button
   - Add achievements within each experience
   - Fill in all required fields (marked with *)
   - Click "Save Changes" to persist updates

3. **Edit Skills:**
   - Click "Edit" button in Skills section
   - Add technical skills with proficiency levels
   - Add soft skills as simple text entries
   - Add language proficiencies
   - Click "Save Changes" to persist updates

4. **Edit Education:**
   - Click "Edit" button in Education section
   - Add education entries with "Add Education" button
   - Fill in institution, degree, and optional fields
   - Add honors and coursework as comma-separated lists
   - Click "Save Changes" to persist updates

### Form Validation

**Client-Side:**
- Required fields are marked with red asterisk (*)
- HTML5 validation for email, dates, and patterns
- Bootstrap validation styling

**Server-Side:**
- Pydantic model validation
- Enum type checking
- Date format validation
- Minimum field length requirements

### Data Persistence

All changes are saved to the YAML file specified in the application configuration:
- Default: `config/cv_data.yaml`
- Backup recommended before major edits
- Changes are immediately reflected in CV generation

## Testing Guide

### Manual Testing Checklist

#### Experience Section:
- [ ] Add a new experience entry
- [ ] Edit existing experience details
- [ ] Remove an experience entry
- [ ] Add achievements to an experience
- [ ] Edit achievement details
- [ ] Remove an achievement
- [ ] Test with multiple skills (comma-separated)
- [ ] Test with JSON metrics
- [ ] Test date validation (YYYY-MM format)
- [ ] Test 'present' as end date
- [ ] Verify data persists after save

#### Skills Section:
- [ ] Add technical skills with different proficiency levels
- [ ] Add technical skills with years of experience
- [ ] Remove technical skills
- [ ] Add soft skills
- [ ] Remove soft skills
- [ ] Add languages with proficiency
- [ ] Remove languages
- [ ] Verify all three sub-sections save correctly

#### Education Section:
- [ ] Add education entry
- [ ] Edit all education fields
- [ ] Remove education entry
- [ ] Test date formats (YYYY and YYYY-MM)
- [ ] Test status dropdown options
- [ ] Add honors as comma-separated list
- [ ] Add coursework as comma-separated list
- [ ] Verify data persists after save

### Error Handling Tests:
- [ ] Submit form with missing required fields
- [ ] Submit invalid date formats
- [ ] Submit invalid enum values
- [ ] Test with empty achievements list
- [ ] Test removing last item (should show warning)

## Known Limitations

1. **Minimum Items:** Each section requires at least one item (enforced by JavaScript)
2. **Date Format:** Strict validation for YYYY-MM format (or YYYY for education)
3. **Metrics Format:** Achievements metrics should be valid JSON or simple text
4. **Browser Compatibility:** Tested on modern browsers (Chrome, Firefox, Safari, Edge)

## Future Enhancements

Potential improvements for future versions:
- [ ] Inline editing (edit without leaving view page)
- [ ] Drag-and-drop reordering of items
- [ ] Rich text editor for descriptions
- [ ] Auto-save functionality
- [ ] Undo/redo capabilities
- [ ] Import/export individual sections
- [ ] Duplicate entry functionality
- [ ] Bulk edit operations
- [ ] Edit history and version control

## Troubleshooting

### Common Issues:

**Issue:** Changes not saving
- **Solution:** Check browser console for JavaScript errors
- **Solution:** Verify all required fields are filled
- **Solution:** Check server logs for validation errors

**Issue:** Form fields not appearing
- **Solution:** Ensure JavaScript is enabled
- **Solution:** Check that cv_form_manager.js is loaded
- **Solution:** Clear browser cache

**Issue:** Validation errors
- **Solution:** Check date formats (YYYY-MM)
- **Solution:** Ensure at least one achievement per experience
- **Solution:** Verify enum values match expected options

## Support

For issues or questions:
1. Check application logs for detailed error messages
2. Verify YAML file syntax after manual edits
3. Review Pydantic model definitions in `core/models.py`
4. Check Flask route handlers in `web/routes/cv_data.py`

## Version History

- **v1.0** (2026-03-21): Initial implementation
  - Experience editing with nested achievements
  - Skills editing (technical, soft, languages)
  - Education editing with all fields
  - Dynamic form management with JavaScript
  - Full CRUD operations for all sections