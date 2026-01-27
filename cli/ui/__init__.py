"""
UI modules for Mider
Inspired by Aider's GUI architecture pattern
"""

from .components import MiderUIComponents
from .panels import UIPanels
from .formatters import ResponseFormatter
from .interactive import InteractiveUI

__all__ = ['MiderUIComponents', 'UIPanels', 'ResponseFormatter', 'InteractiveUI']