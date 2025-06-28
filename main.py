from langgraph.prebuilt import create_react_agent
import sys
import os
import PyPDF2



def search_pdf(file_path, search_term):
    """
    Search for a term in a PDF file and return a list of page numbers (1-based) where the term appears.
    Args:
        file_path (str): Name of the PDF file.
        search_term (str): The term to search for.
    Returns:
        list: List of page numbers where the term is found. Ex: [1,3] means it's present in page 1 and 3
    """
    page_numbers = []
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and search_term.lower() in text.lower():
                page_numbers.append(i + 1)  
    return page_numbers

# if __name__ == "__main__":
#     if len(sys.argv) != 3:
#         print("Usage: python main.py <pdf_path> <search_term>")
#         sys.exit(1)
#     pdf_path = sys.argv[1]
#     term = sys.argv[2]
#     if not os.path.exists(pdf_path):
#         print(f"File not found: {pdf_path}")
#         sys.exit(1)
#     result = search_pdf(pdf_path, term)
#     if result:
#         print(f"Term '{term}' found on page(s): {result}")
#     else:
#         print(f"Term '{term}' not found in the document.")
        
agent = create_react_agent(
    model="ollama:llama3.2", 
    tools=[search_pdf],
    prompt="You are a helpful assistant"
)

# Run the agent
print(agent.invoke(
    {"messages": [{"role": "user", "content": "list of pages in pdf IPCC_AR6_SYR_SPM.pdf containing the word author"}]}
))