import os
import PyPDF2
from typing import List, Optional, Tuple

pdf_doc = None  # Will be set by main.py
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
def next_search_match(search_term: str, match_number: Optional[int] = None) -> str:
    """
    Find the next match for a search term in the loaded PDF and render the page with the match highlighted.
    """
    matches = [i for i, l in enumerate(pdf_doc.lines) if search_term.lower() in l[3].lower()]
    if not matches:
        return "No matches found."
    idx = match_number-1 if match_number else 0
    if idx >= len(matches):
        return f"Only {len(matches)} matches found."
    match_idx = matches[idx]
    page_num = pdf_doc.lines[match_idx][0]
    global_line = pdf_doc.lines[match_idx][2]
    return render_page_markdown(pdf_doc, page_num, highlight_lines=[global_line], highlight_match=idx+1)

# --- Tool: goto ---
def goto(page: int = None, line: int = None) -> str:
    """
    Go to a specific page or line number in the PDF and render it in markdown. Takes either page or line as input.
    """
    if page is not None and 1 <= page <= pdf_doc.get_total_pages():
        return render_page_markdown(pdf_doc, page)
    if line is not None and 1 <= line <= pdf_doc.get_total_lines():
        l = pdf_doc.get_line_by_global(line)
        if l:
            return render_page_markdown(pdf_doc, l[0], highlight_lines=[line])
    return "Invalid target."

# --- Tool: scroll_up ---
def scroll_up(n: int) -> str:
    """
    Scroll up n lines from the current position (simulate by showing the previous n lines).
    """
    lines = pdf_doc.lines[max(0, len(pdf_doc.lines)-n):]
    out = [f"{'-'*42}\n|   Scrolled Up {n} lines                |\n{'-'*42}"]
    for (p, l_on_p, g, text) in lines:
        out.append(f"|{g:03}| {text}")
    out.append("------------------------------------------")
    return '\n'.join(out)

# --- Tool: scroll_down ---
def scroll_down(n: int) -> str:
    """
    Scroll down n lines from the current position (simulate by showing the next n lines).
    """
    lines = pdf_doc.lines[:n]
    out = [f"{'-'*42}\n|   Scrolled Down {n} lines              |\n{'-'*42}"]
    for (p, l_on_p, g, text) in lines:
        out.append(f"|{g:03}| {text}")
    out.append("------------------------------------------")
    return '\n'.join(out)

# --- Tool: clip_memory ---
clip_memory_db = []
def clip_memory(line_num_start: int, line_num_end: int) -> str:
    """
    Clip lines from line_num_start to line_num_end and store in memory.
    """
    clip = [l for l in pdf_doc.lines if line_num_start <= l[2] <= line_num_end]
    clip_memory_db.append(clip)
    return f"Clipped lines {line_num_start} to {line_num_end}."

# --- Tool: use_memory ---
def use_memory(prompt: str) -> str:
    """
    Use the clipped memory to answer a prompt (simulated).
    """
    if not clip_memory_db:
        return "No memory clipped."
    lines = [line for clip in clip_memory_db for (_, _, _, line) in clip]
    return '\n'.join(lines)
