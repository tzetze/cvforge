"""
Custom exceptions for CVForge application.

Provides specific exception types for different error scenarios,
making error handling more precise and informative.
"""


class CVForgeError(Exception):
    """Base exception for all CVForge errors."""
    pass


# Data-related exceptions
class DataError(CVForgeError):
    """Base exception for data-related errors."""
    pass


class CVDataNotFoundError(DataError):
    """Raised when CV data file is not found."""
    pass


class CVDataValidationError(DataError):
    """Raised when CV data fails validation."""
    
    def __init__(self, message: str, validation_errors: list = None):
        super().__init__(message)
        self.validation_errors = validation_errors or []


class CVDataParseError(DataError):
    """Raised when CV data cannot be parsed."""
    pass


# LLM-related exceptions
class LLMError(CVForgeError):
    """Base exception for LLM-related errors."""
    pass


class LLMProviderError(LLMError):
    """Raised when LLM provider encounters an error."""
    pass


class LLMConnectionError(LLMError):
    """Raised when cannot connect to LLM service."""
    pass


class LLMResponseError(LLMError):
    """Raised when LLM response is invalid or unexpected."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""
    pass


# Generation-related exceptions
class GenerationError(CVForgeError):
    """Base exception for CV generation errors."""
    pass


class PDFGenerationError(GenerationError):
    """Raised when PDF generation fails."""
    pass


class TemplateError(GenerationError):
    """Raised when template rendering fails."""
    pass


class ContentSelectionError(GenerationError):
    """Raised when content selection fails."""
    pass


# Job-related exceptions
class JobError(CVForgeError):
    """Base exception for job-related errors."""
    pass


class JobScrapingError(JobError):
    """Raised when job scraping fails."""
    pass


class JobParsingError(JobError):
    """Raised when job description parsing fails."""
    pass


# Configuration exceptions
class ConfigError(CVForgeError):
    """Base exception for configuration errors."""
    pass


class MissingConfigError(ConfigError):
    """Raised when required configuration is missing."""
    pass


class InvalidConfigError(ConfigError):
    """Raised when configuration is invalid."""
    pass


# Web application exceptions
class WebError(CVForgeError):
    """Base exception for web application errors."""
    pass


class RouteError(WebError):
    """Raised when route handling fails."""
    pass


class FormValidationError(WebError):
    """Raised when form validation fails."""
    
    def __init__(self, message: str, field_errors: dict = None):
        super().__init__(message)
        self.field_errors = field_errors or {}

