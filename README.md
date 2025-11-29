# MCP Hack - Insurance Product Design RAG System

A comprehensive RAG (Retrieval Augmented Generation) system for querying and analyzing auto insurance product design documents, specifically designed for the Tokyo market.

## 📁 Repository Structure

```
/
├── src/                          # Core application code
│   ├── rag/                      # RAG system implementation
│   │   ├── modal-rag.py                    # Main RAG system
│   │   └── modal-rag-product-design.py     # Product design RAG
│   └── web/                      # Web application
│       ├── web_app.py                       # Flask web server
│       ├── query_product_design.py         # RAG query interface
│       ├── templates/                      # HTML templates
│       └── static/                         # CSS, JS, assets
│
├── scripts/                       # Utility scripts
│   ├── data/                     # Data processing scripts
│   ├── setup/                    # Setup and installation scripts
│   └── tools/                    # General utility scripts
│
├── docs/                         # Documentation
│   ├── guides/                   # How-to guides and tutorials
│   ├── api/                      # API documentation
│   └── product-design/           # Product design documents
│
├── tests/                         # Test files
├── diagrams/                     # System architecture diagrams
├── finetune/                      # Model fine-tuning documentation
├── bkp/                           # Backup files
└── venv/                          # Python virtual environment
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Modal account and CLI installed
- Virtual environment activated

### Installation

1. **Clone and setup:**
   ```bash
   git clone <repo-url>
   cd mcp-hack
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Index product design documents:**
   ```bash
   modal run src/rag/modal-rag-product-design.py::index_product_design
   ```

3. **Start web interface:**
   ```bash
   python src/web/web_app.py
   # Or use the helper script:
   ./scripts/setup/start_web.sh
   ```

4. **Access the web interface:**
   - Open `http://127.0.0.1:5000` in your browser
   - Ask questions about the product design document

## 📖 Documentation

- **Quick Start Guide:** `docs/guides/QUICK_START_RAG.md`
- **Web Interface:** `docs/guides/WEB_INTERFACE.md`
- **Troubleshooting:** `docs/guides/TROUBLESHOOTING.md`
- **Product Design Docs:** `docs/product-design/`

## 🔧 Key Components

### RAG System (`src/rag/`)
- **modal-rag.py**: Main RAG system for insurance products
- **modal-rag-product-design.py**: Specialized RAG for product design documents

### Web Application (`src/web/`)
- **web_app.py**: Flask web server with REST API
- **query_product_design.py**: RAG query interface
- **templates/**: HTML templates for the web UI
- **static/**: CSS and JavaScript files

### Scripts (`scripts/`)
- **data/**: Data processing and conversion scripts
- **setup/**: Installation and setup scripts
- **tools/**: Utility scripts for various tasks

## 🎯 Usage Examples

### Query via CLI
```bash
python src/web/query_product_design.py --question "What are the premium ranges?"
```

### Query via Web Interface
1. Start the web app: `python src/web/web_app.py`
2. Open `http://127.0.0.1:5000`
3. Enter your question and submit

### Query via Modal Directly
```bash
modal run src/rag/modal-rag-product-design.py::query_product_design --question "How to make product decisions?"
```

## 📊 Features

- ✅ RAG-based document querying
- ✅ Web interface for easy interaction
- ✅ Support for markdown and Word documents
- ✅ Vector database with ChromaDB
- ✅ Fast inference with vLLM
- ✅ Comprehensive documentation

## 🛠️ Development

### Running Tests
```bash
python -m pytest tests/
```

### Adding New Documents
1. Add documents to Modal volume
2. Run indexing: `modal run src/rag/modal-rag-product-design.py::index_product_design`

### Project Structure Guidelines
- **src/**: Core application code only
- **scripts/**: Utility scripts organized by purpose
- **docs/**: Documentation organized by type
- **tests/**: All test files

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]
