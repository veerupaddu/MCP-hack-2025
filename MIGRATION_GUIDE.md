# Repository Restructure Migration Guide

## What Changed

The repository has been reorganized for better structure and maintainability.

## File Moves

### RAG System
- `src/modal-rag.py` → `src/rag/modal-rag.py`
- `src/modal-rag-product-design.py` → `src/rag/modal-rag-product-design.py`

### Web Application
- `web_app.py` → `src/web/web_app.py`
- `query_product_design.py` → `src/web/query_product_design.py`
- `templates/` → `src/web/templates/`
- `static/` → `src/web/static/`

### Scripts
- Data processing scripts → `scripts/data/`
- Setup scripts → `scripts/setup/`
- Utility scripts → `scripts/tools/`

### Documentation
- All `.md` files → `docs/guides/`
- Product design docs → `docs/product-design/`

### Tests
- `test_*.py` → `tests/`

## Updated Commands

### Old Commands (No longer work)
```bash
python web_app.py
modal run src/modal-rag-product-design.py::query_product_design
```

### New Commands
```bash
# Web app
python src/web/web_app.py
# Or use helper script
./scripts/setup/start_web.sh

# Modal RAG
modal run src/rag/modal-rag-product-design.py::query_product_design --question "your question"

# Indexing
modal run src/rag/modal-rag-product-design.py::index_product_design
```

## Import Path Updates

If you have custom scripts that import from these modules, update the imports:

```python
# Old
from query_product_design import query_rag

# New
import sys
sys.path.insert(0, 'src/web')
from query_product_design import query_rag
```

## Next Steps

1. Update any custom scripts with new import paths
2. Update CI/CD pipelines if applicable
3. Update documentation references
4. Test all functionality

## Rollback

If you need to rollback, all files are still in git history. You can:
```bash
git log --oneline --all -- "old/path/to/file"
git checkout <commit-hash> -- "old/path/to/file"
```

