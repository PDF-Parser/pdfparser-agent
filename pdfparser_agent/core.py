"""
Core classes for PDF parsing and agent functionality.
"""

import os
import PyPDF2
from typing import List, Optional, Tuple, Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from pdfparser_agent.processing.pdf_processing import load_pdf_with_budget, ProcessBudget
from pdfparser_agent.db import insert_document_metadata, insert_document_lines


class PDFDocument:
    """A class to manage PDF document parsing and navigation."""
    def __init__(self, file_path: str, budget: ProcessBudget = ProcessBudget.LOW, user_id: str = None):
        self.file_path = file_path
        self.user_id = user_id
        self.document_id = None
        self.processing_type = str(budget)
        self.processing_result = None
        self._load_pdf(budget)

    def _load_pdf(self, budget: ProcessBudget = ProcessBudget.LOW):
        """Load and parse the PDF file using the selected processing method based on budget, and store in MongoDB."""
        # Store metadata and get document_id
        self.document_id = insert_document_metadata(
            document_path=self.file_path,
            processing_type=str(budget),
            user_id=self.user_id or "anonymous"
        )
        # Process PDF
        processing_result = load_pdf_with_budget(self.file_path, budget)
        self.processing_result = processing_result
        # Store processed lines in MongoDB if structured (list of dicts)
        if isinstance(processing_result, list) and processing_result and isinstance(processing_result[0], dict):
            insert_document_lines(self.document_id, [
                {
                    "page_number": l.get("page_num"),
                    "line_num_on_page": l.get("line_num_on_page"),
                    "global_line_number": l.get("global_line_num"),
                    "text": l.get("text")
                } for l in processing_result
            ])




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
        llm = ChatGoogleGenerativeAI(
            model= "gemini-2.5-pro",
            temperature=1.0,
            max_retries=2,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            tool_call = True
            )
        return create_react_agent(
            model=llm,
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
        return render_page_markdown(self.pdf_doc, self.pdf_doc.user_id, page_num)

if __name__ == "__main__":
    # Example usage
    pdf_path = "IPCC_AR6_SYR_SPM.pdf"  # Change as needed
    agent = PDFParserAgent(pdf_path)
    response = agent.query("Give me a 50 word summary of the contents of each page from page 5 to 10. Use tools")
    print(response)