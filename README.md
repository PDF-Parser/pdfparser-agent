# AgenticReader
This project is meant to be the next generation of PDF readers fully orchestrated by AI Agents. It simplifies the documents by allowing you to switch between multiple documents using a cost budget and approach PDF tasks in the same way as a human would approach them as opposed to dumping this into a database with 10k other documents and running RAG.

Here is how our offering stacks up to alternatives on a common set of tasks:
![]()

Download the [benchmark data here]().

## QuickStart
- API Schema is a copy of OpenAI schema
- docker container for server up with qdrant, litellm proxy and agent
- add LLM credentials, fill the values for processors you want to be available in your agent

## Installation

### From PyPI (when published)
```bash
pip install pdfparser-agent
```

### From Source
```bash
git clone https://github.com/priyeshsrivastava/pdfparser-agent.git
cd pdfparser-agent
pip install -e .
```

## Quick Start

### Command Line Interface

```bash
# Basic usage with a query
pdfparser-agent document.pdf "What is this document about?"

# Interactive mode
pdfparser-agent document.pdf

# Get a specific page
pdfparser-agent document.pdf --page 5

# Use a different model
pdfparser-agent document.pdf --model "ollama:llama3.1" "Summarize the key points"
```

### Python API

```python
from pdfparser_agent import PDFParserAgent

# Initialize the agent
agent = PDFParserAgent("document.pdf")

# Query the document
result = agent.query("What are the main findings in this report?")
print(result)

# Get a specific page
page_content = agent.get_page(1)
print(page_content)
```

### Remote PDF Processing

```python
from pdfparser_agent import doc_task, ProcessBudget

# Process a PDF from URL
result = doc_task(
    pdf_url="https://example.com/document.pdf",
    model_name="ollama:llama3.2",
    model_cfg={},
    task="Extract the key conclusions from this document",
    process_budget_pagewise=ProcessBudget.MEDIUM
)
print(result)
```

## Usage Examples

### Interactive Commands

When using interactive mode, you can use these commands:

- `"Show me page 5"` - Display a specific page
- `"Search for 'climate change'"` - Search for terms in the document
- `"Go to line 150"` - Navigate to a specific line
- `"Scroll up 10 lines"` - Scroll through the document
- `"Clip lines 100 to 200"` - Store lines in memory
- `"Use memory to summarize"` - Use stored memory
- `"What is this document about?"` - Get document summary

### Natural Language Queries

You can ask natural language questions like:

- "What are the main conclusions of this report?"
- "Find all mentions of renewable energy"
- "Summarize the methodology section"
- "What are the key recommendations?"
- "Extract all the data tables"

## Requirements

- Python 3.8+
- Ollama (for local model inference)
- Internet connection (for remote PDFs)

## Dependencies

- `langgraph>=0.2.0` - AI agent framework
- `PyPDF2>=3.0.0` - PDF parsing
- `pydantic>=2.0.0` - Data validation
- `requests>=2.28.0` - HTTP requests
- `ollama>=0.1.0` - Local model inference

## Development

### Setup Development Environment

```bash
git clone https://github.com/priyeshsrivastava/pdfparser-agent.git
cd pdfparser-agent
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
```

## Contributing

We welcome contributions! Here are the main areas for improvement:

### Tools
- [ ] Multimodal search capabilities
- [ ] Enhanced search algorithms
- [ ] Better cost calculations

### Parser
- [ ] Agentic reading options
- [ ] Custom parsing algorithms
- [ ] More accurate cost calculations

### Model Router
- [ ] Task-to-LLM routing
- [ ] Full LiteLLM router configuration support

### Agent
- [ ] Multimodal input handling
- [ ] Multi-PDF task support

### Memory
- [ ] Enhanced memory search options
- [ ] Higher recall memory systems

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) for AI agent orchestration
- Uses [Ollama](https://ollama.ai/) for local model inference
- Inspired by the need for more intelligent document processing tools
