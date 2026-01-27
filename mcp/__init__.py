"""
MCP (Model Context Protocol) integration module for Mider
"""

from .client import MCPClient
from .tools import MCPToolManager

__all__ = ['MCPClient', 'MCPToolManager']