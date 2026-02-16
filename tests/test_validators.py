"""Unit tests for validators module."""
import pytest
from hiveforge.validators import validate_project_name


class TestValidateProjectName:
    """Test suite for validate_project_name function."""

    def test_valid_kebab_case_names(self):
        """Valid kebab-case names should pass validation."""
        assert validate_project_name("test-project") == "test-project"
        assert validate_project_name("my-app") == "my-app"
        assert validate_project_name("kiro-v05") == "kiro-v05"
        assert validate_project_name("project-123") == "project-123"

    def test_valid_single_word(self):
        """Single word lowercase names should pass validation."""
        assert validate_project_name("app") == "app"
        assert validate_project_name("project") == "project"

    def test_invalid_name_with_spaces(self):
        """Names with spaces should raise ValueError."""
        with pytest.raises(ValueError, match="Use kebab-case"):
            validate_project_name("Bad Name")

    def test_invalid_name_with_underscores(self):
        """Names with underscores should raise ValueError."""
        with pytest.raises(ValueError, match="Use kebab-case"):
            validate_project_name("test_project")

    def test_invalid_name_pascal_case(self):
        """PascalCase names should raise ValueError."""
        with pytest.raises(ValueError, match="Use kebab-case"):
            validate_project_name("TestProject")

    def test_invalid_name_with_dots(self):
        """Names with dots should raise ValueError."""
        with pytest.raises(ValueError, match="Use kebab-case"):
            validate_project_name("test.project")

    def test_empty_string_raises_error(self):
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_project_name("")

    def test_none_value_raises_error(self):
        """None value should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_project_name(None)

    @pytest.mark.parametrize("invalid_name", [
        "Bad Name",
        "test_project",
        "TestProject",
        "test.project",
        "project@name",
        "project name",
    ])
    def test_multiple_invalid_names(self, invalid_name):
        """Parametrized test for multiple invalid name formats."""
        with pytest.raises(ValueError):
            validate_project_name(invalid_name)
