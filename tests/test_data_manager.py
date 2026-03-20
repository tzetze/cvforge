"""
Unit tests for core.data_manager module
"""
import pytest
import tempfile
from pathlib import Path
from core.data_manager import load_cv_data, save_cv_data
from core.models import CVData, PersonalInfo, Experience, Achievement
from core.utils import CVDataNotFoundError, CVDataValidationError, CVDataParseError


class TestLoadCVData:
    """Tests for load_cv_data function"""
    
    def test_load_valid_cv_data(self):
        """Test loading valid CV data from YAML file"""
        cv_data = load_cv_data("tests/fixtures/sample_cv.yaml")
        
        assert isinstance(cv_data, CVData)
        assert cv_data.personal.name == "Alex Johnson"
        assert cv_data.personal.email == "alex.johnson@email.com"
        assert len(cv_data.experience) >= 2
        assert cv_data.experience[0].company == "TechCorp Inc."
        assert len(cv_data.experience[0].achievements) >= 3
    
    def test_load_nonexistent_file(self):
        """Test loading from non-existent file raises error"""
        with pytest.raises(Exception):  # Will raise FileNotFoundError or CVDataNotFoundError
            load_cv_data("nonexistent_file.yaml")
    
    def test_load_invalid_yaml(self):
        """Test loading invalid YAML raises error"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content:\n  - broken")
            temp_path = f.name
        
        try:
            with pytest.raises(Exception):  # Will raise ValidationError or CVDataParseError
                load_cv_data(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_load_missing_required_fields(self):
        """Test loading CV with missing required fields raises error"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("personal:\n  name: John\n")  # Missing email and other required fields
            temp_path = f.name
        
        try:
            with pytest.raises(Exception):  # Will raise ValidationError or CVDataValidationError
                load_cv_data(temp_path)
        finally:
            Path(temp_path).unlink()


class TestSaveCVData:
    """Tests for save_cv_data function"""
    
    def test_save_cv_data(self):
        """Test saving CV data to YAML file"""
        # Load sample data
        cv_data = load_cv_data("tests/fixtures/sample_cv.yaml")
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            save_cv_data(cv_data, temp_path)
            
            # Verify file exists and can be loaded
            assert Path(temp_path).exists()
            loaded_data = load_cv_data(temp_path)
            
            assert loaded_data.personal.name == cv_data.personal.name
            assert loaded_data.personal.email == cv_data.personal.email
            assert len(loaded_data.experience) == len(cv_data.experience)
        finally:
            Path(temp_path).unlink()
    
    def test_save_creates_directory(self):
        """Test that save_cv_data creates parent directories if needed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "cv_data.yaml"
            cv_data = load_cv_data("tests/fixtures/sample_cv.yaml")
            
            save_cv_data(cv_data, str(output_path))
            
            assert output_path.exists()
            loaded_data = load_cv_data(str(output_path))
            assert loaded_data.personal.name == cv_data.personal.name


class TestCVDataRoundTrip:
    """Tests for loading and saving CV data (round-trip)"""
    
    def test_roundtrip_preserves_data(self):
        """Test that loading and saving preserves all data"""
        original = load_cv_data("tests/fixtures/sample_cv.yaml")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            save_cv_data(original, temp_path)
            loaded = load_cv_data(temp_path)
            
            # Compare key fields
            assert loaded.personal.name == original.personal.name
            assert loaded.personal.email == original.personal.email
            assert loaded.personal.phone == original.personal.phone
            assert len(loaded.experience) == len(original.experience)
            
            # Compare first experience
            assert loaded.experience[0].company == original.experience[0].company
            assert loaded.experience[0].position == original.experience[0].position
            assert len(loaded.experience[0].achievements) == len(original.experience[0].achievements)
            
            # Compare first achievement
            assert loaded.experience[0].achievements[0].text == original.experience[0].achievements[0].text
            assert loaded.experience[0].achievements[0].impact == original.experience[0].achievements[0].impact
        finally:
            Path(temp_path).unlink()

