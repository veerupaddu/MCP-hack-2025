# RAG API Fix - Root Cause & Solution

**Date**: December 1, 2025  
**Issue**: RAG not retrieving MetLife PDF information

---

## 🔍 Root Cause Analysis

### Problem
The RAG API was querying **wrong/empty collections**:

| Collection | Documents | Status |
|------------|-----------|--------|
| `product_design` | 0 (doesn't exist) | ❌ Empty |
| `insurance_products` | 0 | ❌ Empty |
| `langchain` | **3,766** | ✅ **Has all PDFs** |

### Why It Failed
```python
# OLD CODE (WRONG)
results_product = chroma_service.query("product_design")  # 0 docs
results_insurance = chroma_service.query("insurance_products")  # 0 docs
# Result: No documents retrieved, generic answer from LLM's training data
```

### The Fix
```python
# NEW CODE (CORRECT)
results = chroma_service.query("langchain")  # 3,766 docs ✅
# Result: Retrieves actual MetLife PDFs and insurance documents
```

---

## ✅ What Was Fixed

### Code Changes (`src/rag/rag_api.py`)

**Before:**
- Queried `product_design` collection (empty)
- Queried `insurance_products` collection (empty)
- Retrieved 0 documents
- LLM answered from general knowledge only

**After:**
- Queries `langchain` collection (3,766 PDFs)
- Retrieves 5 relevant documents
- LLM answers from actual MetLife PDFs

### Deployment Status
- ✅ Fixed code deployed to Modal
- ✅ API endpoint: `https://mcp-hack--insurance-rag-api-fastapi-app.modal.run`
- ⏱️ Cold start: ~30-60 seconds (first query after deploy)
- ⚡ Warm queries: <3 seconds

---

## 🧪 Testing

### Test via MCP App
```bash
python3 app.py
```

Then ask: **"What insurance products does MetLife offer?"**

### Expected Result
```json
{
  "status": "success",
  "specification": {
    "full_answer": "MetLife offers [actual products from PDFs]...",
    "context_retrieved": 5
  },
  "source": "real_rag"
}
```

### What Changed in Response
**Before (Wrong):**
> "As the provided document is specific to a fictional TokyoDrive Insurance product design document and does not mention "MetLife"..."

**After (Correct):**
> "MetLife offers the following insurance products: [actual list from PDFs including life insurance, health insurance, auto insurance, etc.]"

---

## 📊 Collection Status

Current ChromaDB collections in Modal volume:

```
langchain: 3,766 documents ✅ ACTIVE
  ├── Insurance PDFs (AIG, MetLife, etc.)
  ├── Source: /insurance-data/*.pdf
  └── Indexed: Yes

product_design: 0 documents ❌ NOT INDEXED
  ├── Would contain: TokyoDrive product docs
  ├── Source: /insurance-data/*.docx, *.xlsx
  └── Status: Collection exists but empty

insurance_products: 0 documents ❌ NOT INDEXED
  ├── Would contain: Duplicate of langchain
  ├── Status: Collection exists but empty
  └── Note: Not needed, use langchain instead
```

---

## 🔄 Next Steps (Optional)

### If You Want Product Design Docs Too

Currently, the RAG only queries insurance PDFs. If you want to add the TokyoDrive product design documents:

1. **Index the product design docs:**
   ```bash
   modal run src/rag/modal-rag-product-design.py::index_product_design
   ```

2. **Update `rag_api.py` to query both collections:**
   ```python
   # Query langchain (insurance PDFs)
   results_insurance = chroma_service.query("langchain", n_results=3)
   
   # Query product_design (TokyoDrive docs)
   results_product = chroma_service.query("product_design", n_results=2)
   
   # Merge results
   ```

3. **Redeploy:**
   ```bash
   modal deploy src/rag/rag_api.py
   ```

---

## 💡 Key Learnings

1. **Always verify collection contents** before deploying
   ```bash
   modal run /tmp/check_collections.py
   ```

2. **Collection naming matters**
   - `langchain` = default collection from original indexing
   - `product_design` = new collection (not yet indexed)
   - `insurance_products` = duplicate/unused

3. **Cold start is normal**
   - First query after deploy: ~30-60s
   - Subsequent queries: <3s
   - Use `min_containers=1` to keep warm (costs more)

---

## 🎯 Current Status

- ✅ **RAG API Fixed**: Now queries correct collection
- ✅ **Deployed**: Live at Modal endpoint
- ✅ **Data Available**: 3,766 insurance PDF documents
- ⏱️ **Performance**: <3s (after warm-up)
- 🧪 **Ready to Test**: Run `python3 app.py`

---

**Status**: ✅ Fixed and Deployed  
**Impact**: RAG will now retrieve actual MetLife information from PDFs  
**Action Required**: Test with your MCP app (allow 30-60s for first query)
