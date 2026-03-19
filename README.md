# CVForge

An intelligent CV generator that uses AI to tailor your resume for specific job applications.

## Features

- **Intelligent Achievement Selection**: Automatically selects the most relevant achievements from your comprehensive CV data
- **Multi-Factor Scoring**: Uses keyword matching, skill relevance, impact level, recency, and semantic analysis
- **Interchangeable LLM Backends**: Support for Claude API and local Ollama models
- **LinkedIn Integration**: Scrape job descriptions directly from LinkedIn URLs
- **ATS-Compliant PDFs**: Generate professional, ATS-friendly PDF resumes
- **Data Validation**: Checks CV data quality and suggests improvements
- **Flask Web UI**: Easy-to-use web interface for managing CV data and generating resumes

## Project Status

🚧 **Under Development** - Currently implementing Phase 1: Foundation

See [docs/project_plan.md](docs/project_plan.md) for the complete project plan and roadmap.

## Architecture

- **Modular Design**: Core logic separated from UI layer
- **YAML Data Storage**: Human-editable CV data format
- **Abstract LLM Interface**: Easy to switch between different AI providers
- **Comprehensive Testing**: 80%+ test coverage goal

## Quick Start

(Coming soon - project is under active development)

## Documentation

- [Project Plan](docs/project_plan.md) - Complete technical specification and implementation plan
- [YAML Schema](docs/yaml_schema.md) - CV data format guide (coming soon)
- [API Reference](docs/api_reference.md) - API documentation (coming soon)
- [User Guide](docs/user_guide.md) - End-user instructions (coming soon)

## Technology Stack

- **Language**: Python 3.11+
- **Web Framework**: Flask
- **Data Format**: YAML (PyYAML)
- **Validation**: Pydantic
- **PDF Generation**: WeasyPrint
- **Web Scraping**: Playwright
- **LLM APIs**: Anthropic (Claude), Ollama
- **Testing**: pytest

## License

(To be determined)

## Contributing

(Coming soon)