from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
import sys
import os
import PyPDF2
from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, HttpUrl
from enum import Enum

from sysprompt import build_prompt
from tools import PDFDocument, clip_memory, goto, next_search_match, scroll_down, scroll_up, use_memory
from dotenv import load_dotenv
load_dotenv()

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
    model_name,
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
        next_search_match,
        goto,
        scroll_up,
        scroll_down,
        clip_memory,
        use_memory
    ]
    local_agent = create_react_agent(
        model=model_name,
        tools=tools,
        prompt=build_prompt(structured_output_schema)
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

# --- Tool Registration for Agent ---
global_tools = [
    next_search_match,
    goto,
    scroll_up,
    scroll_down,
    clip_memory,
    use_memory,
    doc_task
]
llm = ChatGoogleGenerativeAI(
    model= "gemini-2.5-pro",
    temperature=1.0,
    max_retries=2,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    tool_call = True
)
# agent = create_react_agent(
#     model=llm,
#     tools=global_tools,
#     prompt=(
#         "You are a PDF parser agent. Your job is to scan through the PDF and provide output strictly based on the user's instructions. "
#         "The pdf is already present and ready to use by tools, you do not need to ask user for the pdf. Use the available tools to navigate and extract content from the PDF. Use memory to store important information for later use. "
#         "Do not provide the user with anything except the PDF content in the required markdown format. do not Generate anything new"
#     )
# )
# print(agent.invoke({"messages": [{"role": "user", "content": "Give me a 50 word Summary of the contents of each pages from page 5 to 10. Use tools"}]}))

print(doc_task(
    pdf_url="https://www.ipcc.ch/report/ar6/syr/downloads/report/IPCC_AR6_SYR_SPM.pdf",
    model_name=llm,
    model_cfg={},
    task="Give me a 50 word Summary of the contents of each pages from page 5 to 10. Use tools",
    process_budget_pagewise={},
    structured_output_schema={}
))

