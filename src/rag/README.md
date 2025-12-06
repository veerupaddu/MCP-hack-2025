# RAG (Retrieval Augmented Generation) System

This directory contains all components for the RAG system that powers intelligent querying of insurance product documentation and design specifications.

## 📁 Directory Overview

The RAG system consists of **two data sources** for comprehensive context:

### 🔷 Core Files

| File | Purpose | Collection |
|------|---------|------------|
| `rag_existing_products.py` | Index insurance PDFs | `existing_products` |
| `rag_product_design.py` | Index design docs | `product_design` |
| `rag_dual_query.py` | **Query both sources** ⭐ | Both |

### 📂 Data Sources

| Collection | Source Folders | File Types |
|------------|----------------|------------|
| `existing_products` | `aig/`, `metlife/`, `sonpo/`, `japan_post/` | PDFs |
| `product_design` | `docs/` | DOCX, XLSX |

> **Note**: Legacy implementations moved to `bkp/rag/` for reference.


---

## 🚀 Quick Start

### Step 1: Index Existing Products (Insurance PDFs)
```bash
cd /Users/veeru/agents/mcp-hack
./venv/bin/modal run src/rag/rag_existing_products.py
```

### Step 2: Index Product Design Documents
```bash
./venv/bin/modal run src/rag/rag_product_design.py
```

### Step 3: Deploy Dual Query API
```bash
./venv/bin/modal deploy src/rag/rag_dual_query.py
```

### Step 4: Test the API
```bash
# Query with intelligent routing (auto-detects source)
curl -X POST https://your-modal-url/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question": "What are TokyoDrive pricing tiers?"}'

# Query existing products only
curl -X POST https://your-modal-url/query/existing \
  -H "Content-Type: application/json" \
  -d '{"question": "What does MetLife offer?"}'

# Query product design only
curl -X POST https://your-modal-url/query/design \
  -H "Content-Type: application/json" \
  -d '{"question": "What coverage does TokyoDrive have?"}'
```

---

## 🔍 Intelligent Routing

The dual query API automatically routes queries based on keywords:

**→ Existing Products**: "existing", "current", "competitor", "metlife", "aig", "sonpo", "market", "compare"

**→ Product Design**: "tokyodrive", "new product", "our product", "design", "specification", "pricing tier", "coverage", "feature"

**→ Both Sources**: When no clear signal, queries both collections

---

## 📦 File Details

### `rag_existing_products.py` 📄 **[INDEX INSURANCE PDFs]**

**Purpose**: Index all insurance company PDFs into `existing_products` collection

**Source Folders**:
- `/insurance-data/aig/`
- `/insurance-data/metlife/`
- `/insurance-data/sonpo/`
- `/insurance-data/japan_post/`

**Usage**:
```bash
# List available PDF files
modal run src/rag/rag_existing_products.py::list_existing_product_files

# Run full indexing
modal run src/rag/rag_existing_products.py
```

---

### `rag_product_design.py` 📝 **[INDEX DESIGN DOCS]**

**Purpose**: Index product design documents into `product_design` collection

**Source Folders**:
- `/insurance-data/docs/`
- `/insurance-data/docs/product-design/`

**Supported Formats**: `.docx`, `.xlsx`, `.xls`

**Usage**:
```bash
# List available design files
modal run src/rag/rag_product_design.py::list_product_design_files

# Run full indexing
modal run src/rag/rag_product_design.py
```

---

### `rag_dual_query.py` ⭐ **[DUAL QUERY API]**

**Purpose**: FastAPI endpoint that queries both collections with intelligent routing

**Endpoints**:
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/retrieve` | POST | Auto-route query |
| `/query/existing` | POST | Query existing products |
| `/query/design` | POST | Query product design |
| `/query/both` | POST | Query both sources |

**Request Format**:
```json
{
  "question": "What are the pricing tiers?",
  "source": "auto",  // "auto", "existing", "design", "both"
  "top_k": 3
}
```

**Response Format**:
```json
{
  "documents": [...],
  "sources_queried": ["existing_products", "product_design"],
  "detected_source": "both",
  "retrieval_time": 0.234,
  "success": true
}
```

---

## � Troubleshooting

### Check Modal Apps
```bash
./venv/bin/modal app list
```

### View Volume Contents
```bash
./venv/bin/modal volume ls mcp-hack-ins-products
```

### Check Collection Status
After indexing, each collection should show document counts in the logs.

---

## 📁 Legacy Files

Legacy implementations have been moved to `bkp/rag/`:
- `rag_api.py` - Original single-source API
- `modal-rag-product-design.py` - Original indexing script
- `rag_api_fast.py` - Fast API variant
- `api_client.py` - Python client library
- `rag_service.py` - Standalone Flask service
- `rag_vllm.py` - Optimized vLLM implementation
- `modal-rag.py` - Original base RAG system
- `inspect_rag_docs.py` - ChromaDB inspection tool
- `debug_chroma.py` - Quick health check utility


These files are kept as backups but are not actively used in production. If you need them, they can be restored from `bkp/rag/`.

---

## 📊 Data Flow

### Indexing Flow

```
Documents (Word/PDF/Excel)
    ↓
Load & Parse (modal-rag-product-design.py)
    ↓
Text Splitting (1000 chars, 200 overlap)
    ↓
Generate Embeddings (BAAI/bge-small-en-v1.5)
    ↓
