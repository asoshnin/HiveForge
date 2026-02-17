"""
Test Orchestrator Integration

**Validates: Requirements 1.16, 1.17, 1.18**

This test module validates that the Power integrates correctly with the
KIRO Orchestrator via the standard Power framework.

Architecture Validation Criteria:
- Orchestrator Integration: Standard KIRO Power framework integration
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

# Add hiveforge-power to Python path
power_dir = Path(__file__).parent.parent.parent / "hiveforge-power"
if str(power_dir) not in sys.path:
    sys.path.insert(0, str(power_dir))


class TestKeywordActivation:
    """Test keyword activation behavior."""
    
    def test_keyword_configuration(self):
        """Test that keywords are properly configured in package.json."""
        # Read package.json
        package_json_path = Path("hiveforge-power/package.json")
        
        if package_json_path.exists():
            with open(package_json_path) as f:
                package_data = json.load(f)
            
            # Verify keywords exist
            assert "kiro" in package_data
            assert "activationKeywords" in package_data["kiro"]
            
            # Verify expected keywords
            keywords = package_data["kiro"]["activationKeywords"]
            assert "steering" in keywords
            assert "documentation" in keywords
            assert "onboarding" in keywords
    
    def test_keyword_detection_patterns(self):
        """Test that various keyword patterns are detected."""
        test_messages = [
            "Please generate steering files for my project",
            "I need help with project documentation",
            "Can you help with onboarding documentation?",
            "Update my steering files",
            "Initialize project setup files"
        ]
        
        keywords = ["steering", "documentation", "onboarding", "project setup"]
        
        for message in test_messages:
            # At least one keyword should match
            matches = [kw for kw in keywords if kw.lower() in message.lower()]
            assert len(matches) > 0, f"No keywords matched in: {message}"
    
    def test_power_metadata(self):
        """Test that Power metadata is correctly configured."""
        package_json_path = Path("hiveforge-power/package.json")
        
        if package_json_path.exists():
            with open(package_json_path) as f:
                package_data = json.load(f)
            
            # Verify Power metadata
            assert "kiro" in package_data
            kiro_config = package_data["kiro"]
            
            assert kiro_config["powerVersion"] == "1.0"
            assert kiro_config["displayName"] == "HiveForge Steering Assistant"
            assert kiro_config["category"] == "documentation"
            assert len(kiro_config["features"]) >= 5


class TestToolDiscovery:
    """Test MCP tool discovery via orchestrator."""
    
    @pytest.mark.asyncio
    async def test_all_tools_are_registered(self):
        """Test that all 5 tools are registered with FastMCP."""
        from mcp_server.tools import (
            init_steering,
            update_steering,
            validate_steering,
            reset_steering,
            discover_docs
        )
        
        # Verify all tools are importable
        assert init_steering is not None
        assert update_steering is not None
        assert validate_steering is not None
        assert reset_steering is not None
        assert discover_docs is not None
    
    @pytest.mark.asyncio
    async def test_tool_signatures(self):
        """Test that tools have correct async signatures."""
        from mcp_server.tools import init_steering, update_steering
        
        import inspect
        
        # All tools should be async functions
        assert inspect.iscoroutinefunction(init_steering)
        assert inspect.iscoroutinefunction(update_steering)
        
        # Check init_steering parameters
        sig = inspect.signature(init_steering)
        params = list(sig.parameters.keys())
        assert "ctx" in params
        assert "project_root" in params
        assert "auto_discover" in params
        assert "autonomous" in params
    
    def test_tool_documentation(self):
        """Test that tools have proper docstrings."""
        from mcp_server.tools import (
            init_steering,
            update_steering,
            validate_steering,
            reset_steering,
            discover_docs
        )
        
        # All tools should have docstrings
        assert init_steering.__doc__ is not None
        assert "Initialize steering files" in init_steering.__doc__
        
        assert update_steering.__doc__ is not None
        assert "Update existing steering files" in update_steering.__doc__
        
        assert validate_steering.__doc__ is not None
        assert "Validate steering files" in validate_steering.__doc__
        
        assert reset_steering.__doc__ is not None
        assert "Reset steering files" in reset_steering.__doc__
        
        assert discover_docs.__doc__ is not None
        assert "Discover existing documentation" in discover_docs.__doc__


class TestToolInvocation:
    """Test tool invocation via orchestrator."""
    
    @pytest.mark.asyncio
    async def test_init_steering_invocation(self):
        """Test init_steering tool invocation with mocked workflow."""
        from mcp_server.tools.init_steering import init_steering
        
        with patch("hiveforge.steering.shared.adapters.SharedInitWorkflow") as mock_workflow_class:
            # Mock workflow execution
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow
            
            from hiveforge.steering.shared.base import WorkflowResult
            mock_result = WorkflowResult(
                success=True,
                message="Successfully initialized steering files (5 files created)",
                files_created=[".kiro/steering/tech-stack.md"],
                metadata={"files_count": 5}
            )
            mock_workflow.execute.return_value = mock_result
            
            # Invoke tool
            ctx = Mock()
            result = await init_steering(
                ctx,
                project_root=".",
                auto_discover=True,
                autonomous=True
            )
            
            # Verify result structure
            assert result["status"] == "success"
            assert "message" in result
            assert "files_created" in result
            assert result["files_count"] == 5
    
    @pytest.mark.asyncio
    async def test_update_steering_invocation(self):
        """Test update_steering tool invocation with mocked workflow."""
        from mcp_server.tools.update_steering import update_steering
        
        with patch("hiveforge.steering.shared.adapters.SharedUpdateWorkflow") as mock_workflow_class:
            # Mock workflow execution
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow
            
            from hiveforge.steering.shared.base import WorkflowResult
            mock_result = WorkflowResult(
                success=True,
                message="Successfully updated steering files",
                files_modified=[".kiro/steering/tech-stack.md"],
                metadata={"files_count": 1}
            )
            mock_workflow.execute.return_value = mock_result
            
            # Invoke tool
            ctx = Mock()
            result = await update_steering(
                ctx,
                project_root=".",
                incremental=True
            )
            
            # Verify result structure
            assert result["status"] == "success"
            assert "files_modified" in result
    
    @pytest.mark.asyncio
    async def test_validate_steering_invocation(self):
        """Test validate_steering tool invocation with mocked workflow."""
        from mcp_server.tools.validate_steering import validate_steering
        
        with patch("hiveforge.steering.shared.adapters.SharedValidateWorkflow") as mock_workflow_class:
            # Mock workflow execution
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow
            
            from hiveforge.steering.shared.base import WorkflowResult
            mock_result = WorkflowResult(
                success=True,
                message="All validation checks passed",
                metadata={
                    "files_checked": 5,
                    "critical_issues": 0,
                    "warnings": 0
                }
            )
            mock_workflow.execute.return_value = mock_result
            
            # Invoke tool
            ctx = Mock()
            result = await validate_steering(ctx, project_root=".")
            
            # Verify result structure
            assert result["status"] == "success"
            assert result["files_checked"] == 5
            assert result["critical_issues"] == 0
    
    @pytest.mark.asyncio
    async def test_reset_steering_invocation(self):
        """Test reset_steering tool invocation with mocked workflow."""
        from mcp_server.tools.reset_steering import reset_steering
        
        with patch("hiveforge.steering.shared.adapters.SharedResetWorkflow") as mock_workflow_class:
            # Mock workflow execution
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow
            
            from hiveforge.steering.shared.base import WorkflowResult
            mock_result = WorkflowResult(
                success=True,
                message="Successfully reset 5 file(s) to default templates",
                files_modified=[".kiro/steering/tech-stack.md"],
                metadata={"backup_location": ".kiro/backups/reset_20260217"}
            )
            mock_workflow.execute.return_value = mock_result
            
            # Invoke tool
            ctx = Mock()
            result = await reset_steering(ctx, project_root=".")
            
            # Verify result structure
            assert result["status"] == "success"
            assert "backup_location" in result
    
    @pytest.mark.asyncio
    async def test_discover_docs_invocation(self):
        """Test discover_docs tool invocation with mocked workflow."""
        from mcp_server.tools.discover_docs import discover_docs
        
        with patch("hiveforge.steering.shared.adapters.SharedDiscoveryWorkflow") as mock_workflow_class:
            # Mock workflow execution
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow
            
            from hiveforge.steering.shared.base import WorkflowResult
            mock_result = WorkflowResult(
                success=True,
                message="Discovery complete: 42 files found",
                metadata={
                    "files_discovered": 42,
                    "files_included": 37
                }
            )
            mock_workflow.execute.return_value = mock_result
            
            # Invoke tool
            ctx = Mock()
            result = await discover_docs(ctx, project_root=".")
            
            # Verify result structure
            assert result["status"] == "success"
            assert result["files_discovered"] == 42


class TestErrorHandling:
    """Test error handling in tool invocations."""
    
    @pytest.mark.asyncio
    async def test_tool_handles_workflow_exception(self):
        """Test that tools handle workflow exceptions gracefully."""
        from mcp_server.tools.init_steering import init_steering
        
        with patch("hiveforge.steering.shared.adapters.SharedInitWorkflow") as mock_workflow_class:
            # Mock workflow to raise exception
            mock_workflow_class.side_effect = Exception("Test error")
            
            # Invoke tool
            ctx = Mock()
            result = await init_steering(ctx, project_root=".")
            
            # Verify error handling
            assert result["status"] == "failed"
            assert "Test error" in result["message"]
            assert len(result["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_tool_handles_invalid_parameters(self):
        """Test that tools handle invalid parameters gracefully."""
        from mcp_server.tools.init_steering import init_steering
        
        with patch("hiveforge.steering.shared.adapters.SharedInitWorkflow") as mock_workflow_class:
            # Mock workflow to raise ValueError
            mock_workflow_class.side_effect = ValueError("Invalid project root")
            
            # Invoke tool
            ctx = Mock()
            result = await init_steering(ctx, project_root="/nonexistent")
            
            # Verify error handling
            assert result["status"] == "failed"
            assert "errors" in result


class TestResultPresentation:
    """Test result presentation to user via orchestrator."""
    
    @pytest.mark.asyncio
    async def test_success_result_format(self):
        """Test that success results have consistent format."""
        from mcp_server.tools.init_steering import init_steering
        
        with patch("hiveforge.steering.shared.adapters.SharedInitWorkflow") as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow
            
            from hiveforge.steering.shared.base import WorkflowResult
            mock_result = WorkflowResult(
                success=True,
                message="Success message",
                files_created=["file1.md"],
                warnings=["warning1"],
                metadata={"key": "value"}
            )
            mock_workflow.execute.return_value = mock_result
            
            ctx = Mock()
            result = await init_steering(ctx, project_root=".")
            
            # Verify standard fields
            assert "status" in result
            assert "message" in result
            assert "files_created" in result
            assert "files_modified" in result
            assert "files_deleted" in result
            assert "warnings" in result
            assert "errors" in result
            
            # Verify metadata is included
            assert "key" in result
            assert result["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_failure_result_format(self):
        """Test that failure results have consistent format."""
        from mcp_server.tools.init_steering import init_steering
        
        with patch("hiveforge.steering.shared.adapters.SharedInitWorkflow") as mock_workflow_class:
            mock_workflow_class.side_effect = Exception("Test error")
            
            ctx = Mock()
            result = await init_steering(ctx, project_root=".")
            
            # Verify standard fields
            assert result["status"] == "failed"
            assert "message" in result
            assert "errors" in result
            assert len(result["errors"]) > 0
    
    def test_result_is_json_serializable(self):
        """Test that all results are JSON serializable."""
        from hiveforge.steering.shared.base import WorkflowResult
        
        result = WorkflowResult(
            success=True,
            message="Test message",
            files_created=["file1.md"],
            metadata={"count": 1}
        )
        
        # Convert to dict and serialize
        result_dict = result.to_dict()
        json_str = json.dumps(result_dict)
        
        # Verify it can be deserialized
        parsed = json.loads(json_str)
        assert parsed["status"] == "success"
        assert parsed["message"] == "Test message"


class TestMCPServerIntegration:
    """Test FastMCP server integration."""
    
    def test_server_imports_all_tools(self):
        """Test that server imports all tools."""
        # Import server module
        import mcp_server.server as server_module
        
        # Verify FastMCP instance exists
        assert hasattr(server_module, "mcp")
        assert server_module.mcp is not None
    
    def test_server_has_main_entry_point(self):
        """Test that server has main() entry point."""
        from mcp_server.server import main
        
        assert main is not None
        assert callable(main)
    
    def test_server_configuration(self):
        """Test that server is configured correctly."""
        import mcp_server.server as server_module
        
        # Verify server name
        assert server_module.mcp.name == "HiveForge Steering Assistant"


class TestSharedBackendUtilization:
    """Test that tools use shared backend exclusively."""
    
    @pytest.mark.asyncio
    async def test_init_uses_shared_workflow(self):
        """Test that init_steering uses SharedInitWorkflow."""
        from mcp_server.tools.init_steering import init_steering
        
        with patch("hiveforge.steering.shared.adapters.SharedInitWorkflow") as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow
            
            from hiveforge.steering.shared.base import WorkflowResult
            mock_workflow.execute.return_value = WorkflowResult(
                success=True,
                message="Test"
            )
            
            ctx = Mock()
            await init_steering(ctx, project_root=".")
            
            # Verify SharedInitWorkflow was used
            mock_workflow_class.assert_called_once()
            mock_workflow.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tools_do_not_duplicate_logic(self):
        """Test that tools contain no workflow logic."""
        from mcp_server.tools import init_steering, update_steering
        
        import inspect
        
        # Get source code
        init_source = inspect.getsource(init_steering)
        update_source = inspect.getsource(update_steering)
        
        # Tools should only call shared workflows
        assert "SharedInitWorkflow" in init_source
        assert "SharedUpdateWorkflow" in update_source
        
        # Tools should not contain workflow logic
        assert "from ..workflows.init_workflow import InitWorkflow" not in init_source  # v02 direct import
        assert "from ..workflows.update_workflow import UpdateWorkflow" not in update_source  # v02 direct import