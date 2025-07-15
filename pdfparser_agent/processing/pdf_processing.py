from enum import Enum

class ProcessBudget(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    PROFESSIONAL = "professional"
    FREE = "free"

def process_pdf_adobeocr(pdf_path: str):
    """Stub: Process PDF using Adobe OCR (placeholder)."""
    return f"[AdobeOCR] Processed {pdf_path}"

def process_pdf_docint_4o_mini(pdf_path: str):
    """Stub: Process PDF using DocInt 4o Mini (placeholder)."""
    return f"[DocInt 4o Mini] Processed {pdf_path}"

def process_pdf_docint(pdf_path: str):
    """Stub: Process PDF using DocInt (placeholder)."""
    return f"[DocInt] Processed {pdf_path}"

def process_pdf_dolphin(pdf_path: str):
    """Stub: Process PDF using Dolphin (placeholder)."""
    return f"[Dolphin] Processed {pdf_path}"

def process_pdf_mistralocr(pdf_path: str):
    """Stub: Process PDF using MistralOCR (placeholder)."""
    return f"[MistralOCR] Processed {pdf_path}"

def process_pdf_comprehend(pdf_path: str):
    """Stub: Process PDF using Comprehend (placeholder)."""
    return f"[Comprehend] Processed {pdf_path}"

def process_pdf_pypdf_pdfplumber(pdf_path: str):
    """
    Process PDF using pdfplumber. Returns a list of dicts with page_num, line_num_on_page, global_line_num, and text for each line.
    """
    import pdfplumber
    result = []
    global_line = 1
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            lines = text.splitlines()
            for line_num_on_page, line in enumerate(lines, 1):
                result.append({
                    "page_num": page_num,
                    "line_num_on_page": line_num_on_page,
                    "global_line_num": global_line,
                    "text": line
                })
                global_line += 1
    return result

def load_pdf_with_budget(pdf_path: str, budget: ProcessBudget):
    """
    Load/process the PDF using the appropriate processor(s) based on the ProcessBudget.
    Returns a string indicating which processor was used (stub).
    """
    return process_pdf_pypdf_pdfplumber(pdf_path);
    if budget == ProcessBudget.HIGH:
        return process_pdf_adobeocr(pdf_path)
    elif budget == ProcessBudget.MEDIUM:
        return process_pdf_docint_4o_mini(pdf_path)
    elif budget == ProcessBudget.LOW:
        return process_pdf_pypdf_pdfplumber(pdf_path)
    elif budget == ProcessBudget.PROFESSIONAL:
        return process_pdf_dolphin(pdf_path)
    elif budget == ProcessBudget.FREE:
        return process_pdf_comprehend(pdf_path)
    else:
        return process_pdf_pypdf_pdfplumber(pdf_path)
