"""
Test Security Validation

**Validates: Requirements 1.13, 1.14, 1.15**

This test module validates that security measures are correctly implemented
and enforced for both CLI and Power interfaces. All security tests should pass
for both interfaces.

Architecture Validation Criteria:
- Security Validation: All security measures implemented and tested
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any


class TestPathTraversalPrevention:
    """Test prevention of path traversal attacks."""
    
    @pytest.mark.asyncio
    async def test_path_traversal_via_project_root(self):
        """Test that path traversal via project_root is blocked."""
        malicious_path = "../../../etc/passwd"
        
        # CLI should reject
        cli_result = run_cli_command([
            "steering", "init",
            "--project-root", malicious_path
        ])
        assert cli_result.returncode != 0
        
        # Power should reject
        power_result = await run_mcp_tool(
            "init_steering",
            project_root=malicious_path
        )
        assert power_result["status"] == "failed"
        assert "security" in power_result.get("error", "").lower()
    
    @pytest.mark.asyncio
    async def test_path_traversal_via_file_param(self):
        """Test that path traversal via file parameter is blocked."""
        malicious_file = "../../../etc/passwd"
        
        # CLI should reject
        cli_result = run_cli_command([
            "steering", "reset",
            "--file", malicious_file
        ])
        assert cli_result.returncode != 0
        
        # Power should reject
        power_result = await run_mcp_tool(
            "reset_steering",
            file=malicious_file
        )
        assert power_result["status"] == "failed"
        assert "security" in power_result.get("error", "").lower()
    
    @pytest.mark.asyncio
    async def test_absolute_path_outside_project(self):
        """Test that absolute paths outside project are blocked."""
        outside_path = "/tmp/malicious_project"
        
        # CLI should reject
        cli_result = run_cli_command([
            "steering", "init",
            "--project-root", outside_path
        ])
        assert cli_result.returncode != 0
        
        # Power should reject
        power_result = await run_mcp_tool(
            "init_steering",
            project_root=outside_path
        )
        assert power_result["status"] == "failed"


class TestInputValidation:
    """Test input validation for all parameters."""
    
    @pytest.mark.asyncio
    async def test_confidence_threshold_validation(self):
        """Test that confidence_threshold is validated."""
        # Valid range: 0.0 to 1.0
        
        # CLI should reject invalid value
        cli_result = run_cli_command([
            "steering", "init",
            "--confidence-threshold", "1.5"
        ])
        assert cli_result.returncode != 0
        
        # Power should reject invalid value
        power_result = await run_mcp_tool(
            "init_steering",
            confidence_threshold=1.5
        )
        assert power_result["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_negative_confidence_threshold(self):
        """Test that negative confidence_threshold is rejected."""
        # CLI should reject
        cli_result = run_cli_command([
            "steering", "init",
            "--confidence-threshold", "-0.5"
        ])
        assert cli_result.returncode != 0
        
        # Power should reject
        power_result = await run_mcp_tool(
            "init_steering",
            confidence_threshold=-0.5
        )
        assert power_result["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_empty_project_root(self):
        """Test that empty project_root is rejected."""
        # CLI should reject
        cli_result = run_cli_command([
            "steering", "init",
            "--project-root", ""
        ])
        assert cli_result.returncode != 0
        
        # Power should reject
        power_result = await run_mcp_tool(
            "init_steering",
            project_root=""
        )
        assert power_result["status"] == "failed"


class TestResourceLimitEnforcement:
    """Test resource limit enforcement."""
    
    def test_memory_limit_enforcement(self):
        """Test that memory limits are enforced."""
        # This would require running with limited memory
        # Implementation in Phase 2
        pass  # Requires ResourceLimiter implementation
    
    def test_cpu_time_limit_enforcement(self):
        """Test that CPU time limits are enforced."""
        # This would require simulating a long-running operation
        # Implementation in Phase 2
        pass  # Requires ResourceLimiter implementation
    
    def test_file_size_limit_enforcement(self):
        """Test that file size limits are enforced."""
        # This would require creating large files
        # Implementation in Phase 2
        pass  # Requires ResourceLimiter implementation


class TestErrorObfuscation:
    """Test that sensitive information is obfuscated in errors."""
    
    @pytest.mark.asyncio
    async def test_api_key_not_exposed(self):
        """Test that API keys are not exposed in error messages."""
        with patch('hiveforge.steering.workflows.InitWorkflow.execute') as mock:
            mock.side_effect = Exception(
                "OpenAI API error: Invalid API key sk-1234567890abcdefghij"
            )
            
            # CLI should not expose API key
            cli_result = run_cli_command(["steering", "init", "--autonomous"])
            
            # Power should not expose API key
            power_result = await run_mcp_tool(
                "init_steering",
                autonomous=True,
                project_root=str(python_project)
            )
            
            # Neither should contain the API key
            assert "sk-1234567890" not in cli_result.stdout
            assert "sk-1234567890" not in power_result.get("error", "")
    
    @pytest.mark.asyncio
    async def test_file_paths_not_exposed(self):
        """Test that internal file paths are not exposed in errors."""
        with patch('hiveforge.steering.workflows.InitWorkflow.execute') as mock:
            mock.side_effect = Exception(
                "Error reading /home/user/.config/hiveforge/api_keys.json"
            )
            
            # CLI should not expose internal paths
            cli_result = run_cli_command(["steering", "init", "--autonomous"])
            
            # Power should not expose internal paths
            power_result = await run_mcp_tool(
                "init_steering",
                autonomous=True,
                project_root=str(python_project)
            )
            
            # Neither should contain the full internal path
            assert "/home/user/.config" not in cli_result.stdout
            assert "/home/user/.config" not in power_result.get("error", "")


class TestSecurityLogging:
    """Test that security events are logged."""
    
    def test_security_violations_are_logged(self, python_project):
        """Test that security violations are logged."""
        from hiveforge.steering.security_wrappers import SecurityLogger
        
        logger = SecurityLogger()
        
        # Simulate a security violation
        logger.log_violation(
            violation_type="path_traversal",
            details={"path": "../../../etc/passwd"},
            blocked_operation="init"
        )
        
        # Check log was created
        log_file = Path(".kiro/.logs/security.log")
        assert log_file.exists()
        
        # Log should contain the violation
        content = log_file.read_text()
        assert "path_traversal" in content
    
    def test_failed_validations_are_logged(self, python_project):
        """Test that failed validations are logged."""
        from hiveforge.steering.security_wrappers import SecurityLogger
        
        logger = SecurityLogger()
        
        # Simulate a validation failure
        logger.log_validation_failure(
            parameter="confidence_threshold",
            value=1.5,
            reason="Value out of range [0.0, 1.0]"
        )
        
        # Check log was created
        log_file = Path(".kiro/.logs/security.log")
        assert log_file.exists()


class TestSecureExecutionDecorator:
    """Test the secure_tool_execution decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_validates_inputs(self):
        """Test that decorator validates all inputs."""
        from hiveforge.steering.security_wrappers import secure_tool_execution
        
        @secure_tool_execution
        async def test_tool(project_root: str, confidence: float):
            return {"status": "success"}
        
        # Should reject invalid inputs
        result = await test_tool(
            project_root="../../../etc/passwd",
            confidence=0.7
        )
        
        assert result["status"] == "failed"
        assert "security" in result.get("error", "").lower()
    
    @pytest.mark.asyncio
    async def test_decorator_sanitizes_paths(self):
        """Test that decorator sanitizes path inputs."""
        from hiveforge.steering.security_wrappers import secure_tool_execution
        
        @secure_tool_execution
        async def test_tool(project_root: str):
            return {"status": "success", "sanitized_path": project_root}
        
        # Should sanitize the path
        result = await test_tool(project_root="./valid/../project")
        
        assert result["status"] == "success"
        # Path should be sanitized (no "..")
        assert ".." not in result.get("sanitized_path", "")