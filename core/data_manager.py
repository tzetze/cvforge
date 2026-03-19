"""
Data manager for loading, saving, and validating CV data and settings.

This module provides the core functionality for working with YAML files,
including validation using Pydantic models and error handling.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import ValidationError

from core.models import CVData, Settings


class DataManagerError(Exception):
    """Base exception for data manager errors."""
    pass


class FileNotFoundError(DataManagerError):
    """Raised when a required file is not found."""
    pass


class ValidationError(DataManagerError):
    """Raised when data validation fails."""
    pass


class DataManager:
    """
    Manages loading, saving, and validating CV data and settings.
    
    This class provides a clean interface for working with YAML files
    and ensures all data is validated using Pydantic models.
    """
    
    def __init__(self, cv_data_path: Optional[str] = None, settings_path: Optional[str] = None):
        """
        Initialize the data manager.
        
        Args:
            cv_data_path: Path to CV data YAML file (default: config/cv_data.yaml)
            settings_path: Path to settings YAML file (default: config/settings.yaml)
        """
        self.cv_data_path = cv_data_path or "config/cv_data.yaml"
        self.settings_path = settings_path or "config/settings.yaml"
        
        self._cv_data: Optional[CVData] = None
        self._settings: Optional[Settings] = None
    
    def load_cv_data(self, path: Optional[str] = None) -> CVData:
        """
        Load and validate CV data from YAML file.
        
        Args:
            path: Optional path to CV data file (overrides default)
            
        Returns:
            Validated CVData object
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValidationError: If the data fails validation
        """
        file_path = path or self.cv_data_path
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CV data file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data is None:
                raise ValidationError(f"CV data file is empty: {file_path}")
            
            # Validate using Pydantic model
            cv_data = CVData(**data)
            self._cv_data = cv_data
            return cv_data
            
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML in CV data file: {e}")
        except ValidationError as e:
            raise ValidationError(f"CV data validation failed: {e}")
        except Exception as e:
            raise DataManagerError(f"Error loading CV data: {e}")
    
    def save_cv_data(self, cv_data: CVData, path: Optional[str] = None) -> None:
        """
        Save CV data to YAML file.
        
        Args:
            cv_data: CVData object to save
            path: Optional path to save to (overrides default)
            
        Raises:
            DataManagerError: If saving fails
        """
        file_path = path or self.cv_data_path
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Convert Pydantic model to dict
            data = cv_data.model_dump(exclude_none=True)
            
            # Save to YAML
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False
                )
            
            self._cv_data = cv_data
            
        except Exception as e:
            raise DataManagerError(f"Error saving CV data: {e}")
    
    def load_settings(self, path: Optional[str] = None) -> Settings:
        """
        Load and validate settings from YAML file.
        
        Args:
            path: Optional path to settings file (overrides default)
            
        Returns:
            Validated Settings object
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValidationError: If the data fails validation
        """
        file_path = path or self.settings_path
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Settings file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data is None:
                raise ValidationError(f"Settings file is empty: {file_path}")
            
            # Replace environment variables in the data
            data = self._replace_env_vars(data)
            
            # Validate using Pydantic model
            settings = Settings(**data)
            self._settings = settings
            return settings
            
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML in settings file: {e}")
        except ValidationError as e:
            raise ValidationError(f"Settings validation failed: {e}")
        except Exception as e:
            raise DataManagerError(f"Error loading settings: {e}")
    
    def save_settings(self, settings: Settings, path: Optional[str] = None) -> None:
        """
        Save settings to YAML file.
        
        Args:
            settings: Settings object to save
            path: Optional path to save to (overrides default)
            
        Raises:
            DataManagerError: If saving fails
        """
        file_path = path or self.settings_path
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Convert Pydantic model to dict
            data = settings.model_dump(exclude_none=True)
            
            # Save to YAML
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False
                )
            
            self._settings = settings
            
        except Exception as e:
            raise DataManagerError(f"Error saving settings: {e}")
    
    def _replace_env_vars(self, data: Any) -> Any:
        """
        Recursively replace environment variable placeholders in data.
        
        Replaces strings like "${VAR_NAME}" with the value of the environment variable.
        
        Args:
            data: Data structure to process
            
        Returns:
            Data with environment variables replaced
        """
        if isinstance(data, dict):
            return {k: self._replace_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_env_vars(item) for item in data]
        elif isinstance(data, str):
            # Check if string is an environment variable placeholder
            if data.startswith("${") and data.endswith("}"):
                var_name = data[2:-1]
                return os.environ.get(var_name, data)  # Return original if not found
            return data
        else:
            return data
    
    def validate_cv_data(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate CV data without loading from file.
        
        Args:
            data: Dictionary containing CV data
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            CVData(**data)
            return True, None
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def validate_settings(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate settings without loading from file.
        
        Args:
            data: Dictionary containing settings
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            Settings(**data)
            return True, None
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {e}"
    
    @property
    def cv_data(self) -> Optional[CVData]:
        """Get cached CV data (if loaded)."""
        return self._cv_data
    
    @property
    def settings(self) -> Optional[Settings]:
        """Get cached settings (if loaded)."""
        return self._settings
    
    def reload_cv_data(self) -> CVData:
        """Reload CV data from file."""
        return self.load_cv_data()
    
    def reload_settings(self) -> Settings:
        """Reload settings from file."""
        return self.load_settings()
    
    def get_cv_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the loaded CV data.
        
        Returns:
            Dictionary with CV statistics
            
        Raises:
            DataManagerError: If CV data is not loaded
        """
        if self._cv_data is None:
            raise DataManagerError("CV data not loaded. Call load_cv_data() first.")
        
        return {
            "name": self._cv_data.personal.name,
            "email": self._cv_data.personal.email,
            "total_experiences": len(self._cv_data.experience),
            "total_achievements": self._cv_data.get_total_achievements(),
            "total_skills": len(self._cv_data.get_all_skills()),
            "has_education": bool(self._cv_data.education),
            "has_certifications": bool(self._cv_data.certifications),
            "has_volunteer": bool(self._cv_data.volunteer),
            "has_projects": bool(self._cv_data.projects),
            "has_publications": bool(self._cv_data.publications),
            "has_awards": bool(self._cv_data.awards),
        }
    
    def export_to_dict(self, cv_data: Optional[CVData] = None) -> Dict[str, Any]:
        """
        Export CV data to dictionary format.
        
        Args:
            cv_data: Optional CVData object (uses cached if not provided)
            
        Returns:
            Dictionary representation of CV data
            
        Raises:
            DataManagerError: If no CV data is available
        """
        data = cv_data or self._cv_data
        if data is None:
            raise DataManagerError("No CV data available to export")
        
        return data.model_dump(exclude_none=True)
    
    def import_from_dict(self, data: Dict[str, Any]) -> CVData:
        """
        Import and validate CV data from dictionary.
        
        Args:
            data: Dictionary containing CV data
            
        Returns:
            Validated CVData object
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            cv_data = CVData(**data)
            self._cv_data = cv_data
            return cv_data
        except ValidationError as e:
            raise ValidationError(f"Import validation failed: {e}")


# Convenience functions for quick access
def load_cv_data(path: str = "config/cv_data.yaml") -> CVData:
    """
    Quick function to load CV data.
    
    Args:
        path: Path to CV data file
        
    Returns:
        Validated CVData object
    """
    manager = DataManager(cv_data_path=path)
    return manager.load_cv_data()


def load_settings(path: str = "config/settings.yaml") -> Settings:
    """
    Quick function to load settings.
    
    Args:
        path: Path to settings file
        
    Returns:
        Validated Settings object
    """
    manager = DataManager(settings_path=path)
    return manager.load_settings()


def save_cv_data(cv_data: CVData, path: str = "config/cv_data.yaml") -> None:
    """
    Quick function to save CV data.
    
    Args:
        cv_data: CVData object to save
        path: Path to save to
    """
    manager = DataManager(cv_data_path=path)
    manager.save_cv_data(cv_data, path)


def save_settings(settings: Settings, path: str = "config/settings.yaml") -> None:
    """
    Quick function to save settings.
    
    Args:
        settings: Settings object to save
        path: Path to save to
    """
    manager = DataManager(settings_path=path)
    manager.save_settings(settings, path)

