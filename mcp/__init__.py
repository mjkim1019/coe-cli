"""
MCP (Model Context Protocol) integration module for Swing CLI
"""

from .client import MCPClient
from .tools import MCPToolManager

__all__ = ['MCPClient', 'MCPToolManager']