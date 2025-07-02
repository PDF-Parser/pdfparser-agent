from langgraph.prebuilt import create_react_agent
import sys
import os
import PyPDF2
from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, HttpUrl
from enum import Enum
from functools import partial

# --- PDF State Management ---
class PDFDocument:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.pages = []
        self.lines = []  # List of (page_num, line_num_on_page, global_line_num, text)
        self.page_line_ranges = []  # List of (start_global_line, end_global_line) for each page
        self._load_pdf()

    def _load_pdf(self):
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
        return [l for l in self.lines if l[0] == page_num]

    def get_line_by_global(self, global_line_num: int) -> Optional[Tuple[int, int, int, str]]:
        for l in self.lines:
            if l[2] == global_line_num:
                return l
        return None

    def get_total_pages(self):
        return len(self.page_line_ranges)

    def get_total_lines(self):
        return len(self.lines)

# --- Markdown Output Helper ---
def render_page_markdown(pdf: PDFDocument, page_num: int, highlight_lines: Optional[List[int]] = None, highlight_match: Optional[int] = None) -> str:
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
def next_search_match(doc: PDFDocument, search_term: str, match_number: Optional[int] = None) -> str:
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
def goto(doc: PDFDocument, page: int = None, line: int = None) -> str:
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
def scroll_up(doc: PDFDocument, n: int) -> str:
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
def scroll_down(doc: PDFDocument, n: int) -> str:
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
def clip_memory(doc: PDFDocument, line_num_start: int, line_num_end: int) -> str:
    """
    Clip lines from line_num_start to line_num_end and store in memory.
    """
    clip = [l for l in doc.lines if line_num_start <= l[2] <= line_num_end]
    clip_memory_db.append(clip)
    return f"Clipped lines {line_num_start} to {line_num_end}."

# --- Tool: use_memory ---
def use_memory(doc: PDFDocument, prompt: str) -> str:
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
    import tempfile
    import requests
    # Download the PDF
    response = requests.get(str(pdf_url))
    if response.status_code != 200:
        return {"error": f"Failed to download PDF from {pdf_url}"}
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(response.content)
        tmp_pdf_path = tmp_file.name
    # Initialize the document
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
    return result

# --- PDF Load (for now, load at startup) ---
pdf_path = "IPCC_AR6_SYR_SPM.pdf"  # Change as needed
if not os.path.exists(pdf_path):
    raise FileNotFoundError(f"PDF not found: {pdf_path}")
pdf_doc = PDFDocument(pdf_path)

# --- Tool Wrappers for Agent Registration ---
def make_tool_with_doc(tool_func, doc):
    def wrapper(*args, **kwargs):
        return tool_func(doc, *args, **kwargs)
    wrapper.__name__ = tool_func.__name__
    wrapper.__doc__ = tool_func.__doc__
    return wrapper

global_tools = [
    make_tool_with_doc(next_search_match, pdf_doc),
    make_tool_with_doc(goto, pdf_doc),
    make_tool_with_doc(scroll_up, pdf_doc),
    make_tool_with_doc(scroll_down, pdf_doc),
    make_tool_with_doc(clip_memory, pdf_doc),
    make_tool_with_doc(use_memory, pdf_doc),
    doc_task
]

agent = create_react_agent(
    model="ollama:llama3.2",
    tools=global_tools,
    prompt=(
        "You are a PDF parser agent. Your job is to scan through the PDF and provide output strictly based on the user's instructions. "
        "Use the available tools to navigate and extract content from the PDF. Use memory to store important information for later use. "
        "Do not provide the user with anything except the PDF content in the required markdown format."
    )
)
print(agent.invoke({"messages": [{"role": "user", "content": "Give me the markdown of page 5."}]}))
# Example agent call
# if __name__ == "__main__":
#     result = doc_task(
#         pdf_url="https://www.ipcc.ch/report/ar6/syr/downloads/report/IPCC_AR6_SYR_SPM.pdf",
#         model_name="ollama:llama3.2",
#         model_cfg={"api_base": "..."},
#         task="From the given pdf, give me an overview of Global Warming",
#         process_budget_pagewise=ProcessBudget.HIGH,
#         structured_output_schema={"summary": "list[str]"}
#     )
#     print("\n--- Tool Calls and Results ---\n")
#     messages = result['messages'] if 'messages' in result else []
#     tool_call_map = {}
#     # First, collect all tool calls
#     print(result)
#     for msg in messages:
#         if hasattr(msg, 'tool_calls') and msg.tool_calls:
#             for call in msg.tool_calls:
#                 tool_call_map[call['id']] = call
#     # Now, print tool calls and their responses
#     for msg in messages:
#         if getattr(msg, 'type', None) == 'tool_call' or msg.__class__.__name__ == 'ToolMessage':
#             call_id = getattr(msg, 'tool_call_id', None) or getattr(msg, 'id', None)
#             if call_id and call_id in tool_call_map:
#                 call = tool_call_map[call_id]
#                 print(f"Tool Call: {call['name']}({call['args']})")
#                 print(f"Response: {getattr(msg, 'content', '')}")
#                 print()
#     # Print the final AI message
#     print("--- Final Output ---\n")
#     for msg in messages:
#         if msg.__class__.__name__ == 'AIMessage' and getattr(msg, 'content', None):
#             print(msg.content)
#             break


