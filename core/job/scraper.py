"""
LinkedIn job scraper for fetching job descriptions.

This module provides functionality to scrape job descriptions from LinkedIn
using Playwright for browser automation.
"""

import re
import time
from typing import Optional, Dict, Any
from urllib.parse import urlparse

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class JobScraperError(Exception):
    """Base exception for job scraper errors."""
    pass


class InvalidURLError(JobScraperError):
    """Raised when the provided URL is invalid."""
    pass


class ScrapingError(JobScraperError):
    """Raised when scraping fails."""
    pass


class LinkedInJobScraper:
    """
    Scraper for LinkedIn job postings.
    
    Uses Playwright to fetch job descriptions from LinkedIn URLs.
    Supports manual login for authenticated access.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LinkedIn job scraper.
        
        Args:
            config: Optional configuration dict with scraping settings
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise JobScraperError(
                "Playwright not installed. Install with: pip install playwright && "
                "playwright install chromium"
            )
        
        self.config = config or {}
        self.headless = self.config.get("headless", True)
        self.timeout = self.config.get("timeout", 30) * 1000  # Convert to ms
        self.wait_for_manual_login = self.config.get("wait_for_manual_login", True)
        self.user_agent = self.config.get(
            "user_agent",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
    
    def scrape_job(self, url: str) -> Dict[str, Any]:
        """
        Scrape a job posting from LinkedIn.
        
        Args:
            url: LinkedIn job posting URL
            
        Returns:
            Dict containing job information:
                - url: Job URL
                - title: Job title
                - company: Company name
                - location: Job location
                - description: Full job description
                - posted_date: When the job was posted
                - employment_type: Full-time, Part-time, etc.
                - seniority_level: Entry level, Mid-Senior, etc.
                
        Raises:
            InvalidURLError: If URL is not a valid LinkedIn job URL
            ScrapingError: If scraping fails
        """
        # Validate URL
        if not self._is_valid_linkedin_job_url(url):
            raise InvalidURLError(
                f"Invalid LinkedIn job URL: {url}. "
                "Expected format: https://www.linkedin.com/jobs/view/..."
            )
        
        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(user_agent=self.user_agent)
                page = context.new_page()
                
                # Navigate to job page
                page.goto(url, timeout=self.timeout)
                
                # Check if login is required
                if self._is_login_required(page):
                    if self.wait_for_manual_login:
                        print("\n" + "="*60)
                        print("LinkedIn login required!")
                        print("Please log in manually in the browser window.")
                        print("The scraper will continue automatically after login.")
                        print("="*60 + "\n")
                        
                        # Wait for user to login (check for job description element)
                        try:
                            page.wait_for_selector(
                                ".jobs-description",
                                timeout=120000  # 2 minutes
                            )
                        except PlaywrightTimeout:
                            raise ScrapingError(
                                "Login timeout. Please try again and log in within 2 minutes."
                            )
                    else:
                        raise ScrapingError(
                            "LinkedIn login required. Set 'wait_for_manual_login: true' "
                            "in config to enable manual login."
                        )
                
                # Wait for job description to load
                page.wait_for_selector(".jobs-description", timeout=self.timeout)
                
                # Extract job information
                job_data = self._extract_job_data(page, url)
                
                browser.close()
                
                return job_data
                
        except PlaywrightTimeout as e:
            raise ScrapingError(f"Timeout while loading job page: {e}")
        except Exception as e:
            if isinstance(e, JobScraperError):
                raise
            raise ScrapingError(f"Failed to scrape job: {e}")
    
    def _is_valid_linkedin_job_url(self, url: str) -> bool:
        """
        Check if URL is a valid LinkedIn job URL.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ("http", "https") and
                "linkedin.com" in parsed.netloc and
                "/jobs/view/" in parsed.path
            )
        except Exception:
            return False
    
    def _is_login_required(self, page) -> bool:
        """
        Check if LinkedIn is requiring login.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if login is required, False otherwise
        """
        # Check for login form or auth wall
        login_selectors = [
            "form.login-form",
            ".authwall",
            "input[name='session_key']",
        ]
        
        for selector in login_selectors:
            try:
                if page.query_selector(selector):
                    return True
            except Exception:
                pass
        
        return False
    
    def _extract_job_data(self, page, url: str) -> Dict[str, Any]:
        """
        Extract job data from the page.
        
        Args:
            page: Playwright page object
            url: Job URL
            
        Returns:
            Dict with job information
        """
        job_data = {"url": url}
        
        # Extract job title
        try:
            title_elem = page.query_selector("h1.jobs-unified-top-card__job-title")
            if title_elem:
                job_data["title"] = title_elem.inner_text().strip()
        except Exception:
            job_data["title"] = None
        
        # Extract company name
        try:
            company_elem = page.query_selector(".jobs-unified-top-card__company-name")
            if company_elem:
                job_data["company"] = company_elem.inner_text().strip()
        except Exception:
            job_data["company"] = None
        
        # Extract location
        try:
            location_elem = page.query_selector(".jobs-unified-top-card__bullet")
            if location_elem:
                job_data["location"] = location_elem.inner_text().strip()
        except Exception:
            job_data["location"] = None
        
        # Extract job description
        try:
            desc_elem = page.query_selector(".jobs-description__content")
            if desc_elem:
                # Get text content and clean it up
                description = desc_elem.inner_text()
                # Remove excessive whitespace
                description = re.sub(r'\n\s*\n', '\n\n', description)
                description = description.strip()
                job_data["description"] = description
        except Exception:
            job_data["description"] = None
        
        # Extract posted date
        try:
            posted_elem = page.query_selector(".jobs-unified-top-card__posted-date")
            if posted_elem:
                job_data["posted_date"] = posted_elem.inner_text().strip()
        except Exception:
            job_data["posted_date"] = None
        
        # Extract job criteria (employment type, seniority, etc.)
        try:
            criteria_items = page.query_selector_all(".jobs-unified-top-card__job-insight")
            criteria = {}
            for item in criteria_items:
                text = item.inner_text().strip()
                # Parse criteria (format: "Label\nValue")
                parts = text.split('\n', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower().replace(' ', '_')
                    value = parts[1].strip()
                    criteria[key] = value
            
            job_data["employment_type"] = criteria.get("employment_type")
            job_data["seniority_level"] = criteria.get("seniority_level")
            job_data["job_function"] = criteria.get("job_function")
            job_data["industries"] = criteria.get("industries")
        except Exception:
            job_data["employment_type"] = None
            job_data["seniority_level"] = None
            job_data["job_function"] = None
            job_data["industries"] = None
        
        return job_data
    
    def scrape_with_fallback(self, url: str, manual_description: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape job with fallback to manual description.
        
        If scraping fails, allows providing a manual description.
        
        Args:
            url: LinkedIn job URL
            manual_description: Optional manual job description
            
        Returns:
            Dict with job information
        """
        try:
            return self.scrape_job(url)
        except Exception as e:
            if manual_description:
                return {
                    "url": url,
                    "title": None,
                    "company": None,
                    "location": None,
                    "description": manual_description,
                    "posted_date": None,
                    "employment_type": None,
                    "seniority_level": None,
                    "scraping_error": str(e),
                }
            raise


def scrape_linkedin_job(url: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to scrape a LinkedIn job.
    
    Args:
        url: LinkedIn job URL
        config: Optional scraper configuration
        
    Returns:
        Dict with job information
    """
    scraper = LinkedInJobScraper(config)
    return scraper.scrape_job(url)
