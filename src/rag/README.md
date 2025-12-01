# RAG (Retrieval Augmented Generation) System

This directory contains all components for the RAG system that powers intelligent querying of insurance product documentation and design specifications.

## 📁 Directory Overview

The RAG system consists of production-ready components:

- **Production API** (`rag_api.py`) - Fast FastAPI endpoint for Modal deployment ⭐
- **Product Design RAG** (`modal-rag-product-design.py`) - Document indexing and querying ⭐
- **Client Library** (`api_client.py`) - Python client for API interaction
- **Documentation** (`README.md`) - This file
- **Package** (`__init__.py`) - Python package configuration

**Note**: Legacy/alternative implementations have been moved to `bkp/rag/` for reference.

---

## 🚀 Core Files (Priority: HIGH)

### 1. `rag_api.py` ⭐ **[PRODUCTION]**

**Purpose**: Fast FastAPI endpoint optimized for sub-3 second responses

**Key Features**:
- **Dual Collection Retrieval**: Queries both `product_design` (Word/Excel docs) and `insurance_products` (PDFs)
- **Performance Optimizations**:
  - Warm containers (`min_containers=1`)
  - Fast scaledown (`scaledown_window=60s`)
  - Prefix caching for repeated queries
  - GPU memory optimization (`gpu_memory_utilization=0.85`)
  - Concurrent request handling
- **FastAPI Endpoints**:
  - `POST /query` - Query the RAG system
  - `GET /health` - Health check

**Usage**:
```bash
# Deploy to Modal
modal deploy src/rag/rag_api.py

# Check deployment status
modal app list

# Query via API
curl -X POST https://your-modal-url/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the product features?", "top_k": 5}'
```

**Configuration**:
- `LLM_MODEL`: `microsoft/Phi-3-mini-4k-instruct`
- `EMBEDDING_MODEL`: `BAAI/bge-small-en-v1.5`
- `top_k`: 5 (split 3:2 between collections)
- `max_tokens`: 1024
- Response time: **<3 seconds** (warm) / ~10s (cold start)

**Collections**:
- `product_design`: TokyoDrive product design documents (.docx, .xlsx)
- `insurance_products`: Insurance PDFs (MetLife, competitor analysis, etc.)

---

### 2. `modal-rag-product-design.py` ⭐ **[INDEXING & QUERY]**

**Purpose**: Extended RAG system for indexing and querying product design documents

**Key Features**:
- **Document Loading**: Supports Word (.docx), PDF (.pdf), Excel (.xlsx/.xls)
- **Excludes**: All markdown files (`.md`)
- **Indexing**: Creates embeddings and stores in ChromaDB
- **Query**: Retrieves relevant context and generates answers using vLLM

**Usage**:
```bash
# Index documents (run once or when docs change)
modal run src/rag/modal-rag-product-design.py::index_product_design

# Query the system
modal run src/rag/modal-rag-product-design.py::query_product_design \
  --query "What are the pricing tiers?"

# List indexed files
modal run src/rag/modal-rag-product-design.py::list_volume_files
```

**Document Processing**:
- **Word (.docx)**: Extracts text from paragraphs and tables
- **PDF (.pdf)**: Extracts text using pypdf
- **Excel (.xlsx/.xls)**: Converts sheets to text format
- **Text Splitting**: 1000 char chunks with 200 char overlap

**Storage**:
- Modal Volume: `mcp-hack-ins-products`
- ChromaDB Collection: `product_design`
- Location: `/insurance-data/chroma_db/`

---

### 3. `api_client.py` 📦 **[CLIENT LIBRARY]**

**Purpose**: Python client for interacting with the RAG API

**Usage**:
```python
from src.rag.api_client import RAGAPIClient

# Initialize client
client = RAGAPIClient(base_url="https://your-modal-url")

# Health check
health = client.health_check()
print(health)  # {"status": "healthy", ...}

# Query the RAG
result = client.query(
    question="What are the product features?",
    top_k=5,
    max_tokens=1024,
    timeout=5
)

print(result["answer"])
print(result["sources"])
print(result["timing"])
```

**Methods**:
- `health_check()` - Check API status
- `query(question, top_k, max_tokens, timeout)` - Query the RAG system

---

---

## 📦 Archived Files

Legacy and alternative implementations have been moved to `bkp/rag/` for reference:

- **`rag_service.py`** - Standalone Flask service (for Nebius/Docker)
- **`rag_vllm.py`** - Optimized vLLM implementation
- **`modal-rag.py`** - Original base RAG system
- **`inspect_rag_docs.py`** - ChromaDB inspection tool
- **`debug_chroma.py`** - Quick health check utility

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

