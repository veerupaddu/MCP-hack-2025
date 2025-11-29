# Troubleshooting Guide

## Modal Command Not Found

### Error
```
FileNotFoundError: [Errno 2] No such file or directory: 'modal'
```

### Solutions

#### Option 1: Activate Virtual Environment (Recommended)
```bash
source venv/bin/activate
python query_product_design.py --index
```

#### Option 2: Use venv's Modal Directly
```bash
./venv/bin/modal run src/modal-rag-product-design.py::index_product_design
```

#### Option 3: Install Modal Globally
```bash
pip3 install modal
python query_product_design.py --index
```

#### Option 4: Use Python Module Syntax
```bash
python3 -m modal run src/modal-rag-product-design.py::index_product_design
```

## Quick Fix

The script should auto-detect Modal in your venv. If it doesn't work:

1. **Activate venv first:**
   ```bash
   source venv/bin/activate
   ```

2. **Then run:**
   ```bash
   python query_product_design.py --index
   ```

## Other Common Issues

### "No documents found"
- Make sure documents are in Modal volume:
  ```bash
  modal volume put mcp-hack-ins-products \
    docs/tokyo_auto_insurance_product_design_filled.md \
    docs/tokyo_auto_insurance_product_design.docx
  ```

### "Collection not found"
- Run indexing first:
  ```bash
  python query_product_design.py --index
  ```

### Slow First Query
- Normal! First query takes 10-15 seconds (cold start)
- Subsequent queries are faster (3-5 seconds)

### Import Errors
- Make sure you're in the project directory
- Check that all dependencies are installed in venv

