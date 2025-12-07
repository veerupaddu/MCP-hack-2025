# 🧠 Dual RAG System

Retrieval Augmented Generation system with two data sources for comprehensive insurance product context.

## 📁 Files

| File | Purpose |
|------|---------|
| `rag_dual_query.py` | **Query API** ⭐ - FastAPI endpoint for dual-source queries |
| `rag_existing_products.py` | Index insurance PDFs into `existing_products` collection |
| `rag_product_design.py` | Index design DOCX/XLSX into `product_design` collection |

## 📂 Data Sources

| Collection | Source Folders | File Types |
|------------|----------------|------------|
| `existing_products` | `aig/`, `metlife/`, `sonpo/`, `japan_post/` | PDFs |
| `product_design` | `docs/` | DOCX, XLSX |

## 🚀 Quick Start

```bash
# Step 1: Index existing products (PDFs)
./venv/bin/modal run src/rag/rag_existing_products.py

# Step 2: Index product design (DOCX)
./venv/bin/modal run src/rag/rag_product_design.py

# Step 3: Deploy dual query API
./venv/bin/modal deploy src/rag/rag_dual_query.py
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/retrieve` | POST | Auto-route query to best source |
| `/query/existing` | POST | Query existing products only |
| `/query/design` | POST | Query product design only |
| `/query/both` | POST | Query both sources |
| `/health` | GET | Health check |

## 📝 Request Example

```bash
curl -X POST https://mcp-hack--insurance-rag-dual-query-fastapi-app.modal.run/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question": "What are TokyoDrive pricing tiers?", "source": "auto", "top_k": 5}'
```

## 🔍 Intelligent Routing

The API auto-routes queries based on keywords:

- **→ Existing Products**: "metlife", "aig", "sonpo", "competitor", "market"
- **→ Product Design**: "tokyodrive", "our product", "pricing tier", "coverage"
- **→ Both Sources**: When no clear signal detected
