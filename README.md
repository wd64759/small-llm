# LangChain Project

A comprehensive LangChain-based application with RAG (Retrieval-Augmented Generation), Agents, and Vector Search capabilities.

## Features

- **RAG Chain**: Document retrieval and question answering
- **ReAct Agent**: Reasoning and acting agent with tool usage
- **Function Agent**: OpenAI Functions-based agent
- **Vector Database Support**: FAISS, Chroma, and Qdrant
- **Document Processing**: PDF, Markdown, CSV, and text files
- **FastAPI API**: RESTful API with automatic documentation
- **Comprehensive Logging**: Structured logging throughout the application

## Project Structure

```
langchain_project/
├── .env                    # Environment variables (API Key 等)
├── .gitignore              # Git ignore file
├── pyproject.toml          # Poetry/依赖管理
├── README.md               # Project documentation
├── main.py                 # FastAPI application entry point
│
├── config/                 # Configuration loading module
│   └── env.py              # Load .env, encapsulate os.getenv
│
├── chains/                 # Custom Chain, such as RetrievalQA Chain
│   └── rag_chain.py        # Vector retrieval, LLM, QA chain
│
├── agents/                 # Agent construction and execution
│   ├── react_agent.py      # ReAct agent
│   ├── function_agent.py   # OpenAI Functions agent
│   └── tools.py            # Custom tool functions
│
├── retriever/              # Vector database construction and Retriever definition
│   ├── embedder.py         # Vector generation (text2vec/openai/cohere)
│   ├── vectordb.py         # FAISS / Chroma / Qdrant initialization
│   └── loader.py           # Document loading and splitting
│
├── prompts/                # Custom prompt templates
│   ├── qa_prompt.txt
│   └── agent_prompt.txt
│
├── data/                   # Business data original files
│   ├── docs/               # Document original data
│   └── knowledge_base/     # Vector database storage
│
├── api/                    # FastAPI routes
│   └── router.py           # Unified API call entry
│
└── utils/                  # Utility modules
    ├── logger.py           # Logging encapsulation
    └── helper.py           # Miscellaneous utilities
```

## Quick Start

### Prerequisites

- Python 3.9+
- Poetry (for dependency management)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd langchain_project
```

2. Install dependencies:
```bash
poetry install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

4. Create a `.env` file with the following variables:
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
VECTOR_DB_PATH=./data/knowledge_base
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
```

### Running the Application

1. Start the FastAPI server:
```bash
poetry run python main.py
```

2. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Query Endpoint
```bash
POST /api/v1/query
{
  "question": "What is LangChain?",
  "agent_type": "rag",
  "k": 4
}
```

### Health Check
```bash
GET /api/v1/health
```

### Available Tools
```bash
GET /api/v1/tools
```

### Document Upload
```bash
POST /api/v1/upload
{
  "file_path": "/path/to/document.pdf",
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

## Usage Examples

### Using RAG Chain

```python
from chains.rag_chain import RAGChain
from retriever.vectordb import VectorDBManager
from retriever.embedder import EmbedderManager

# Initialize components
embedder = EmbedderManager("openai")
vector_db = VectorDBManager("faiss")
# ... setup vector store with documents

rag_chain = RAGChain(vector_db.get_retriever())
result = rag_chain.query("What is the main topic?")
print(result["answer"])
```

### Using ReAct Agent

```python
from agents.react_agent import ReActAgent
from agents.tools import get_default_tools

tools = get_default_tools()
agent = ReActAgent(tools)
result = agent.run("What's the weather like in New York?")
print(result["answer"])
```

### Using Function Agent

```python
from agents.function_agent import FunctionAgent
from agents.tools import get_default_tools

tools = get_default_tools()
agent = FunctionAgent(tools)
result = agent.run("Calculate 15 * 23")
print(result["answer"])
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_BASE_URL`: OpenAI API base URL (default: https://api.openai.com/v1)
- `OPENAI_MODEL`: OpenAI model to use (default: gpt-3.5-turbo)
- `VECTOR_DB_PATH`: Path for vector database storage
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)

### Vector Database Options

The application supports multiple vector databases:

- **FAISS**: Fast and efficient for large datasets
- **Chroma**: Good for development and small to medium datasets
- **Qdrant**: Production-ready with advanced features

## Development

### Code Formatting

```bash
# Format code with black
poetry run black .

# Sort imports with isort
poetry run isort .

# Run linting with flake8
poetry run flake8 .
```

### Type Checking

```bash
# Run mypy type checking
poetry run mypy .
```

### Testing

```bash
# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=.
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue on the GitHub repository.