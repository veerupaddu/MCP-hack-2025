# Repository Structure

This document describes the organization of the repository.

## Directory Layout

```
mcp-hack/
├── src/                          # Core application source code
│   ├── rag/                      # RAG (Retrieval Augmented Generation) system
│   │   ├── modal-rag.py                    # Main RAG system for insurance products
│   │   └── modal-rag-product-design.py     # Product design document RAG
│   └── web/                      # Web application
│       ├── web_app.py                       # Flask web server
│       ├── query_product_design.py          # RAG query CLI interface
│       ├── templates/                       # HTML templates
│       │   └── index.html
│       └── static/                          # Static assets
│           ├── css/
│           │   └── style.css
│           └── js/
│               └── app.js
│
├── scripts/                       # Utility scripts organized by purpose
│   ├── data/                     # Data processing scripts
│   │   ├── download_*.py         # Data download scripts
│   │   ├── convert_*.py          # Data conversion scripts
│   │   ├── prepare_*.py          # Data preparation scripts
│   │   └── cleanup_*.py          # Data cleanup scripts
│   ├── setup/                    # Setup and installation scripts
│   │   ├── start_web.sh          # Start web application
│   │   └── run_with_venv.sh      # Run scripts with venv
│   └── tools/                     # General utility scripts
│       ├── api_endpoint*.py       # API endpoint scripts
│       ├── finetune_*.py          # Fine-tuning scripts
│       └── debug_*.py             # Debugging utilities
│
├── docs/                         # Documentation
│   ├── guides/                   # How-to guides and tutorials
│   │   ├── QUICK_START_RAG.md
│   │   ├── WEB_INTERFACE.md
│   │   ├── TROUBLESHOOTING.md
│   │   └── ...                   # Other guides
│   ├── api/                      # API documentation (if any)
│   └── product-design/           # Product design documents
│       ├── tokyo_auto_insurance_product_design.md
│       ├── tokyo_auto_insurance_product_design_filled.md
│       ├── tokyo_auto_insurance_product_design.docx
│       ├── PRODUCT_DECISION_GUIDE.md
│       └── setup_product_design_rag.md
│
├── tests/                         # Test files
│   ├── test_server.py
│   └── test_web.py
│
├── diagrams/                      # System architecture diagrams
│   ├── *.mmd                      # Mermaid diagram sources
│   └── *.svg                      # Rendered diagrams
│
├── finetune/                      # Model fine-tuning documentation
│   ├── README.md
│   └── *.md                       # Fine-tuning guides
│
├── bkp/                           # Backup files (old versions)
│
├── config/                        # Configuration files (if any)
│
├── venv/                          # Python virtual environment (gitignored)
│
├── README.md                      # Main project README
├── MIGRATION_GUIDE.md            # Guide for migrating from old structure
├── STRUCTURE.md                   # This file
└── .gitignore                    # Git ignore rules
```

## Key Directories

### `src/`
Contains all core application code. Organized into:
- **`rag/`**: RAG system implementations using Modal
- **`web/`**: Web application (Flask) with templates and static assets

### `scripts/`
Utility scripts organized by purpose:
- **`data/`**: Data processing, downloading, conversion
- **`setup/`**: Installation and setup scripts
- **`tools/`**: General utilities, API endpoints, debugging tools

### `docs/`
Documentation organized by type:
- **`guides/`**: How-to guides and tutorials
- **`api/`**: API documentation
- **`product-design/`**: Product design documents

### `tests/`
All test files for the application.

## File Naming Conventions

- Python scripts: `snake_case.py`
- Documentation: `UPPER_CASE.md` or `kebab-case.md`
- Shell scripts: `kebab-case.sh`
- Config files: `.config` or `config.json`

## Import Paths

When importing from this repository:

```python
# From root directory
import sys
sys.path.insert(0, 'src/web')
from query_product_design import query_rag

# Or add src to path
sys.path.insert(0, 'src')
from rag.modal_rag_product_design import ...
```

## Running Applications

### Web Application
```bash
# From project root
python src/web/web_app.py

# Or use helper script
./scripts/setup/start_web.sh
```

### RAG Queries
```bash
# CLI
python src/web/query_product_design.py --question "your question"

# Modal direct
modal run src/rag/modal-rag-product-design.py::query_product_design --question "your question"
```

## Adding New Files

When adding new files, follow the structure:
- **Application code** → `src/`
- **Utility scripts** → `scripts/{data,setup,tools}/`
- **Documentation** → `docs/{guides,api,product-design}/`
- **Tests** → `tests/`
- **Config** → `config/`

