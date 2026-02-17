"""
Unit tests for MCP tools.

These tests verify that MCP tools correctly use the shared backend
and return properly structured JSON responses.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path


class TestInitSteeringTool:
    """Tests for init_steering MCP tool."""
    
    @pytest.mark.asyncio
    async def test_init_steering_success(self):
        """Test successful init workflow execution."""
        from mcp_server.tools.init_steering import init_steering
        
        # Mock the shared workflow
        with patch("mcp_server.tools.init_steering.SharedInitWorkflow") as mock_workflow_class:
            # Create mock workflow instance
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow
            
            # Mock successful execution
            from hiveforge.steering.shared.base import WorkflowResult
            mock_result = WorkflowResult(
                success=True,
                message="Successfully initialized steering files (5 files created)",
                files_created=[
                    ".kiro/steering/tech-stack.md",
                    ".kiro/steering/architecture.md"
                ],
                metadata={
                    "autonomous": True,
                    "auto_discover": True,
                    "confidence_threshold": 0.7,
                    "files_count": 5
                }
            )
            mock_workflow.execute.return_value = mock_result
            
            # Execute tool
            ctx = Mock()
            result = await init_steering(
                ctx,
                project_root=".",
                auto_discover=True,
                autonomous=True,
                confidence_threshold=0.7
            )
            
            # Verify workflow was created with correct parameters
            mock_workflow_class.assert_called_once_with(
                project_root=".",
                auto_discover=True,
                autonomous=True,
                confidence_threshold=0.7
            )
            
            # Verify workflow was executed
            mock_workflow.execute.assert_called_once()
            
            # Verify result structure
            assert result["status"] == "success"
            assert result["message"] == "Successfully initialized steering files (5 files created)"
            assert len(result["files_created"]) == 2
            assert result["autonomous"] == True
            assert result["files_count"] == 5
    
    @pytest.mark.asyncio
    async def test_init_steering_failure(self):
        """Test init workflow failure handling."""
        from mcp_server.tools.init_steering import init_steering
        
        # Mock the shared workflow to raise an exception
        with patch("mcp_server.tools.init_steering.SharedInitWorkflow") as mock_workflow_class:
            mock_workflow_class.side_effect = Exception("Test error")
            
            # Execute tool
            ctx = Mock()
            result = await init_steering(ctx, project_root=".")
            
            # Verify error handling
            assert result["status"] == "failed"
            assert "Test error" in result["message"]
            assert len(result["errors"]) == 1


class TestUpdateSteeringTool:
    """Tests for update_steering MCP tool."""
    
    @pytest.mark.asyncio
    async def test_update_steering_success(self):
        """Test successful update workflow execution."""
        from mcp_server.tools.update_steering import update_steering
        
        # Mock the shared workflow
        with patch("mcp_server.tools.update_steering.SharedUpdateWorkflow") as mock_workflow_class:
            # Create mock workflow instance
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow
            
            # Mock successful execution
            from hiveforge.steering.shared.base import WorkflowResult
            mock_result = WorkflowResult(
                success=True,
                message="Successfully updated steering files (3 files modified)",
                files_modified=[
                    ".kiro/steering/tech-stack.md",
                    ".kiro/steering/architecture.md"
                ],
                warnings=["1 customization detected"],
                metadata={
                    "incremental": True,
                    "preserve_customizations": True,
                    "files_count": 2,
                    "customizations_detected": 1
                }
            )
            mock_workflow.execute.return_value = mock_result
            
            # Execute tool
            ctx = Mock()
            result = await update_steering(
                ctx,
                project_root=".",
                files_to_update=None,
                preserve_customizations=True,
                incremental=True
            )
            
            # Verify workflow was created with correct parameters
            mock_workflow_class.assert_called_once_with(
                project_root=".",
                files_to_update=None,
                preserve_customizations=True,
                incremental=True
            )
            
            # Verify result structure
            assert result["status"] == "success"
            assert len(result["files_modified"]) == 2
            assert len(result["warnings"]) == 1
            assert result["customizations_detected"] == 1


class TestValidateSteeringTool:
    """Tests for validate_steering MCP tool."""
    
    @pytest.mark.asyncio
    async def test_validate_steering_success(self):
        """Test successful validation workflow execution."""
        from mcp_server.tools.validate_steering import validate_steering
        
        # Mock the shared workflow
        with patch("mcp_server.tools.validate_steering.SharedValidateWorkflow") as mock_workflow_class:
            # Create mock workflow instance
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow
            
            # Mock successful execution
            from hiveforge.steering.shared.base import WorkflowResult
            mock_result = WorkflowResult(
                success=True,
                message="All validation checks passed",
                warnings=[],
                errors=[],
                metadata={
                    "files_checked": 5,
                    "critical_issues": 0,
                    "warnings": 0,
                    "info": 2,
                    "overall_status": "valid",
                    "strict_mode": False,
                    "use_llm": True
                }
            )
            mock_workflow.execute.return_value = mock_result
            
            # Execute tool
            ctx = Mock()
            result = await validate_steering(
                ctx,
                project_root=".",
                strict=False,
                use_llm=True
            )
            
            # Verify workflow was created with correct parameters
            mock_workflow_class.assert_called_once_with(
                project_root=".",
                strict=False,
                use_llm=True
            )
            
            # Verify result structure
            assert result["status"] == "success"
            assert result["files_checked"] == 5
            assert result["critical_issues"] == 0
            assert result["overall_status"] == "valid"


class TestResetSteeringTool:
    """Tests for reset_steering MCP tool."""
    
    @pytest.mark.asyncio
    async def test_reset_steering_success(self):
        """Test successful reset workflow execution."""
        from mcp_server.tools.reset_steering import reset_steering
        
        # Mock the shared workflow
        with patch("mcp_server.tools.reset_steering.SharedResetWorkflow") as mock_workflow_class:
            # Create mock workflow instance
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow
            
            # Mock successful execution
            from hiveforge.steering.shared.base import WorkflowResult
            mock_result = WorkflowResult(
                success=True,
                message="Successfully reset 5 file(s) to default templates",
                files_modified=[
                    ".kiro/steering/tech-stack.md",
                    ".kiro/steering/architecture.md"
                ],
                metadata={
                    "backup_location": ".kiro/backups/reset_20260217_143022",
                    "files_count": 5
                }
            )
            mock_workflow.execute.return_value = mock_result
            
            # Execute tool
            ctx = Mock()
            result = await reset_steering(
                ctx,
                project_root=".",
                file=None,
                confirm=False
            )
            
            # Verify workflow was created with correct parameters
            mock_workflow_class.assert_called_once_with(
                project_root=".",
                file=None,
                confirm=False
            )
            
            # Verify result structure
            assert result["status"] == "success"
            assert len(result["files_modified"]) == 2
            assert "backup_location" in result
            assert result["files_count"] == 5


class TestDiscoverDocsTool:
    """Tests for discover_docs MCP tool."""
    
    @pytest.mark.asyncio
    async def test_discover_docs_success(self):
        """Test successful discovery workflow execution."""
        from mcp_server.tools.discover_docs import discover_docs
        
        # Mock the shared workflow
        with patch("mcp_server.tools.discover_docs.SharedDiscoveryWorkflow") as mock_workflow_class:
            # Create mock workflow instance
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow
            
            # Mock successful execution
            from hiveforge.steering.shared.base import WorkflowResult
            mock_result = WorkflowResult(
                success=True,
                message="Discovery complete: 42 files found",
                warnings=["5 files skipped: too large"],
                metadata={
                    "files_discovered": 42,
                    "files_included": 37,
                    "commit_count": 0,
                    "include_git_history": False,
                    "max_discovery_files": 1000,
                    "max_file_size_mb": 10,
                    "discovery_method": "scalable"
                }
            )
            mock_workflow.execute.return_value = mock_result
            
            # Execute tool
            ctx = Mock()
            result = await discover_docs(
                ctx,
                project_root=".",
                include_git_history=False,
                max_discovery_files=1000,
                max_file_size_mb=10
            )
            
            # Verify workflow was created with correct parameters
            mock_workflow_class.assert_called_once_with(
                project_root=".",
                include_git_history=False,
                max_discovery_files=1000,
                max_file_size_mb=10
            )
            
            # Verify result structure
            assert result["status"] == "success"
            assert result["files_discovered"] == 42
            assert result["files_included"] == 37
            assert len(result["warnings"]) == 1
