"""
FastMCP server for HiveForge Steering Power.

This server provides MCP tools for steering file management in KIRO.
All tools use the shared backend to ensure identical behavior with the CLI.
"""

import logging
import sys
from pathlib import Path

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("HiveForge Steering Assistant")

# Import and register tools
from .tools.init_steering import init_steering
from .tools.update_steering import update_steering
from .tools.validate_steering import validate_steering
from .tools.reset_steering import reset_steering
from .tools.discover_docs import discover_docs

# Register tools with FastMCP
mcp.tool()(init_steering)
mcp.tool()(update_steering)
mcp.tool()(validate_steering)
mcp.tool()(reset_steering)
mcp.tool()(discover_docs)


def main() -> None:
    """
    Main entry point for the MCP server.
    
    This function starts the FastMCP server and makes all tools available
    to the KIRO orchestrator.
    """
    try:
        logger.info("Starting HiveForge Steering MCP Server v2.0.0")
        logger.info("Server initialized with shared backend architecture")
        
        # Run the MCP server
        mcp.run()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
