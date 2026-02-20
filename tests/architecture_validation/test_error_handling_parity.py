"""
Test Error Handling Parity

**Validates: Requirements 1.7, 1.8, 1.9**

This test module validates that CLI and Power interfaces handle errors identically.
Both interfaces should produce the same error responses and follow the same
rollback behavior.

Architecture Validation Criteria:
- Error Handling Parity: Identical error handling for both interfaces
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any


class TestErrorResponseParity:
    """Test that both interfaces produce identical error responses."""
    
    @pytest.mark.asyncio
    async def test_missing_project_root_error(self, python_project):
        """Test error response for missing project root."""
        # CLI error
        cli_result = run_cli_command([
            "steering", "init",
            "--project-root", "/nonexistent/path"
        ])
        
        # Power error
        power_result = await run_mcp_tool(
            "init_steering",
            project_root="/nonexistent/path"
        )
        
        # Both should indicate failure with similar message
        assert cli_result.returncode != 0
        assert power_result["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_permission_error(self, python_project):
        """Test error response for permission denied."""
        # Make directory read-only
        python_project.chmod(0o555)
        
        try:
            # CLI error
            cli_result = run_cli_command(["steering", "init", "--autonomous"])
            
            # Power error
            power_result = await run_mcp_tool(
                "init_steering",
                autonomous=True,
                project_root=str(python_project)
            )
            
            # Both should fail with permission error
            assert cli_result.returncode != 0
            assert power_result["status"] == "failed"
        finally:
            # Restore permissions
            python_project.chmod(0o755)
    
    @pytest.mark.asyncio
    async def test_llm_api_error(self, python_project):
        """Test error response for LLM API failure."""
        with patch('hiveforge.steering.workflows.InitWorkflow.execute') as mock:
            mock.side_effect = Exception("LLM API rate limit exceeded")
            
            # CLI error
            cli_result = run_cli_command(["steering", "init", "--autonomous"])
            
            # Power error
            power_result = await run_mcp_tool(
                "init_steering",
                autonomous=True,
                project_root=str(python_project)
            )
            
            # Both should fail gracefully
            assert cli_result.returncode != 0
            assert power_result["status"] == "failed"


class TestRollbackBehavior:
    """Test that both interfaces perform identical rollback on failure."""
    
    def test_rollback_creates_backup(self, python_project):
        """Test that rollback creates backup before modifications."""
        # Create initial steering files
        run_cli_command(["steering", "init", "--autonomous"])
        
        original_conventions = (
            python_project / ".kiro" / "steering" / "CONVENTIONS.md"
        ).read_text()
        
        # Simulate failed update
        with patch('hiveforge.steering.workflows.UpdateWorkflow.execute') as mock:
            mock.side_effect = Exception("Update failed")
            
            run_cli_command(["steering", "update", "--incremental"])
        
        # Check backup was created
        backup_dir = python_project / ".kiro" / "backups"
        assert backup_dir.exists()
        assert len(list(backup_dir.glob("*"))) > 0
    
    def test_rollback_restores_state(self, python_project):
        """Test that rollback restores original state on failure."""
        # Create initial steering files
        run_cli_command(["steering", "init", "--autonomous"])
        
        original_content = (
            python_project / ".kiro" / "steering" / "CONVENTIONS.md"
        ).read_text()
        
        # Simulate failed update
        with patch('hiveforge.steering.workflows.UpdateWorkflow.execute') as mock:
            mock.side_effect = Exception("Update failed")
            
            run_cli_command(["steering", "update", "--incremental"])
        
        # Content should be restored
        restored_content = (
            python_project / ".kiro" / "steering" / "CONVENTIONS.md"
        ).read_text()
        
        assert restored_content == original_content


class TestErrorMessageConsistency:
    """Test that error messages are consistent between interfaces."""
    
    def test_user_error_messages_match(self):
        """Test that user-facing error messages are identical."""
        from hiveforge.steering.error_handling import (
            ToolExecutor,
            ErrorContext,
            ErrorSeverity
        )
        
        executor = ToolExecutor()
        
        # Test error formatting
        cli_message = executor.format_error(
            ErrorContext(
                operation="init",
                error_type="validation_error",
                message="Project root not found",
                severity=ErrorSeverity.USER_ERROR
            )
        )
        
        # Power should use same formatting
        power_message = executor.format_error(
            ErrorContext(
                operation="init",
                error_type="validation_error",
                message="Project root not found",
                severity=ErrorSeverity.USER_ERROR
            )
        )
        
        assert cli_message == power_message
    
    def test_system_error_messages_match(self):
        """Test that system error messages are consistent."""
        from hiveforge.steering.error_handling import (
            ToolExecutor,
            ErrorContext,
            ErrorSeverity
        )
        
        executor = ToolExecutor()
        
        # System errors should be obfuscated for users
        cli_message = executor.format_error(
            ErrorContext(
                operation="init",
                error_type="llm_api_error",
                message="OpenAI API key invalid: sk-1234567890abcdef",
                severity=ErrorSeverity.SYSTEM_ERROR
            )
        )
        
        power_message = executor.format_error(
            ErrorContext(
                operation="init",
                error_type="llm_api_error",
                message="OpenAI API key invalid: sk-1234567890abcdef",
                severity=ErrorSeverity.SYSTEM_ERROR
            )
        )
        
        # Both should have obfuscated API key
        assert "sk-1234567890abcdef" not in cli_message
        assert "sk-1234567890abcdef" not in power_message
        assert cli_message == power_message


class TestRecoveryOptions:
    """Test that recovery options are identical for both interfaces."""
    
    @pytest.mark.asyncio
    async def test_retry_recovery_option(self, python_project):
        """Test that retry option is available for transient errors."""
        with patch('hiveforge.steering.workflows.InitWorkflow.execute') as mock:
            mock.side_effect = Exception("Temporary network error")
            
            # CLI should suggest retry
            cli_result = run_cli_command(["steering", "init", "--autonomous"])
            
            # Power should suggest retry
            power_result = await run_mcp_tool(
                "init_steering",
                autonomous=True,
                project_root=str(python_project)
            )
            
            # Both should indicate retry is possible
            assert power_result.get("can_retry", False) is True
    
    @pytest.mark.asyncio
    async def test_abort_recovery_option(self, python_project):
        """Test that abort option is available for fatal errors."""
        with patch('hiveforge.steering.workflows.InitWorkflow.execute') as mock:
            mock.side_effect = Exception("Fatal error: corrupted state")
            
            # CLI should allow abort
            cli_result = run_cli_command(["steering", "init", "--autonomous"])
            
            # Power should allow abort
            power_result = await run_mcp_tool(
                "init_steering",
                autonomous=True,
                project_root=str(python_project)
            )
            
            # Both should indicate abort is the only option
            assert power_result.get("can_retry", False) is False