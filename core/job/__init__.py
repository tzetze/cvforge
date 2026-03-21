"""
Job scraping and parsing module for CVForge.

This module provides functionality for scraping job descriptions from LinkedIn
and parsing them to extract requirements, skills, and keywords.

Supports both traditional regex-based parsing and AI-powered parsing using LLM providers.
"""

from core.job.scraper import (
    LinkedInJobScraper,
    JobScraperError,
    InvalidURLError,
    ScrapingError,
    scrape_linkedin_job,
)
from core.job.parser import (
    JobDescriptionParser,
    JobRequirements,
    parse_job_description,
)
from core.job.ai_parser import (
    AIJobDescriptionParser,
    create_ai_parser,
    parse_job_description_with_ai,
)

__all__ = [
    # Scraper
    "LinkedInJobScraper",
    "JobScraperError",
    "InvalidURLError",
    "ScrapingError",
    "scrape_linkedin_job",
    # Parser (traditional)
    "JobDescriptionParser",
    "JobRequirements",
    "parse_job_description",
    # AI Parser
    "AIJobDescriptionParser",
    "create_ai_parser",
    "parse_job_description_with_ai",
]
