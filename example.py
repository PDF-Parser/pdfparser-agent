#!/usr/bin/env python3
"""
Example usage of the PDF Parser Agent.

This script demonstrates how to use the PDF Parser Agent to analyze PDF documents.
"""

from pdfparser_agent import PDFParserAgent, doc_task, ProcessBudget


def basic_usage():
    """Demonstrate basic usage of the PDF Parser Agent."""
    print("=== Basic PDF Parser Agent Usage ===")
    
    # Initialize the agent with a PDF file
    # Note: You'll need to provide a path to a PDF file
    pdf_path = "IPCC_AR6_SYR_SPM.pdf"  # Update this path to your PDF file
    
    try:
        agent = PDFParserAgent(pdf_path)
        
        # Query the PDF
        result = agent.query("What is this document about?")
        print("Query result:")
        print(result)
        
        # Get a specific page
        page_content = agent.get_page(1)
        print("\nPage 1 content:")
        print(page_content)
        
    except FileNotFoundError:
        print(f"PDF file '{pdf_path}' not found. Please update the path in the script.")
    except Exception as e:
        print(f"Error: {e}")


def remote_pdf_usage():
    """Demonstrate usage with a remote PDF URL."""
    print("\n=== Remote PDF Usage ===")
    
    # Example with a remote PDF
    pdf_url = "https://www.ipcc.ch/report/ar6/syr/downloads/report/IPCC_AR6_SYR_SPM.pdf"
    
    try:
        result = doc_task(
            pdf_url=pdf_url,
            model_name="ollama:llama3.2",
            model_cfg={},
            task="Give me a brief overview of the main findings in this document",
            process_budget_pagewise=ProcessBudget.MEDIUM
        )
        
        print("Remote PDF task result:")
        print(result)
        
    except Exception as e:
        print(f"Error processing remote PDF: {e}")


def interactive_mode():
    """Demonstrate interactive mode."""
    print("\n=== Interactive Mode ===")
    print("To use interactive mode, run:")
    print("pdfparser-agent your_document.pdf")
    print("Or:")
    print("python -m pdfparser_agent.cli your_document.pdf")


if __name__ == "__main__":
    print("PDF Parser Agent - Example Usage")
    print("=" * 50)
    
    basic_usage()
    remote_pdf_usage()
    interactive_mode()
    
    print("\n" + "=" * 50)
    print("For more information, see the README.md file.")
    print("To install the package: pip install -e .")
    print("To use the CLI: pdfparser-agent your_document.pdf") 