Store in ChromaDB (product_design collection)
    ↓
Persist to Modal Volume
```

### Query Flow

```
User Question
    ↓
Generate Query Embedding
    ↓
Retrieve Top-K Documents (5 docs: 3 from product_design, 2 from insurance_products)
    ↓
Construct Prompt with Context
    ↓
Generate Answer (Phi-3-mini via vLLM)
    ↓
Return Answer + Sources + Timing
```

---

## 🔑 Key Concepts

### ChromaDB Collections

| Collection | Content | Source Files |
|------------|---------|--------------|
| `product_design` | TokyoDrive product specs | `.docx`, `.xlsx` |
| `insurance_products` | Insurance PDFs | `.pdf` |
| `langchain` | Legacy insurance docs | `.pdf` (old) |

### Models

| Model | Purpose | Size | Performance |
|-------|---------|------|-------------|
| `Phi-3-mini-4k-instruct` | Text generation | 3.8B params | ~1s/query |
| `BAAI/bge-small-en-v1.5` | Embeddings | 33M params | ~0.1s/query |

### Performance Targets

- **Cold Start**: ~10 seconds (first query after deploy)
- **Warm Query**: <3 seconds (subsequent queries)
- **Retrieval**: ~0.5 seconds
- **Generation**: ~0.5-1.5 seconds

---

## 🚀 Quick Start

### 1. Deploy Production API

```bash
# Deploy to Modal
modal deploy src/rag/rag_api.py

# Get the API URL
modal app show insurance-rag-api
```

### 2. Index Your Documents

```bash
# Upload documents to Modal volume
modal volume put mcp-hack-ins-products docs/tokyo_auto_insurance_product_design.docx /insurance-data/

# Index documents
modal run src/rag/modal-rag-product-design.py::index_product_design
```

### 3. Query the System

```bash
# Via Python client
python -c "
from src.rag.api_client import RAGAPIClient
client = RAGAPIClient('https://your-modal-url')
result = client.query('What are the product features?')
print(result['answer'])
"

# Or via curl
curl -X POST https://your-modal-url/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the pricing tiers?"}'
```

---

## 🐛 Troubleshooting

### Issue: "No documents retrieved"

**Solution**: Check if documents are indexed
```bash
modal run src/rag/debug_chroma.py
```

### Issue: "Timeout errors"

**Solution**: Increase timeout in client
```python
client.query(question="...", timeout=30)
```

### Issue: "Cold start too slow"

**Solution**: Use `rag_api.py` with `min_containers=1` (already configured)

### Issue: "Not finding PDFs"

**Solution**: Verify both collections are being queried
```python
# Check rag_api.py line ~150
# Should query BOTH product_design AND insurance_products
```

---

## 📚 Related Documentation

- **API Docs**: `docs/api/RAG_API.md`
- **Quick Start**: `QUICK_START_API.md`
- **Deployment**: `docs/deployment/NEBIUS_DEPLOYMENT.md`
- **RAG Sources**: `docs/RAG_SOURCES_EXPLAINED.md`
- **Troubleshooting**: `docs/guides/TROUBLESHOOTING.md`

---

## 🔄 Migration Notes

### From Legacy Systems to Current Production

**Old implementations** (now in `bkp/rag/`):
- `modal-rag.py` - CLI-based, single collection
- `rag_vllm.py` - Class-based, complex setup
- `rag_service.py` - Flask-based, for non-Modal deployments

**Current production** (active in `src/rag/`):
- `rag_api.py` - FastAPI, dual collection, optimized
- `modal-rag-product-design.py` - Document indexing

**Migration**:
```bash
# Old way (CLI)
modal run src/rag/modal-rag.py::query_insurance_docs --query "..."

# New way (API)
curl -X POST https://your-modal-url/query -d '{"question": "..."}'
```

---

## 📝 Development

### Adding New Document Types

1. Update `modal-rag-product-design.py::load_product_design_docs()`
2. Add new file extension handling
3. Reindex documents
4. Test retrieval

### Optimizing Performance

1. Adjust `top_k` (fewer docs = faster)
2. Reduce `max_tokens` (shorter answers = faster)
3. Enable prefix caching (already enabled)
4. Increase `min_containers` (more warm containers)

### Testing

```bash
# Test indexing
modal run src/rag/modal-rag-product-design.py::index_product_design

# Test query
modal run src/rag/modal-rag-product-design.py::query_product_design \
  --query "test query"

# Test API
python -m pytest tests/test_rag_system.py
```

---

## 🎯 Current Status

### ✅ Working
- FastAPI production endpoint (`rag_api.py`)
- Dual collection retrieval (product_design + insurance_products)
- Sub-3 second response times
- Document indexing (Word/PDF/Excel)
- Python client library

### 🚧 In Progress
- None (system is production-ready)

### 📋 Future Enhancements
- Add more document types (PowerPoint, etc.)
- Implement semantic caching
- Add multi-language support
- Implement RAG evaluation metrics

---

## 📞 Support

For issues or questions:
1. Check `docs/guides/TROUBLESHOOTING.md`
2. Review `docs/RAG_SOURCES_EXPLAINED.md`
3. Run debug scripts (`debug_chroma.py`, `inspect_rag_docs.py`)
4. Check Modal logs: `modal app logs insurance-rag-api`

---

**Last Updated**: December 2025  
**Maintainer**: MCP Hack Team  
**Status**: Production Ready ✅

