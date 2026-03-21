# AI-Powered Job Description Parser

This document describes the AI-powered job description parser that uses LLM providers for intelligent extraction of job requirements.

## Overview

The AI job parser (`core/job/ai_parser.py`) uses Large Language Models to analyze job descriptions and extract structured information. It provides more accurate and context-aware parsing compared to traditional regex-based approaches.

## Features

- Intelligent extraction of required and preferred skills
- Context-aware identification of responsibilities and qualifications
- Technology and tool detection
- Action verb extraction
- Keyword identification
- Seniority level inference
- Years of experience extraction
- Automatic fallback to basic extraction if AI fails

## Usage

### Basic Usage

```python
from core.job.ai_parser import AIJobDescriptionParser
from core.llm.factory import LLMManager

# Initialize LLM provider
settings = load_settings()
llm_manager = LLMManager(settings)
llm_provider = llm_manager.get_default_provider()

# Create parser
parser = AIJobDescriptionParser(llm_provider)

# Parse job description
job_data = {
    "title": "Senior Python Developer",
    "company": "Tech Corp",
    "description": "We are looking for..."
}

requirements = parser.parse(job_data)
```

### Convenience Function

```python
from core.job.ai_parser import parse_job_description_with_ai

requirements = parse_job_description_with_ai(job_data, llm_provider)
```

### Parse from Plain Text

```python
requirements = parser.parse_from_text(
    description="Job description text...",
    title="Software Engineer",
    company="Tech Co"
)
```

## Output Structure

The parser returns a `JobRequirements` object with the following fields:

```python
@dataclass
class JobRequirements:
    # Basic info
    title: Optional[str]
    company: Optional[str]
    location: Optional[str]
    
    # Extracted information
    required_skills: List[str]
    preferred_skills: List[str]
    responsibilities: List[str]
    qualifications: List[str]
    
    # Keywords and phrases
    keywords: Set[str]
    action_verbs: Set[str]
    technologies: Set[str]
    
    # Metadata
    seniority_level: Optional[str]
    employment_type: Optional[str]
    years_experience: Optional[int]
    
    # Raw data
    raw_description: str
```

## How It Works

### 1. AI Extraction

The parser sends a structured prompt to the LLM asking it to extract specific information in JSON format:

- Required skills (explicitly marked as required/must-have)
- Preferred skills (nice-to-have, bonus)
- Responsibilities (main duties)
- Qualifications (education, certifications, experience)
- Technologies (specific tools, languages, frameworks)
- Action verbs (develop, lead, manage, etc.)
- Keywords (domain-specific terms)
- Seniority level (inferred from title and requirements)
- Years of experience (minimum mentioned)

### 2. JSON Parsing

The AI response is parsed as JSON and validated. The parser handles:
- Extra text before/after JSON
- Invalid JSON with graceful fallback
- Missing or null fields

### 3. Fallback Mechanism

If AI parsing fails for any reason:
- Falls back to basic keyword extraction
- Extracts common technologies
- Searches for years of experience patterns
- Returns partial results rather than failing completely

## Integration with Web Application

The AI parser is automatically used in the CV generation workflow when:
1. An LLM provider is configured in settings
2. The provider is available and accessible
3. The job description is being analyzed

If AI parsing fails, the system automatically falls back to the traditional regex-based parser.

### Web Route Integration

In `web/routes/generate.py`, the analyze route attempts to use AI parsing:

```python
try:
    # Load LLM configuration
    llm_manager = LLMManager(settings_dict)
    llm_provider = llm_manager.get_default_provider()
    
    # Use AI parser
    ai_parser = AIJobDescriptionParser(llm_provider)
    job_info = ai_parser.parse(job_data)
    
except Exception as e:
    # Fall back to traditional parser
    parser = JobDescriptionParser()
    job_info = parser.parse(job_data)
```

## Advantages Over Traditional Parser

### Traditional Parser (Regex-based)
- Uses predefined keyword lists
- Pattern matching with regular expressions
- Limited context understanding
- May miss domain-specific terms
- Requires manual keyword list maintenance

### AI Parser
- Context-aware extraction
- Understands job description structure
- Identifies implicit requirements
- Adapts to different writing styles
- No manual keyword maintenance needed
- Better handling of synonyms and variations

## Configuration

The AI parser uses the LLM configuration from `config/settings.yaml`:

```yaml
llm:
  default_provider: "claude"
  providers:
    claude:
      type: "claude"
      model: "claude-3-sonnet-20240229"
      api_key: "${ANTHROPIC_API_KEY}"
      temperature: 0.3
      max_tokens: 4096
```

Lower temperature (0.3) is used for more consistent extraction.

## Error Handling

The parser includes comprehensive error handling:

1. Empty description: Returns empty JobRequirements
2. LLM API errors: Falls back to basic extraction
3. Invalid JSON: Attempts to extract JSON from response text
4. Missing fields: Uses default values
5. Network timeouts: Graceful degradation

## Testing

Tests are provided in `tests/test_ai_job_parser.py`:

```bash
pytest tests/test_ai_job_parser.py -v
```

Test coverage includes:
- Successful AI parsing
- Empty description handling
- AI failure fallback
- Invalid JSON handling
- JSON with extra text
- Convenience functions

## Performance Considerations

- AI parsing takes 2-5 seconds depending on LLM provider
- Results are cached in session for the workflow
- Fallback to traditional parser is instant
- Consider rate limits for high-volume usage

## Future Enhancements

Potential improvements:
- Caching of parsed results
- Batch processing for multiple jobs
- Fine-tuned prompts for specific industries
- Multi-language support
- Confidence scores for extracted information
- Structured output validation with Pydantic

## Comparison Example

### Traditional Parser Output
```python
required_skills: ["Python", "AWS", "Docker"]
technologies: {"python", "aws", "docker"}
keywords: {"experience", "development", "cloud"}
```

### AI Parser Output
```python
required_skills: [
    "Python (5+ years)",
    "AWS (EC2, S3, Lambda)",
    "Docker and Kubernetes",
    "RESTful API design",
    "Microservices architecture"
]
technologies: {
    "python", "aws", "docker", "kubernetes",
    "ec2", "s3", "lambda", "rest", "microservices"
}
keywords: {
    "scalability", "distributed systems",
    "cloud-native", "containerization"
}
```

The AI parser provides more detailed and contextual information.

## Troubleshooting

### AI Parser Not Being Used

Check:
1. LLM provider is configured in settings
2. API key is valid and set in environment
3. Provider is accessible (network connectivity)
4. Check logs for error messages

### Inaccurate Extraction

Try:
1. Adjusting temperature (lower = more consistent)
2. Using a different LLM model
3. Providing more context (title, company)
4. Checking prompt engineering in ai_parser.py

### Performance Issues

Solutions:
1. Use faster LLM models
2. Implement caching
3. Reduce max_tokens if responses are too long
4. Consider async processing for multiple jobs