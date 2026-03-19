# CV Data YAML Schema

This document describes the complete YAML schema for storing CV data in CVForge.

## Overview

The CV data is stored in a human-editable YAML format that supports:
- Rich metadata for intelligent achievement selection
- Multiple achievements per job role
- Comprehensive skill categorization
- Volunteer work and open-source contributions
- Flexible education status (completed, in-progress, incomplete)

## Complete Schema

```yaml
personal:
  name: string (required)
  email: string (required, email format)
  phone: string (optional)
  location: string (optional)
  linkedin: string (optional, URL)
  github: string (optional, URL)
  website: string (optional, URL)

summary: string (optional, 2-3 sentences professional summary)

experience:
  - company: string (required)
    position: string (required)
    location: string (optional)
    start_date: string (required, YYYY-MM format)
    end_date: string (optional, YYYY-MM or "present")
    description: string (optional, brief role overview)
    achievements:
      - text: string (required, the achievement description)
        skills: list[string] (required, related skills/technologies)
        impact: string (required, one of: high, medium, low)
        metrics: dict (optional, quantifiable data)
          # Examples:
          # revenue: "40%"
          # users: "1M+"
          # performance: "50ms reduction"
          # team_size: 5
        keywords: list[string] (optional, additional ATS keywords)

skills:
  technical:
    - name: string (required)
      level: string (optional, one of: expert, advanced, intermediate, beginner)
      years: int (optional, years of experience)
  soft:
    - string (e.g., "Leadership", "Communication")
  languages:
    - language: string (required)
      proficiency: string (required, e.g., "Native", "Fluent", "Professional")

education:
  - institution: string (required)
    degree: string (required)
    field: string (optional)
    location: string (optional)
    start_date: string (optional, YYYY-MM or YYYY)
    graduation_date: string (optional, YYYY-MM or YYYY)
    status: string (optional, one of: completed, in-progress, incomplete)
    gpa: string (optional)
    honors: list[string] (optional)
    relevant_coursework: list[string] (optional)

certifications:
  - name: string (required)
    issuer: string (required)
    date: string (required, YYYY-MM)
    expiry: string (optional, YYYY-MM)
    credential_id: string (optional)
    url: string (optional, verification URL)

volunteer:
  - organization: string (required)
    role: string (required)
    start_date: string (required, YYYY-MM)
    end_date: string (optional, YYYY-MM or "present")
    description: string (optional)
    achievements: list[string] (optional)
    type: string (optional, e.g., "open-source", "conference", "meetup", "community")

projects:
  - name: string (required)
    description: string (required)
    technologies: list[string] (required)
    url: string (optional, project URL)
    github: string (optional, GitHub repository URL)
    achievements: list[string] (optional)
    start_date: string (optional, YYYY-MM)
    end_date: string (optional, YYYY-MM or "present")

publications:
  - title: string (required)
    venue: string (required, journal/conference name)
    date: string (required, YYYY-MM)
    authors: list[string] (optional)
    url: string (optional, DOI or publication URL)
    description: string (optional)

awards:
  - title: string (required)
    issuer: string (required)
    date: string (required, YYYY-MM)
    description: string (optional)
```

## Field Descriptions

### Personal Information

- **name**: Full name as it should appear on CV
- **email**: Professional email address
- **phone**: Phone number with country code (optional)
- **location**: City, State/Country
- **linkedin**: LinkedIn profile URL
- **github**: GitHub profile URL
- **website**: Personal website or portfolio URL

### Summary

A brief professional summary (2-3 sentences) highlighting your key strengths and career focus. This will be tailored for each job application.

### Experience

Each experience entry represents a job role with multiple achievements.

**Achievement Metadata:**
- **text**: The achievement description (use action verbs, be specific)
- **skills**: List of technologies/skills used (important for scoring)
- **impact**: high/medium/low (affects selection priority)
- **metrics**: Quantifiable results (revenue, users, performance, etc.)
- **keywords**: Additional keywords for ATS optimization

**Best Practices:**
- Start with strong action verbs (Built, Led, Implemented, Designed)
- Include quantifiable metrics whenever possible
- Be specific about technologies and methodologies
- Focus on impact and results, not just tasks

### Skills

**Technical Skills:**
- **name**: Technology, framework, or tool name
- **level**: Your proficiency level (optional but recommended)
- **years**: Years of experience (optional)

**Soft Skills:**
Simple list of soft skills (Leadership, Communication, Problem Solving, etc.)

**Languages:**
- **language**: Language name
- **proficiency**: Native, Fluent, Professional, Conversational, Basic

### Education

Supports various education statuses:
- **completed**: Graduated with degree
- **in-progress**: Currently enrolled
- **incomplete**: Started but didn't complete (e.g., dropout founders)

**Fields:**
- **start_date** and **graduation_date** are both optional
- Use **status** to indicate completion status
- **honors**: Dean's List, Cum Laude, scholarships, etc.
- **relevant_coursework**: Important courses for technical roles

### Certifications

Professional certifications and licenses.
- Include **expiry** date if applicable
- Add **credential_id** for verification
- Include **url** for online verification

### Volunteer Work

Showcase community involvement, open-source contributions, and leadership.

**Types:**
- **open-source**: Contributions to open-source projects
- **conference**: Conference organization or speaking
- **meetup**: Meetup organization or hosting
- **community**: General community service

### Projects

Personal or side projects that demonstrate skills.
- Include **github** URL for code repositories
- List **technologies** used
- Highlight **achievements** and impact

### Publications

Academic or professional publications.
- Include all **authors** if co-authored
- Provide **url** (DOI, arXiv, etc.)
- Add brief **description** if title isn't self-explanatory

### Awards

Professional awards and recognitions.
- Include **issuer** (company, organization, institution)
- Add **description** to provide context

## Validation Rules

1. **Required Fields:**
   - personal.name
   - personal.email
   - experience[].company
   - experience[].position
   - experience[].start_date
   - experience[].achievements[].text
   - experience[].achievements[].skills (at least one)
   - experience[].achievements[].impact

2. **Date Formats:**
   - YYYY-MM for month-specific dates
   - YYYY for year-only dates
   - "present" for current/ongoing

3. **Email Format:**
   - Must be valid email address

4. **URL Format:**
   - Must be valid HTTP/HTTPS URL

5. **Enum Values:**
   - impact: high, medium, low
   - skill level: expert, advanced, intermediate, beginner
   - education status: completed, in-progress, incomplete
   - volunteer type: open-source, conference, meetup, community

## Tips for Best Results

1. **Be Comprehensive**: Include ALL achievements, even if they seem minor. The system will select the most relevant ones for each job.

2. **Use Metrics**: Quantify impact whenever possible (percentages, numbers, time saved, etc.)

3. **Tag Skills Accurately**: List all relevant skills for each achievement to improve matching.

4. **Categorize Impact**: Be honest about impact levels - this helps prioritize achievements.

5. **Keep It Updated**: Regularly add new achievements and update skills.

6. **Use Keywords**: Include industry-standard terms and technologies in achievements.

## Example

See `config/cv_data.example.yaml` for a complete example with realistic data.