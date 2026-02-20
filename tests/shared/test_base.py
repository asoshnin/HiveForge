"""Tests for shared workflow base classes."""

import pytest
from pathlib import Path
from hiveforge.steering.shared.base import (
    SharedWorkflowBase,
    WorkflowResult,
)


class TestWorkflowResult:
    """Test WorkflowResult class."""
    
    def test_success_result_to_dict(self):
        """Test converting success result to dictionary."""
        result = WorkflowResult(
            success=True,
            message="Operation completed",
            files_created=["file1.md", "file2.md"]
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["status"] == "success"
        assert result_dict["message"] == "Operation completed"
        assert result_dict["files_created"] == ["file1.md", "file2.md"]
    
    def test_failure_result_to_dict(self):
        """Test converting failure result to dictionary."""
        result = WorkflowResult(
            success=False,
            message="Operation failed",
            errors=["Error 1", "Error 2"]
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["status"] == "failed"
        assert result_dict["message"] == "Operation failed"
        assert result_dict["errors"] == ["Error 1", "Error 2"]
    
    def test_format_for_cli_success(self):
        """Test formatting success result for CLI."""
        result = WorkflowResult(
            success=True,
            message="Files created successfully",
            files_created=["conventions.md", "architecture.md"]
        )
        
        output = result.format_for_cli()
        
        assert "✓ Files created successfully" in output
        assert "+ conventions.md" in output
        assert "+ architecture.md" in output
    
    def test_format_for_cli_failure(self):
        """Test formatting failure result for CLI."""
        result = WorkflowResult(
            success=False,
            message="Operation failed",
            errors=["File not found"]
        )
        
        output = result.format_for_cli()
        
        assert "✗ Operation failed" in output
        assert "✗ File not found" in output
    
    def test_format_for_cli_with_warnings(self):
        """Test formatting result with warnings for CLI."""
        result = WorkflowResult(
            success=True,
            message="Completed with warnings",
            warnings=["Warning 1", "Warning 2"]
        )
        
        output = result.format_for_cli()
        
        assert "⚠ Warning 1" in output
        assert "⚠ Warning 2" in output


class ConcreteWorkflow(SharedWorkflowBase):
    """Concrete implementation for testing."""
    
    def execute(self) -> WorkflowResult:
        """Execute workflow."""
        return self._create_success_result("Executed successfully")


class TestSharedWorkflowBase:
    """Test SharedWorkflowBase class."""
    
    def test_init_with_valid_project_root(self, tmp_path):
        """Test initialization with valid project root."""
        workflow = ConcreteWorkflow(project_root=tmp_path)
        
        assert workflow.project_root == tmp_path.resolve()
        assert workflow.config == {}
    
    def test_init_with_config(self, tmp_path):
        """Test initialization with configuration."""
        config = {"key": "value"}
        workflow = ConcreteWorkflow(project_root=tmp_path, config=config)
        
        assert workflow.config == config
    
    def test_init_with_nonexistent_project_root(self):
        """Test initialization with nonexistent project root."""
        with pytest.raises(ValueError, match="Project root does not exist"):
            ConcreteWorkflow(project_root="/nonexistent/path")
    
    def test_init_with_file_as_project_root(self, tmp_path):
        """Test initialization with file instead of directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")
        
        with pytest.raises(ValueError, match="Project root is not a directory"):
            ConcreteWorkflow(project_root=file_path)
    
    def test_resolve_path_relative(self, tmp_path):
        """Test resolving relative path."""
        workflow = ConcreteWorkflow(project_root=tmp_path)
        
        resolved = workflow._resolve_path("subdir/file.txt")
        
        assert resolved == (tmp_path / "subdir" / "file.txt").resolve()
    
    def test_resolve_path_absolute(self, tmp_path):
        """Test resolving absolute path."""
        workflow = ConcreteWorkflow(project_root=tmp_path)
        absolute_path = Path("/absolute/path")
        
        resolved = workflow._resolve_path(absolute_path)
        
        assert resolved == absolute_path
    
    def test_get_steering_dir(self, tmp_path):
        """Test getting steering directory path."""
        workflow = ConcreteWorkflow(project_root=tmp_path)
        
        steering_dir = workflow._get_steering_dir()
        
        assert steering_dir == tmp_path / ".kiro" / "steering"
    
    def test_ensure_steering_dir(self, tmp_path):
        """Test ensuring steering directory exists."""
        workflow = ConcreteWorkflow(project_root=tmp_path)
        
        workflow._ensure_steering_dir()
        
        assert (tmp_path / ".kiro" / "steering").exists()
        assert (tmp_path / ".kiro" / "steering").is_dir()
    
    def test_handle_error(self, tmp_path):
        """Test error handling."""
        workflow = ConcreteWorkflow(project_root=tmp_path)
        error = ValueError("Test error")
        
        result = workflow.handle_error(error)
        
        assert result.success is False
        assert "Test error" in result.message
        assert "Test error" in result.errors
    
    def test_create_success_result(self, tmp_path):
        """Test creating success result."""
        workflow = ConcreteWorkflow(project_root=tmp_path)
        
        result = workflow._create_success_result(
            "Success",
            files_created=["file1.md"]
        )
        
        assert result.success is True
        assert result.message == "Success"
        assert result.files_created == ["file1.md"]
    
    def test_create_failure_result(self, tmp_path):
        """Test creating failure result."""
        workflow = ConcreteWorkflow(project_root=tmp_path)
        
        result = workflow._create_failure_result(
            "Failed",
            errors=["Error 1"]
        )
        
        assert result.success is False
        assert result.message == "Failed"
        assert result.errors == ["Error 1"]
    
    def test_execute(self, tmp_path):
        """Test execute method."""
        workflow = ConcreteWorkflow(project_root=tmp_path)
        
        result = workflow.execute()
        
        assert result.success is True
        assert result.message == "Executed successfully"
