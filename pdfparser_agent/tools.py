"""
Tools for PDF parsing and navigation.
"""

import tempfile
import requests
from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, HttpUrl
from enum import Enum
from langgraph.prebuilt import create_react_agent
from .db import get_lines


# In-memory memory, keyed by (user_id, document_id)
clip_memory_db = {}


# --- Markdown Output Helper ---
def render_page_markdown(document_id: str, user_id: str, page_num: int, highlight_lines: Optional[List[int]] = None, highlight_match: Optional[int] = None) -> str:
    lines = get_lines(document_id, {"page_number": page_num})
    total_pages = max([l["page_number"] for l in get_lines(document_id)]) if lines else 0
    out = [f"{'-'*42}\n|               Page {page_num} of {total_pages}             |\n{'-'*42}"]
    out.append("|                                        |\n|                                        |\n|                                        |")
    for l in lines:
        g = l["global_line_number"]
        text = l["text"]
        if highlight_lines and g in highlight_lines:
            line = f"|{g:03}| <highlight match=\"{highlight_match}\"></highlight> {text}"
        else:
            line = f"|{g:03}| {text}"
        out.append(line)
    out.append("|                                        |\n------------------------------------------")
    return '\n'.join(out)


# --- Tool: next_search_match ---
def next_search_match(document_id: str, user_id: str, search_term: str, match_number: Optional[int] = None) -> str:
    """
    Find the next match for a search term in the loaded PDF and render the page with the match highlighted.
    """
    all_lines = get_lines(document_id)
    matches = [l for l in all_lines if search_term.lower() in l["text"].lower()]
    if not matches:
        return "No matches found."
    idx = match_number-1 if match_number else 0
    if idx >= len(matches):
        return f"Only {len(matches)} matches found."
    match = matches[idx]
    page_num = match["page_number"]
    global_line = match["global_line_number"]
    return render_page_markdown(document_id, user_id, page_num, highlight_lines=[global_line], highlight_match=idx+1)


# --- Tool: goto ---
def goto(document_id: str, user_id: str, page: int = None, line: int = None) -> str:
    """
    Go to a specific page or line number in the PDF and render it in markdown. Takes either page or line as input.
    """
    if page is not None:
        return render_page_markdown(document_id, user_id, page)
    if line is not None:
        all_lines = get_lines(document_id, {"global_line_number": line})
        if all_lines:
            l = all_lines[0]
            return render_page_markdown(document_id, user_id, l["page_number"], highlight_lines=[line])
    return "Invalid target."


# --- Tool: scroll_up ---
def scroll_up(document_id: str, user_id: str, n: int) -> str:
    """
    Scroll up n lines from the end (simulate by showing the previous n lines).
    """
    all_lines = get_lines(document_id)
    lines = all_lines[-n:] if n <= len(all_lines) else all_lines
    out = [f"{'-'*42}\n|   Scrolled Up {n} lines                |\n{'-'*42}"]
    for l in lines:
        g = l["global_line_number"]
        text = l["text"]
        out.append(f"|{g:03}| {text}")
    out.append("------------------------------------------")
    return '\n'.join(out)


# --- Tool: scroll_down ---
def scroll_down(document_id: str, user_id: str, n: int) -> str:
    """
    Scroll down n lines from the start (simulate by showing the next n lines).
    """
    all_lines = get_lines(document_id)
    lines = all_lines[:n]
    out = [f"{'-'*42}\n|   Scrolled Down {n} lines              |\n{'-'*42}"]
    for l in lines:
        g = l["global_line_number"]
        text = l["text"]
        out.append(f"|{g:03}| {text}")
    out.append("------------------------------------------")
    return '\n'.join(out)


# --- Tool: clip_memory ---
def clip_memory(document_id: str, user_id: str, line_num_start: int, line_num_end: int) -> str:
    """
    Clip lines from line_num_start to line_num_end and store in memory (per user/document).
    """
    all_lines = get_lines(document_id)
    clip = [l for l in all_lines if line_num_start <= l["global_line_number"] <= line_num_end]
    key = (user_id, document_id)
    if key not in clip_memory_db:
        clip_memory_db[key] = []
    clip_memory_db[key].append(clip)
    return f"Clipped lines {line_num_start} to {line_num_end}."


# --- Tool: use_memory ---
def use_memory(document_id: str, user_id: str, prompt: str) -> str:
    """
    Use the clipped memory to answer a prompt (simulated).
    """
    key = (user_id, document_id)
    if key not in clip_memory_db or not clip_memory_db[key]:
        return "No memory clipped."
    lines = [line["text"] for clip in clip_memory_db[key] for line in clip]
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