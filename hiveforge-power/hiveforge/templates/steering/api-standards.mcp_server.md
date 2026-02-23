---
inclusion: fileMatch
patterns: ["**/mcp_server/**", "**/*_mcp.py", "**/tools/**"]
priority: 2
description: "MCP tool standards and conventions. Only loaded when working on MCP server code."
---

# MCP Tool Standards & Conventions

## Tool Naming
- Use descriptive verb-noun format: `get_user`, `create_task`, `list_files`
- Avoid abbreviations unless widely understood
- Use snake_case for tool names

## Tool Decorators
```python
@mcp.tool()
async def tool_name(arg1: str, arg2: int) -> dict:
    """
    Brief description of what the tool does.
    
    Args:
        arg1: Description of first argument
        arg2: Description of second argument
        
    Returns:
        Description of return value
    """
    pass
```

## Parameter Standards
- Always use type hints for all parameters
- Exclude `ctx` parameter from tool signatures (handled by framework)
- Use descriptive parameter names
- Provide clear docstrings for each parameter

## Return Format
- Return structured data (dict, list, dataclass)
- Include error information in response when applicable
- Use consistent field naming across tools

## Error Handling
- Catch and handle exceptions gracefully
- Return error information in structured format
- Log errors for debugging
- Never expose internal implementation details in errors

## Tool Documentation
- Every tool must have a docstring
- First line: brief summary (max 120 chars)
- Include Args and Returns sections
- Document any side effects or state changes

## Testing
- Write unit tests for each tool
- Test with valid and invalid inputs
- Mock external dependencies
- Test error handling paths

## Context Usage
- Use `ctx` for accessing MCP context
- Never modify ctx state directly
- Use ctx for logging and sampling
