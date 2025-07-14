"""
Core classes for PDF parsing and agent functionality.
"""

import os
import PyPDF2
from typing import List, Optional, Tuple, Dict, Any
from langgraph.prebuilt import create_react_agent


class PDFDocument:
    """A class to manage PDF document parsing and navigation."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.pages = []
        self.lines = []  # List of (page_num, line_num_on_page, global_line_num, text)
        self.page_line_ranges = []  # List of (start_global_line, end_global_line) for each page
        self._load_pdf()

    def _load_pdf(self):
        """Load and parse the PDF file."""
        with open(self.file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            global_line = 1
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""
                lines = text.splitlines()
                start_line = global_line
                for line_num_on_page, line in enumerate(lines, 1):
                    self.lines.append((page_num, line_num_on_page, global_line, line))
                    global_line += 1
                end_line = global_line - 1
                self.page_line_ranges.append((start_line, end_line))

    def get_page_lines(self, page_num: int) -> List[Tuple[int, int, int, str]]:
        """Get all lines from a specific page."""
        return [l for l in self.lines if l[0] == page_num]

    def get_line_by_global(self, global_line_num: int) -> Optional[Tuple[int, int, int, str]]:
        """Get a line by its global line number."""
        for l in self.lines:
            if l[2] == global_line_num:
                return l
        return None

    def get_total_pages(self):
        """Get the total number of pages in the PDF."""
        return len(self.page_line_ranges)

    def get_total_lines(self):
        """Get the total number of lines in the PDF."""
        return len(self.lines)


class PDFParserAgent:
    """A class to manage the PDF parsing agent with tools."""
    
    def __init__(self, pdf_path: str, model_name: str = "ollama:llama3.2"):
        """
        Initialize the PDF parser agent.
        
        Args:
            pdf_path: Path to the PDF file
            model_name: Name of the model to use for the agent
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        self.pdf_doc = PDFDocument(pdf_path)
        self.model_name = model_name
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """Create the agent with all the necessary tools."""
        from .tools import (
            next_search_match,
            goto,
            scroll_up,
            scroll_down,
            clip_memory,
            use_memory,
            make_tool_with_doc
        )
        
        global_tools = [
            make_tool_with_doc(next_search_match, self.pdf_doc),
            make_tool_with_doc(goto, self.pdf_doc),
            make_tool_with_doc(scroll_up, self.pdf_doc),
            make_tool_with_doc(scroll_down, self.pdf_doc),
            make_tool_with_doc(clip_memory, self.pdf_doc),
            make_tool_with_doc(use_memory, self.pdf_doc),
        ]
        
        return create_react_agent(
            model=self.model_name,
            tools=global_tools,
            prompt=(
                "You are a PDF parser agent. Your job is to scan through the PDF and provide output strictly based on the user's instructions. "
                "Use the available tools to navigate and extract content from the PDF. Use memory to store important information for later use. "
                "Do not provide the user with anything except the PDF content in the required markdown format."
            )
        )
    
    def query(self, query: str) -> Dict[str, Any]:
        """
        Query the PDF using the agent.
        
        Args:
            query: The query to process
            
        Returns:
            The agent's response
        """
        return self.agent.invoke({"messages": [{"role": "user", "content": query}]})
    
    def get_page(self, page_num: int) -> str:
        """
        Get a specific page from the PDF.
        
        Args:
            page_num: The page number to retrieve
            
        Returns:
            The page content in markdown format
        """
        from .tools import render_page_markdown
        return render_page_markdown(self.pdf_doc, page_num) 