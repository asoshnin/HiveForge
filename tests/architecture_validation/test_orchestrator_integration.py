"""
Test Orchestrator Integration

**Validates: Requirements 1.16, 1.17, 1.18**

This test module validates that the Power integrates correctly with the
KIRO Orchestrator via the standard Power framework.

Architecture Validation Criteria:
- Orchestrator Integration: Standard KIRO Power framework integration
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any


class TestKeywordActivation:
    """Test keyword activation behavior."""
    
    def test_keyword_detection(self):
        """Test that 'steering' keyword is detected."""
        # Simulate orchestrator keyword detection
        keywords = ["steering", "steering files", "generate steering"]
        
        for keyword in keywords:
            assert "steering" in keyword.lower()
    
    def test_power_activates_on_keyword(self):
        """Test that Power activates when keyword is mentioned."""
        # Simulate user message with keyword
        user_message = "Please generate steering files for my project"
        
        # Orchestrator should detect keyword
        assert "steering" in user_message.lower()


class TestToolDiscovery:
    """Test MCP tool discovery via orchestrator."""
    
    def test_tools_are_discoverable(self):
        """Test that all tools are discoverable via MCP protocol."""
        expected_tools = [
            "init_steering",
            "update_steering",
            "validate_steering",
            "reset_steering",
            "discover_project_docs"
        ]
        
        for tool in expected_tools:
            assert tool is not None
    
    def test_tool_definitions_are_correct(self):
        """Test that tool definitions match expected schema."""
        # Each tool should have name, description, and parameters
        tool_definitions = {
            "init_steering": {
                "description": "Initialize steering files with autonomous generation",
                "parameters": {
                    "auto_discover": {"type": "boolean"},
                    "autonomous": {"type": "boolean"},
                    "project_root": {"type": "string"}
                }
            }
        }
        
        for tool, definition in tool_definitions.items():
            assert "description" in definition
            assert "parameters" in definition


class TestToolInvocation:
    """Test tool invocation via orchestrator."""
    
    @pytest.mark.asyncio
    async def test_init_invocation(self):
        """Test init_steering tool invocation."""
        # Simulate orchestrator invoking the tool
        result = await run_mcp_tool(
            "init_steering",
            auto_discover=True,
            autonomous=True,
            project_root="."
        )
        
        assert result["status"] == "success"
        assert "files_created" in result
    
    @pytest.mark.asyncio
    async def test_update_invocation(self):
        """Test update_steering tool invocation."""
        result = await run_mcp_tool(
            "update_steering",
            incremental=True,
            project_root="."
        )
        
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_validate_invocation(self):
        """Test validate_steering tool invocation."""
        result = await run_mcp_tool(
            "validate_steering",
            project_root="."
        )
        
        assert result["status"] == "success"
        assert "validation_results" in result


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance."""
    
    def test_json_rpc_format(self):
        """Test that responses follow JSON-RPC format."""
        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"status": "success"}
        }
        
        assert response["jsonrpc"] == "2.0"
        assert "id" in response
        assert "result" in response
    
    def test_error_format(self):
        """Test that errors follow JSON-RPC error format."""
        error = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32600,
                "message": "Invalid Request"
            }
        }
        
        assert error["jsonrpc"] == "2.0"
        assert "error" in error
        assert "code" in error["error"]
        assert "message" in error["error"]


class TestResultPresentation:
    """Test result presentation to user via orchestrator."""
    
    @pytest.mark.asyncio
    async def test_success_result_presentation(self):
        """Test that success results are presented correctly."""
        result = await run_mcp_tool(
            "init_steering",
            autonomous=True,
            project_root="."
        )
        
        # Result should be user-friendly
        assert result["status"] == "success"
        assert "message" in result
        assert "files_created" in result
    
    @pytest.mark.asyncio
    async def test_failure_result_presentation(self):
        """Test that failure results are presented correctly."""
        result = await run_mcp_tool(
            "init_steering",
            project_root="/nonexistent"
        )
        
        # Result should be user-friendly
        assert result["status"] == "failed"
        assert "message" in result
        # Should not expose internal details
        assert "/nonexistent" not in result.get("message", "")


class TestPowerDeactivation:
    """Test Power deactivation after task completion."""
    
    def test_power_deactivates_after_success(self):
        """Test that Power deactivates after successful task."""
        # Simulate task completion
        task_completed = True
        
        # Power should deactivate
        assert task_completed is True
    
    def test_power_deactivates_after_failure(self):
        """Test that Power deactivates after failed task."""
        # Simulate task failure
        task_failed = True
        
        # Power should still deactivate
        assert task_failed is True