# Quick Start Guide

## Prerequisites

- Python 3.13+
- Modal account and CLI installed
- Virtual environment (recommended)

## Setup

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install flask flask-cors
   # Or install all requirements if you have requirements.txt
   pip install -r requirements.txt
   ```

3. **Index product design documents (first time only):**
   ```bash
   modal run src/rag/modal-rag-product-design.py::index_product_design
   ```

## Running the Web Application

### Option 1: Using the helper script (Recommended)
```bash
./scripts/setup/start_web.sh
```

### Option 2: Direct Python command
```bash
# Make sure venv is activated
source venv/bin/activate
python src/web/web_app.py
```

### Option 3: From project root
```bash
python3 src/web/web_app.py
```

## Access the Web Interface

Once the server starts, open your browser and go to:
- **http://127.0.0.1:5000** (or the port shown in the terminal)

⚠️ **Important:** Use `127.0.0.1` instead of `localhost` to avoid potential 403 errors on macOS.

## Querying the RAG System

### Via Web Interface
1. Start the web app (see above)
2. Open the URL in your browser
3. Enter your question and click "Ask Question"

### Via CLI
```bash
python src/web/query_product_design.py --question "your question here"
```

### Via Modal Directly
```bash
modal run src/rag/modal-rag-product-design.py::query_product_design --question "your question here"
```

## Troubleshooting

### Flask Not Installed
```bash
# Activate venv
source venv/bin/activate

# Install Flask
pip install flask flask-cors
```

### Port Already in Use
The web app will automatically find an available port (5000-5009).

### Modal Command Not Found
```bash
# Install Modal CLI
pip install modal

# Or use python -m modal
python -m modal --version
```

For more help, see `docs/guides/TROUBLESHOOTING.md`.

