# CVForge API Documentation

Complete API reference for CVForge core modules.

## Table of Contents

- [Data Management](#data-management)
- [CV Generation](#cv-generation)
- [Validation](#validation)
- [LLM Integration](#llm-integration)
- [Job Processing](#job-processing)
- [Utilities](#utilities)

---

## Data Management

### `core.data_manager`

Functions for loading and saving CV data.

#### `load_cv_data(file_path: str) -> CVData`

Load CV data from a YAML file.

**Parameters:**
- `file_path` (str): Path to the YAML file

**Returns:**
- `CVData`: Validated CV data object

**Raises:**
- `CVDataNotFoundError`: If file doesn't exist
- `CVDataParseError`: If YAML is invalid
- `CVDataValidationError`: If data doesn't match schema

**Example:**
```python
from core.data_manager import load_cv_data

cv_data = load_cv_data("config/cv_data.yaml")
print(f"Loaded CV for {cv_data.personal.name}")
```

#### `save_cv_data(cv_data: CVData, file_path: str) -> None`

Save CV data to a YAML file.

**Parameters:**
- `cv_data` (CVData): CV data object to save
- `file_path` (str): Output file path

**Example:**
```python
from core.data_manager import save_cv_data

save_cv_data(cv_data, "config/my_cv.yaml")
```

---

## CV Generation

### `core.generation.cv_selector`

Select relevant CV content based on job requirements.

#### `CVSelector`

**Constructor:**
```python
CVSelector(scorer: Optional[AchievementScorer] = None)
```

**Methods:**

##### `select_content(cv_data: CVData, job_requirements: JobRequirements, max_achievements_per_role: int = 5, min_score_threshold: float = 0.3) -> SelectedContent`

Select and rank CV content for a specific job.

**Parameters:**
- `cv_data`: Complete CV data
- `job_requirements`: Parsed job requirements
- `max_achievements_per_role`: Maximum achievements per experience
- `min_score_threshold`: Minimum relevance score (0.0-1.0)

**Returns:**
- `SelectedContent`: Filtered and ranked CV content

**Example:**
```python
from core.generation.cv_selector import CVSelector
from core.job.parser import JobParser

selector = CVSelector()
parser = JobParser()

job_reqs = parser.parse(job_description_text)
selected = selector.select_content(
    cv_data=cv_data,
    job_requirements=job_reqs,
    max_achievements_per_role=4,
    min_score_threshold=0.4
)
```

### `core.generation.cv_tailor`

Tailor CV content using LLM.

#### `CVTailor`

**Constructor:**
```python
CVTailor(llm_provider: BaseLLMProvider)
```

**Methods:**

##### `tailor_cv(selected_content: SelectedContent, job_requirements: JobRequirements, company_info: Optional[Dict] = None) -> TailoredCV`

Generate tailored CV with LLM-enhanced content.

**Parameters:**
- `selected_content`: Pre-selected relevant content
- `job_requirements`: Job requirements
- `company_info`: Optional company information

**Returns:**
- `TailoredCV`: Tailored CV with enhanced summary and achievements

**Example:**
```python
from core.generation.cv_tailor import CVTailor
from core.llm.factory import create_llm_provider

llm = create_llm_provider("claude")
tailor = CVTailor(llm)

tailored = tailor.tailor_cv(
    selected_content=selected,
    job_requirements=job_reqs
)
```

### `core.generation.pdf_generator`

Generate PDF from CV data.

#### `PDFGenerator`

**Constructor:**
```python
PDFGenerator(template_dir: Optional[Path] = None)
```

**Methods:**

##### `generate_pdf(cv_data: CVData, output_path: Path, template_name: str = "modern", custom_css: Optional[str] = None, metadata: Optional[Dict] = None) -> Path`

Generate PDF from complete CV data.

**Parameters:**
- `cv_data`: Complete CV data
- `output_path`: Output PDF file path
- `template_name`: Template name (default: "modern")
- `custom_css`: Optional custom CSS
- `metadata`: Optional PDF metadata

**Returns:**
- `Path`: Path to generated PDF

**Example:**
```python
from core.generation.pdf_generator import PDFGenerator
from pathlib import Path

generator = PDFGenerator()
pdf_path = generator.generate_pdf(
    cv_data=cv_data,
    output_path=Path("output/my_cv.pdf"),
    template_name="modern"
)
```

##### `generate_pdf_from_selected_content(personal_info: Dict, summary: Optional[str], experiences: List[Experience], skills: Optional[Dict] = None, education: Optional[List] = None, output_path: Optional[Path] = None, template_name: str = "modern") -> Path`

Generate PDF from selected/tailored content.

**Example:**
```python
pdf_path = generator.generate_pdf_from_selected_content(
    personal_info=cv_data.personal.model_dump(),
    summary=tailored.summary,
    experiences=tailored.experiences,
    skills=cv_data.skills.model_dump() if cv_data.skills else None,
    output_path=Path("output/tailored_cv.pdf")
)
```

---

## Validation

### `core.validation.cv_validator`

Validate CV data quality and completeness.

#### `validate_cv_data(cv_data: CVData, min_experiences: int = 2, min_achievements_per_role: int = 3, min_skills: int = 5) -> ValidationReport`

Validate CV data and generate report.

**Parameters:**
- `cv_data`: CV data to validate
- `min_experiences`: Minimum number of experiences
- `min_achievements_per_role`: Minimum achievements per role
- `min_skills`: Minimum number of skills

**Returns:**
- `ValidationReport`: Detailed validation report

**Example:**
```python
from core.validation.cv_validator import validate_cv_data

report = validate_cv_data(cv_data)

if report.is_valid:
    print("✓ CV is valid!")
else:
    print(f"Found {report.error_count} errors:")
    for issue in report.errors:
        print(f"  - {issue.message}")
```

#### `ValidationReport`

**Properties:**
- `is_valid` (bool): Overall validation status
- `error_count` (int): Number of errors
- `warning_count` (int): Number of warnings
- `info_count` (int): Number of info messages
- `errors` (List[ValidationIssue]): List of errors
- `warnings` (List[ValidationIssue]): List of warnings
- `infos` (List[ValidationIssue]): List of info messages

**Methods:**
- `to_dict()`: Export as dictionary
- `__str__()`: Human-readable string representation

---

## LLM Integration

### `core.llm.factory`

Create LLM provider instances.

#### `create_llm_provider(provider_type: str, settings: Optional[Dict] = None) -> BaseLLMProvider`

Factory function to create LLM providers.

**Parameters:**
- `provider_type`: "claude" or "ollama"
- `settings`: Optional provider settings

**Returns:**
- `BaseLLMProvider`: LLM provider instance

**Example:**
```python
from core.llm.factory import create_llm_provider

# Claude API
claude = create_llm_provider("claude")

# Ollama (local)
ollama = create_llm_provider("ollama", {
    "model": "llama2",
    "base_url": "http://localhost:11434"
})
```

### `core.llm.base.BaseLLMProvider`

Base interface for LLM providers.

**Methods:**

##### `generate(prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1000, temperature: float = 0.7) -> str`

Generate text from prompt.

**Parameters:**
- `prompt`: User prompt
- `system_prompt`: Optional system instructions
- `max_tokens`: Maximum response length
- `temperature`: Creativity (0.0-1.0)

**Returns:**
- `str`: Generated text

---

## Job Processing

### `core.job.scraper`

Scrape job descriptions from LinkedIn.

#### `LinkedInScraper`

**Methods:**

##### `scrape_job(job_url: str) -> Dict[str, Any]`

Scrape job description from LinkedIn URL.

**Parameters:**
- `job_url`: LinkedIn job posting URL

**Returns:**
- `Dict`: Job data including title, company, description, etc.

**Example:**
```python
from core.job.scraper import LinkedInScraper

scraper = LinkedInScraper()
job_data = scraper.scrape_job("https://www.linkedin.com/jobs/view/...")
```

### `core.job.parser`

Parse job descriptions to extract requirements.

#### `JobParser`

**Methods:**

##### `parse(job_data: Dict[str, Any]) -> JobRequirements`

Parse job data to extract requirements.

**Parameters:**
- `job_data`: Job data dictionary (from scraper or manual input)

**Returns:**
- `JobRequirements`: Parsed requirements

**Example:**
```python
from core.job.parser import JobParser

parser = JobParser()

# From scraped data
job_reqs = parser.parse(job_data)

# From manual text
job_reqs = parser.parse({
    "title": "Senior Python Developer",
    "description": "We are looking for...",
    "company": "Tech Corp"
})
```

---

## Utilities

### `core.utils.logger`

Logging utilities.

#### `get_logger(name: str) -> logging.Logger`

Get a logger instance.

**Parameters:**
- `name`: Logger name (typically `__name__`)

**Returns:**
- `logging.Logger`: Configured logger

**Example:**
```python
from core.utils import get_logger

logger = get_logger(__name__)
logger.info("Processing CV data")
logger.error("Failed to generate PDF", exc_info=True)
```

### `core.utils.exceptions`

Custom exception types for better error handling.

**Available Exceptions:**

**Data Exceptions:**
- `CVDataNotFoundError`
- `CVDataValidationError`
- `CVDataParseError`

**LLM Exceptions:**
- `LLMProviderError`
- `LLMConnectionError`
- `LLMResponseError`
- `LLMRateLimitError`

**Generation Exceptions:**
- `PDFGenerationError`
- `TemplateError`
- `ContentSelectionError`

**Job Exceptions:**
- `JobScrapingError`
- `JobParsingError`

**Example:**
```python
from core.utils import get_logger, PDFGenerationError

logger = get_logger(__name__)

try:
    pdf_path = generator.generate_pdf(cv_data, output_path)
except PDFGenerationError as e:
    logger.error(f"PDF generation failed: {e}")
    raise
```

---

## Complete Example

Here's a complete example of generating a tailored CV:

```python
from pathlib import Path
from core.data_manager import load_cv_data
from core.job.parser import JobParser
from core.generation.cv_selector import CVSelector
from core.generation.cv_tailor import CVTailor
from core.generation.pdf_generator import PDFGenerator
from core.llm.factory import create_llm_provider
from core.utils import get_logger

logger = get_logger(__name__)

# 1. Load CV data
logger.info("Loading CV data")
cv_data = load_cv_data("config/cv_data.yaml")

# 2. Parse job description
logger.info("Parsing job description")
parser = JobParser()
job_reqs = parser.parse({
    "title": "Senior Python Developer",
    "description": "Looking for experienced Python developer...",
    "company": "Tech Corp"
})

# 3. Select relevant content
logger.info("Selecting relevant content")
selector = CVSelector()
selected = selector.select_content(
    cv_data=cv_data,
    job_requirements=job_reqs,
    max_achievements_per_role=4
)

# 4. Tailor with LLM
logger.info("Tailoring CV with LLM")
llm = create_llm_provider("claude")
tailor = CVTailor(llm)
tailored = tailor.tailor_cv(selected, job_reqs)

# 5. Generate PDF
logger.info("Generating PDF")
generator = PDFGenerator()
pdf_path = generator.generate_pdf_from_selected_content(
    personal_info=cv_data.personal.model_dump(),
    summary=tailored.summary,
    experiences=tailored.experiences,
    skills=cv_data.skills.model_dump() if cv_data.skills else None,
    output_path=Path("output/tailored_cv.pdf")
)

logger.info(f"✓ CV generated: {pdf_path}")
```

---

## Error Handling Best Practices

Always use try-except blocks with specific exceptions:

```python
from core.utils import (
    get_logger,
    CVDataNotFoundError,
    PDFGenerationError,
    LLMConnectionError
)

logger = get_logger(__name__)

try:
    cv_data = load_cv_data("config/cv_data.yaml")
except CVDataNotFoundError:
    logger.error("CV data file not found")
    # Handle missing file
except CVDataValidationError as e:
    logger.error(f"CV data validation failed: {e.validation_errors}")
    # Handle validation errors

try:
    pdf_path = generator.generate_pdf(cv_data, output_path)
except PDFGenerationError as e:
    logger.error(f"PDF generation failed: {e}", exc_info=True)
    # Handle PDF generation failure

try:
    response = llm.generate(prompt)
except LLMConnectionError:
    logger.error("Cannot connect to LLM service")
    # Handle connection failure
except LLMRateLimitError:
    logger.warning("Rate limit exceeded, retrying...")
    # Handle rate limiting
```

---

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# LLM API Keys
ANTHROPIC_API_KEY=your_claude_api_key_here
OLLAMA_BASE_URL=http://localhost:11434

# Application Settings
LOG_LEVEL=INFO
CV_DATA_PATH=config/cv_data.yaml
```

### Settings File

Edit `config/settings.yaml`:

```yaml
llm:
  provider: claude  # or ollama
  model: claude-3-sonnet-20240229
  temperature: 0.7
  max_tokens: 2000

generation:
  default_template: modern
  max_achievements_per_role: 5
  min_score_threshold: 0.3

validation:
  min_experiences: 2
  min_achievements_per_role: 3
  min_skills: 5
```

---

For more information, see:
- [README.md](../README.md) - Project overview
- [QUICKSTART.md](../QUICKSTART.md) - Quick start guide
- [yaml_schema.md](yaml_schema.md) - CV data schema