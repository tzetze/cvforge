# CVForge - Intelligent CV Generator

An AI-powered CV generation system that creates targeted, ATS-compliant CVs tailored to specific job descriptions.

## Features

**Intelligent Content Selection**
- Multi-factor scoring system (keywords, skills, impact, recency, semantic similarity)
- Automatically selects most relevant achievements for each job
- Calculates job match scores

**LLM-Powered Tailoring (Tailor-First Workflow)**
- **NEW:** Tailors ALL achievements upfront before scoring
- Shows side-by-side comparison of original vs tailored content
- Scores and selects based on tailored (more relevant) achievements
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

**Project Complete: 27/28 tasks completed (96%)**

### Completed Features
- Core architecture and data models
- LLM provider system (Claude API, Ollama)
- LinkedIn job scraper with Playwright
- Achievement scoring system (multi-factor)
- Content selection and tailoring
- PDF generation with ATS-compliant templates
- Flask web application with full UI
- CV data validator with detailed reports
- CV improvement suggester
- Achievement memory helper (interactive)
- Comprehensive error handling and logging
- Complete documentation (README, API docs, YAML schema)
- Unit tests (24 passing tests, zero warnings)

### Skipped
- CLI interface (YAGNI - web UI is sufficient)

### Production Ready
The project is fully functional and ready for real-world use!

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
# Copy example environment file
cp .env.example .env

# Edit your CV data (example provided)
nano config/cv_data.yaml

# Add your API keys (optional, for LLM features)
nano .env  # Add ANTHROPIC_API_KEY if using Claude
```

**Note:** The project includes a complete example CV in `config/cv_data.yaml` that you can use as a template.

### 3. Generate Your First CV

**On macOS (requires helper script):**
```bash
# Simple PDF generation (no LLM required)
./run_with_libs.sh python3 examples/simple_pdf_example.py

# Output will be in: output/alex_johnson_cv.pdf
```

**On Linux:**
```bash
python3 examples/simple_pdf_example.py
```

### 4. Run the Web Application

**On macOS (requires helper script for WeasyPrint):**
```bash
# Start the Flask web server
source venv/bin/activate
./run_with_libs.sh python3 -m flask --app web.app run

# Open browser to http://localhost:5000
```

**On Linux:**
```bash
source venv/bin/activate
python3 -m flask --app web.app run

# Open browser to http://localhost:5000
```

### 5. Run Tests

```bash
# Run all tests
./run_tests.sh

# Or run specific tests
pytest tests/test_data_manager.py -v

## How It Works: Tailor-First Workflow

CVForge uses an innovative **Tailor-First** approach that ensures the most relevant content is selected:

### Workflow Steps

```
1. Job Input → 2. Tailor All → 3. Review → 4. Analyze & Score → 5. Preview → 6. Download
```

#### 1. **Job Input**
- Enter job description manually or paste LinkedIn URL
- System extracts requirements, skills, and keywords

#### 2. **Tailor All Achievements** (NEW!)
- **All** achievements are tailored upfront using LLM
- Content is rewritten to emphasize job-relevant skills
- Original text is preserved for comparison

#### 3. **Review Tailored Content**
- Side-by-side comparison of original vs tailored achievements
- Visual indicators show what changed
- Transparency before scoring happens

#### 4. **Analyze & Score**
- Scoring happens on **tailored** achievements (not original)
- Multi-factor scoring: keywords, skills, impact, recency, semantic similarity
- Best achievements selected based on actual tailored relevance

#### 5. **Preview**
- See your final CV before downloading
- All content is already optimized

#### 6. **Download PDF**
- ATS-compliant PDF generation
- Professional formatting

### Why Tailor-First?

**Traditional Approach Problems:**
- Scoring happens on original achievements
- Tailoring happens after selection
- Selected achievements might not be best after tailoring

**Tailor-First Benefits:**
- ✅ Scoring based on actual tailored content
- ✅ Better selection of most relevant achievements
- ✅ User sees tailored content early for review
- ✅ More transparent process
- ✅ Higher quality final CV

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
├── web/                       # Flask web application
├── tests/                     # Unit tests (24 passing)
├── examples/                  # Example scripts
├── config/                    # Configuration files
└── docs/                      # Documentation
```

## CV Data Format

CVForge uses YAML for CV data storage. Here's a minimal example:

```yaml
personal:
  name: "John Doe"
  email: "john@example.com"
  phone: "+1-555-0123"
  location: "San Francisco, CA"
  linkedin: "https://linkedin.com/in/johndoe"

summary: "Experienced software engineer with 5+ years..."

experience:
  - company: "Tech Corp"
    position: "Senior Software Engineer"
    start_date: "2020-01"
    end_date: "present"
    location: "San Francisco, CA"
    achievements:
      - text: "Led migration to microservices architecture"
        skills: ["Python", "Docker", "Kubernetes"]
        impact: "high"
        metrics:
          deployment_time: "50% reduction"
          team_size: 5

skills:
  technical:
    - name: "Python"
      level: "expert"
    - name: "Docker"
      level: "advanced"
```

See `config/cv_data.yaml` for a complete example with all fields.

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