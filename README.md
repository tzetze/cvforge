# CVForge - Intelligent CV Generator

An AI-powered CV generation system that creates targeted, ATS-compliant CVs tailored to specific job descriptions.

## Features

**Intelligent Content Selection**
- Multi-factor scoring system (keywords, skills, impact, recency, semantic similarity)
- Automatically selects most relevant achievements for each job
- Calculates job match scores

**LLM-Powered Tailoring**
- Rewrites CV content to emphasize job-relevant skills
- Supports multiple LLM providers (Claude API, Ollama)
- Maintains authenticity while optimizing for relevance

**Professional PDF Generation**
- ATS-compliant templates
- Clean, parseable formatting
- WeasyPrint-based rendering

**LinkedIn Job Scraping**
- Automated job description extraction
- Manual login support for authenticated access
- Intelligent parsing of requirements and skills

**YAML-Based Data Management**
- Human-readable CV data format
- Rich metadata support (skills, impact metrics, keywords)
- Environment variable support for sensitive data

## Project Status

**Current Progress: 16/28 tasks completed (57%)**

### Completed
- Core architecture and data models
- LLM provider system (Claude, Ollama)
- LinkedIn job scraper
- Achievement scoring system
- Content selection and tailoring
- PDF generation with templates

### In Progress
- Web UI (Flask application)
- CV data validator
- Documentation

### Planned
- CLI interface
- Achievement memory helper
- Additional templates
- Comprehensive testing

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone git@github.com:tzetze/cvforge.git
cd cvforge

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install Playwright browsers (for LinkedIn scraping)
playwright install chromium
```

### 2. Configuration

```bash
# Copy example files
cp config/cv_data.example.yaml config/cv_data.yaml
cp config/settings.example.yaml config/settings.yaml
cp .env.example .env

# Edit your CV data
nano config/cv_data.yaml

# Configure LLM providers (optional)
nano config/settings.yaml
nano .env  # Add API keys
```

### 3. Generate Your First CV

```bash
# Simple PDF generation (no LLM required)
python examples/simple_pdf_example.py

# Output will be in: output/your_name_cv.pdf
```

## Project Structure

```
cvmaker/
├── core/                      # Core business logic
│   ├── llm/                   # LLM provider system
│   │   ├── base.py           # Abstract provider interface
│   │   ├── claude_provider.py
│   │   ├── ollama_provider.py
│   │   └── factory.py        # Provider factory
│   ├── job/                   # Job analysis
│   │   ├── scraper.py        # LinkedIn scraper
│   │   └── parser.py         # Job description parser
│   ├── scoring/               # Content scoring
│   │   └── achievement_scorer.py
│   ├── generation/            # CV generation
│   │   ├── cv_selector.py    # Content selection
│   │   ├── cv_tailor.py      # LLM tailoring
│   │   └── pdf_generator.py  # PDF rendering
│   ├── models.py              # Pydantic data models
│   └── data_manager.py        # YAML operations
├── templates/                 # CV templates
│   └── cv/
│       └── modern.html       # ATS-compliant template
├── web/                       # Flask web application (WIP)
├── cli/                       # CLI interface (planned)
├── tests/                     # Unit tests
├── examples/                  # Example scripts
├── config/                    # Configuration files
└── docs/                      # Documentation
```

## CV Data Format

CVForge uses YAML for CV data storage. Here's a minimal example:

```yaml
personal_info:
  name: "John Doe"
  email: "john@example.com"
  phone: "+1-555-0123"
  location: "San Francisco, CA"
  linkedin: "https://linkedin.com/in/johndoe"

summary: "Experienced software engineer with 5+ years..."

experiences:
  - company: "Tech Corp"
    position: "Senior Software Engineer"
    start_date: "2020-01"
    end_date: "present"
    location: "San Francisco, CA"
    achievements:
      - text: "Led migration to microservices architecture"
        skills: ["Python", "Docker", "Kubernetes"]
        impact: "high"
        metrics: ["50% reduction in deployment time"]

skills:
  technical:
    - name: "Python"
      level: "expert"
    - name: "Docker"
      level: "advanced"
```

See `config/cv_data.example.yaml` for a complete example with all fields.

## Usage Examples

### Basic PDF Generation

```python
from core.data_manager import load_cv_data
from core.generation import PDFGenerator

