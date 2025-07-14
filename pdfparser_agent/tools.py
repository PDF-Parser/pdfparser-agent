"""
Tools for PDF parsing and navigation.
"""

import tempfile
import requests
from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, HttpUrl
from enum import Enum
from langgraph.prebuilt import create_react_agent


# --- Markdown Output Helper ---
def render_page_markdown(pdf, page_num: int, highlight_lines: Optional[List[int]] = None, highlight_match: Optional[int] = None) -> str:
    """Render a page in markdown format with optional highlighting."""
    total_pages = pdf.get_total_pages()
    lines = pdf.get_page_lines(page_num)
    out = [f"{'-'*42}\n|               Page {page_num} of {total_pages}             |\n{'-'*42}"]
    out.append("|                                        |\n|                                        |\n|                                        |")
    for (p, l_on_p, g, text) in lines:
        if highlight_lines and g in highlight_lines:
            line = f"|{g:03}| <highlight match=\"{highlight_match}\"></highlight> {text}"
        else:
            line = f"|{g:03}| {text}"
        out.append(line)
    out.append("|                                        |\n------------------------------------------")
    return '\n'.join(out)


# --- Tool: next_search_match ---
def next_search_match(doc, search_term: str, match_number: Optional[int] = None) -> str:
    """
    Find the next match for a search term in the loaded PDF and render the page with the match highlighted.
    """
    matches = [i for i, l in enumerate(doc.lines) if search_term.lower() in l[3].lower()]
    if not matches:
        return "No matches found."
    idx = match_number-1 if match_number else 0
    if idx >= len(matches):
        return f"Only {len(matches)} matches found."
    match_idx = matches[idx]
    page_num = doc.lines[match_idx][0]
    global_line = doc.lines[match_idx][2]
    return render_page_markdown(doc, page_num, highlight_lines=[global_line], highlight_match=idx+1)


# --- Tool: goto ---
def goto(doc, page: int = None, line: int = None) -> str:
    """
    Go to a specific page or line number in the PDF and render it in markdown. Takes either page or line as input.
    """
    if page is not None and 1 <= page <= doc.get_total_pages():
        return render_page_markdown(doc, page)
    if line is not None and 1 <= line <= doc.get_total_lines():
        l = doc.get_line_by_global(line)
        if l:
            return render_page_markdown(doc, l[0], highlight_lines=[line])
    return "Invalid target."


# --- Tool: scroll_up ---
def scroll_up(doc, n: int) -> str:
    """
    Scroll up n lines from the current position (simulate by showing the previous n lines).
    """
    lines = doc.lines[max(0, len(doc.lines)-n):]
    out = [f"{'-'*42}\n|   Scrolled Up {n} lines                |\n{'-'*42}"]
    for (p, l_on_p, g, text) in lines:
        out.append(f"|{g:03}| {text}")
    out.append("------------------------------------------")
    return '\n'.join(out)


# --- Tool: scroll_down ---
def scroll_down(doc, n: int) -> str:
    """
    Scroll down n lines from the current position (simulate by showing the next n lines).
    """
    lines = doc.lines[:n]
    out = [f"{'-'*42}\n|   Scrolled Down {n} lines              |\n{'-'*42}"]
    for (p, l_on_p, g, text) in lines:
        out.append(f"|{g:03}| {text}")
    out.append("------------------------------------------")
    return '\n'.join(out)


# --- Tool: clip_memory ---
clip_memory_db = []
def clip_memory(doc, line_num_start: int, line_num_end: int) -> str:
    """
    Clip lines from line_num_start to line_num_end and store in memory.
    """
    clip = [l for l in doc.lines if line_num_start <= l[2] <= line_num_end]
    clip_memory_db.append(clip)
    return f"Clipped lines {line_num_start} to {line_num_end}."


# --- Tool: use_memory ---
def use_memory(doc, prompt: str) -> str:
    """
    Use the clipped memory to answer a prompt (simulated).
    """
    if not clip_memory_db:
        return "No memory clipped."
    lines = [line for clip in clip_memory_db for (_, _, _, line) in clip]
    return '\n'.join(lines)


# --- Tool: doc_task ---
class ProcessBudget(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    PROFESSIONAL = "professional"
    FREE = "free"


class DocTaskConfig(BaseModel):
    pdf_url: HttpUrl
    model_name: str
    model_cfg: Dict[Any, Any]  # Renamed from model_config
    task: str
    process_budget_pagewise: ProcessBudget
    structured_output_schema: Optional[Dict[Any, Any]] = None


def doc_task(
    pdf_url: HttpUrl,
    model_name: str,
    model_cfg: Dict[Any, Any],
    task: str,
    process_budget_pagewise: ProcessBudget,
    structured_output_schema: Optional[Dict[Any, Any]] = None
) -> dict:
    """
    Loads the PDF from the given URL, initializes the document, and equips the agent with tools to perform the task.
    Returns a structured output (pydantic dict) with the result.
    """
    # Download the PDF
    response = requests.get(str(pdf_url))
    if response.status_code != 200:
        return {"error": f"Failed to download PDF from {pdf_url}"}
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(response.content)
        tmp_pdf_path = tmp_file.name
    
    # Initialize the document
    from .core import PDFDocument
    doc = PDFDocument(tmp_pdf_path)
    
    # Bind the doc to each tool using named wrappers
    tools = [
        make_tool_with_doc(next_search_match, doc),
        make_tool_with_doc(goto, doc),
        make_tool_with_doc(scroll_up, doc),
        make_tool_with_doc(scroll_down, doc),
        make_tool_with_doc(clip_memory, doc),
        make_tool_with_doc(use_memory, doc)
    ]
    
    local_agent = create_react_agent(
        model=model_name,
        tools=tools,
        prompt=("You are a PDF parser agent. Your job is to scan through the PDF and provide output strictly based on the user's instructions. "
        "Use the available tools to navigate and extract content from the PDF. Use memory to store important information for later use. "
        "Do not provide the user with anything except the PDF content in the required markdown format.")
    )
    
    result = local_agent.invoke({
        "messages": [
            {"role": "user", "content": task}
        ]
    })
    
    # Clean up temporary file
    import os
    try:
        os.unlink(tmp_pdf_path)
    except:
        pass
    
    return result


# --- Tool Wrappers for Agent Registration ---
def make_tool_with_doc(tool_func, doc):
    """Create a wrapper function that binds the document to the tool."""
    def wrapper(*args, **kwargs):
        return tool_func(doc, *args, **kwargs)
    wrapper.__name__ = tool_func.__name__
    wrapper.__doc__ = tool_func.__doc__
    return wrapper 