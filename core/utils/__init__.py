"""
Utility modules for CVForge.

Provides logging, exception handling, and other utility functions.
"""

from core.utils.logger import get_logger, CVForgeLogger
from core.utils.exceptions import (
    # Base exceptions
    CVForgeError,
    
    # Data exceptions
    DataError,
    CVDataNotFoundError,
    CVDataValidationError,
    CVDataParseError,
    
    # LLM exceptions
    LLMError,
    LLMProviderError,
    LLMConnectionError,
    LLMResponseError,
    LLMRateLimitError,
    
    # Generation exceptions
    GenerationError,
    PDFGenerationError,
    TemplateError,
    ContentSelectionError,
    
    # Job exceptions
    JobError,
    JobScrapingError,
    JobParsingError,
    
    # Config exceptions
    ConfigError,
    MissingConfigError,
    InvalidConfigError,
    
    # Web exceptions
    WebError,
    RouteError,
    FormValidationError,
)

__all__ = [
    # Logger
    'get_logger',
    'CVForgeLogger',
    
    # Base exceptions
    'CVForgeError',
    
    # Data exceptions
    'DataError',
    'CVDataNotFoundError',
    'CVDataValidationError',
    'CVDataParseError',
    
    # LLM exceptions
    'LLMError',
    'LLMProviderError',
    'LLMConnectionError',
    'LLMResponseError',
    'LLMRateLimitError',
    
    # Generation exceptions
    'GenerationError',
    'PDFGenerationError',
    'TemplateError',
    'ContentSelectionError',
    
    # Job exceptions
    'JobError',
    'JobScrapingError',
    'JobParsingError',
    
    # Config exceptions
    'ConfigError',
    'MissingConfigError',
    'InvalidConfigError',
    
    # Web exceptions
    'WebError',
    'RouteError',
    'FormValidationError',
]

