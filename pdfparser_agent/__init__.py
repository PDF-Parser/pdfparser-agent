"""
PDF Parser Agent - A next-generation PDF reader fully orchestrated by AI Agents.

This package provides tools for parsing and interacting with PDF documents using AI agents.
"""

__version__ = "0.1.0"
__author__ = "Priyesh Srivastava"
__email__ = "priyesh@example.com"

from .core import PDFDocument, PDFParserAgent
from .tools import (
    next_search_match,
    goto,
    scroll_up,
    scroll_down,
    clip_memory,
    use_memory,
    doc_task,
    ProcessBudget,
    DocTaskConfig,
)

__all__ = [
    "PDFDocument",
    "PDFParserAgent",
    "next_search_match",
    "goto",
    "scroll_up",
    "scroll_down",
    "clip_memory",
    "use_memory",
    "doc_task",
    "ProcessBudget",
    "DocTaskConfig",
] 