"""
Logging configuration for CVForge.

Provides centralized logging setup with file and console handlers,
structured logging, and different log levels for different components.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class CVForgeLogger:
    """Centralized logger for CVForge application."""
    
    _loggers = {}
    _initialized = False
    
    @classmethod
    def setup(
        cls,
        log_dir: Optional[Path] = None,
        log_level: str = "INFO",
        console_output: bool = True,
        file_output: bool = True
    ):
        """
        Set up logging configuration.
        
        Args:
            log_dir: Directory for log files (default: ./logs)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_output: Enable console logging
            file_output: Enable file logging
        """
        if cls._initialized:
            return
        
        # Create log directory
        if log_dir is None:
            log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger("cvforge")
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(simple_formatter)
            root_logger.addHandler(console_handler)
        
        # File handlers
        if file_output:
            # General log file
            general_log = log_dir / f"cvforge_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(general_log, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(file_handler)
            
            # Error log file
            error_log = log_dir / f"cvforge_errors_{datetime.now().strftime('%Y%m%d')}.log"
            error_handler = logging.FileHandler(error_log, encoding='utf-8')
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(error_handler)
        
        cls._initialized = True
        root_logger.info("Logging system initialized")
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance for a specific module.
        
        Args:
            name: Logger name (typically __name__)
        
        Returns:
            Logger instance
        """
        if not cls._initialized:
            cls.setup()
        
        if name not in cls._loggers:
            logger = logging.getLogger(f"cvforge.{name}")
            cls._loggers[name] = logger
        
        return cls._loggers[name]


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return CVForgeLogger.get_logger(name)


# Initialize logging on import
CVForgeLogger.setup()