# Load CV data
cv_data = load_cv_data("config/cv_data.yaml")

# Generate PDF
generator = PDFGenerator()
generator.generate_pdf(
    cv_data=cv_data,
    output_path="output/my_cv.pdf",
    template_name="modern"
)
```

### Job-Targeted CV Generation

```python
from core.data_manager import load_cv_data
from core.job import JobDescriptionParser
from core.scoring import AchievementScorer
from core.generation import CVContentSelector, PDFGenerator

# Load CV
cv_data = load_cv_data("config/cv_data.yaml")

# Parse job description
parser = JobDescriptionParser()
job_info = parser.parse(job_description_dict)

# Score and select content
scorer = AchievementScorer()
selector = CVContentSelector(scorer)
selected = selector.select_content(
    cv_data=cv_data,
    job_requirements=job_info.required_skills,
    top_n=10
)

# Generate PDF with selected content
generator = PDFGenerator()
generator.generate_pdf_from_selected_content(
    personal_info=cv_data.personal_info.model_dump(),
    summary=cv_data.summary,
    experiences=selected.experiences,
    skills=cv_data.skills.model_dump(),
    education=cv_data.education,
    output_path="output/targeted_cv.pdf"
)
```

### With LLM Tailoring

```python
from core.llm import LLMManager
from core.generation import CVTailoringEngine

# Initialize LLM
llm_manager = LLMManager.from_yaml("config/settings.yaml")
llm = llm_manager.get_provider("default")

# Tailor content
tailor = CVTailoringEngine(llm)
tailored = tailor.tailor_cv(
    selected_content=selected,
    job_requirements=job_info.required_skills
)

# Generate PDF with tailored content
generator.generate_pdf_from_selected_content(
    personal_info=cv_data.personal_info.model_dump(),
    summary=tailored.summary,
    experiences=tailored.experiences,
    # ... other fields
    output_path="output/tailored_cv.pdf"
)
```

## LLM Configuration

CVForge supports multiple LLM providers:

### Claude API (Anthropic)

```yaml
# config/settings.yaml
llm_providers:
  default:
    provider: "claude"
    model: "claude-3-5-sonnet-20241022"
    api_key_env: "ANTHROPIC_API_KEY"
```

```bash
# .env
ANTHROPIC_API_KEY=your_api_key_here
```

### Ollama (Local)

```yaml
# config/settings.yaml
llm_providers:
  local:
    provider: "ollama"
    model: "llama3.1:8b"
    base_url: "http://localhost:11434"
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html

# Run specific test file
pytest tests/test_achievement_scorer.py -v
```

## ATS Compliance

CVForge generates ATS-compliant CVs by:

- Using standard HTML structure
- Avoiding complex layouts and tables
- Using standard fonts (Arial, Helvetica)
- Clear section headings
- No images or graphics in text areas
- Proper semantic markup
- Clean, parseable PDF output

## Contributing

Contributions are welcome! Areas for contribution:

- Additional CV templates
- More LLM provider integrations
- Web UI improvements
- Additional test coverage
- Documentation improvements

## License

MIT License - see LICENSE file for details

## Roadmap

### Phase 1: Core Functionality (Current)
- [x] Data models and YAML storage
- [x] LLM provider system
- [x] Job scraping and parsing
- [x] Content scoring and selection
- [x] PDF generation

### Phase 2: User Interface
- [ ] Flask web application
- [ ] CV data management UI
- [ ] Job input interface
- [ ] Interactive CV generation workflow

### Phase 3: Enhancement
- [ ] Achievement memory helper
- [ ] CV improvement suggestions
- [ ] Multiple template options
- [ ] Batch CV generation

### Phase 4: Polish
- [ ] Comprehensive documentation
- [ ] Full test coverage
- [ ] CLI interface
- [ ] Deployment guides

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/tzetze/cvforge/issues
- Documentation: See `docs/` directory

## Acknowledgments

Built with:
- [Pydantic](https://pydantic.dev/) - Data validation
- [WeasyPrint](https://weasyprint.org/) - PDF generation
- [Playwright](https://playwright.dev/) - Web scraping
- [Anthropic Claude](https://www.anthropic.com/) - LLM provider
- [Ollama](https://ollama.ai/) - Local LLM support