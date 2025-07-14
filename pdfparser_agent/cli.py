"""
Command-line interface for the PDF Parser Agent.
"""

import argparse
import sys
import os
from pathlib import Path
from .core import PDFParserAgent


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PDF Parser Agent - A next-generation PDF reader fully orchestrated by AI Agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pdfparser-agent document.pdf "What is the main topic of this document?"
  pdfparser-agent document.pdf "Show me page 5"
  pdfparser-agent document.pdf "Search for 'climate change' in the document"
        """
    )
    
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF file to analyze"
    )
    
    parser.add_argument(
        "query",
        nargs="?",
        help="Query to run against the PDF (optional - will start interactive mode if not provided)"
    )
    
    parser.add_argument(
        "--model",
        default="ollama:llama3.2",
        help="Model to use for the agent (default: ollama:llama3.2)"
    )
    
    parser.add_argument(
        "--page",
        type=int,
        help="Get a specific page number"
    )
    
    args = parser.parse_args()
    
    # Check if PDF file exists
    if not os.path.exists(args.pdf_path):
        print(f"Error: PDF file '{args.pdf_path}' not found.")
        sys.exit(1)
    
    try:
        # Initialize the agent
        agent = PDFParserAgent(args.pdf_path, model_name=args.model)
        
        # If page is specified, get that page
        if args.page:
            print(agent.get_page(args.page))
            return
        
        # If query is provided, run it
        if args.query:
            result = agent.query(args.query)
            print(result)
            return
        
        # Interactive mode
        print("PDF Parser Agent - Interactive Mode")
        print("Type 'quit' or 'exit' to exit")
        print("Type 'help' for available commands")
        print("-" * 50)
        
        while True:
            try:
                query = input("Query: ").strip()
                
                if query.lower() in ['quit', 'exit']:
                    break
                elif query.lower() == 'help':
                    print_help()
                    continue
                elif not query:
                    continue
                
                result = agent.query(query)
                print("\nResult:")
                print(result)
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    except Exception as e:
        print(f"Error initializing agent: {e}")
        sys.exit(1)


def print_help():
    """Print help information for interactive mode."""
    help_text = """
Available commands:
- "Show me page X" - Display a specific page
- "Search for 'term'" - Search for a term in the document
- "Go to line X" - Go to a specific line
- "Scroll up/down X lines" - Scroll through the document
- "Clip lines X to Y" - Store lines in memory
- "Use memory with prompt" - Use stored memory
- "What is this document about?" - Get document summary
- "quit" or "exit" - Exit the program
- "help" - Show this help message

You can also ask natural language questions about the document content.
"""
    print(help_text)


if __name__ == "__main__":
    main() 