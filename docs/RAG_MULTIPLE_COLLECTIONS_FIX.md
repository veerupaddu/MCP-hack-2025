# RAG Multiple Collections Issue & Fix

## 🔍 **Problem Identified:**

You have **TWO separate ChromaDB collections**:

### Collection 1: `insurance_products`
- **Source**: `src/rag/modal-rag.py`
- **Contains**: Insurance PDF documents
- **Indexed by**: `modal run src/rag/modal-rag.py::create_vector_db`

### Collection 2: `product_design`
- **Source**: `src/rag/modal-rag-product-design.py`
- **Contains**: Product design docs (Word, PDF, Excel)
- **Indexed by**: `modal run src/rag/modal-rag-product-design.py::index_product_design`

## ❌ **Current Behavior:**

Your RAG API (`src/rag/rag_api.py` line 92) **ONLY queries `product_design` collection**:

```python
results = self.chroma_service.query.remote(
    collection_name="product_design",  # ← Only this collection!
    query_embeddings=[query_embedding],
    n_results=self.k
)
```

**Result:** PDF documents in `insurance_products` collection are **NEVER retrieved**.

---

## ✅ **Solution Options:**

### **Option 1: Query Both Collections (Recommended)**

Modify the RAG query to search **both collections** and merge results.

### **Option 2: Merge Collections**

Combine both collections into one unified collection.

### **Option 3: Add Collection Parameter**

Allow the user to specify which collection(s) to query.

---

## 🔧 **Implementation: Option 1 (Query Both Collections)**

### **Step 1: Update `rag_api.py`**

Edit `src/rag/rag_api.py` around line 89-103:

```python
def get_relevant_documents(self, query: str):
    query_embedding = self.embeddings.embed_query(query)
    
    # Query BOTH collections
    results_product = self.chroma_service.query.remote(
        collection_name="product_design",
        query_embeddings=[query_embedding],
        n_results=self.k // 2  # Half from each collection
    )
    
    results_insurance = self.chroma_service.query.remote(
        collection_name="insurance_products",
        query_embeddings=[query_embedding],
        n_results=self.k // 2  # Half from each collection
    )
    
    # Merge results
    docs = []
    
    # Add product design docs
    if results_product and 'documents' in results_product and len(results_product['documents']) > 0:
        for i, doc_text in enumerate(results_product['documents'][0]):
            metadata = results_product.get('metadatas', [[{}]])[0][i] if 'metadatas' in results_product else {}
            metadata['collection'] = 'product_design'  # Mark source
            docs.append(Document(page_content=doc_text, metadata=metadata))
    
    # Add insurance PDF docs
    if results_insurance and 'documents' in results_insurance and len(results_insurance['documents']) > 0:
        for i, doc_text in enumerate(results_insurance['documents'][0]):
            metadata = results_insurance.get('metadatas', [[{}]])[0][i] if 'metadatas' in results_insurance else {}
            metadata['collection'] = 'insurance_products'  # Mark source
            docs.append(Document(page_content=doc_text, metadata=metadata))
    
    return docs
```

### **Step 2: Redeploy**

```bash
modal deploy src/rag/rag_api.py
```

---

## 🔧 **Implementation: Option 2 (Merge Collections)**

### **Create a Unified Collection**

Create a new script `src/rag/merge_collections.py`:

```python
import modal

app = modal.App("merge-collections")
vol = modal.Volume.from_name("mcp-hack-ins-products")

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "chromadb>=0.4.0",
    "sentence-transformers>=2.2.0",
)

@app.function(image=image, volumes={"/insurance-data": vol}, timeout=900)
def merge_collections():
    """Merge insurance_products and product_design into unified_docs collection"""
    
    chroma_service = modal.Cls.from_name("chroma-server-v2", "ChromaDB")()
    
    # Get all docs from both collections
    print("📥 Fetching from insurance_products...")
    insurance_docs = chroma_service.get_all.remote("insurance_products")
    
    print("📥 Fetching from product_design...")
    product_docs = chroma_service.get_all.remote("product_design")
    
    # Merge and upsert to new collection
    print("🔀 Merging into unified_docs...")
    
    all_ids = insurance_docs['ids'] + product_docs['ids']
    all_docs = insurance_docs['documents'] + product_docs['documents']
    all_embeddings = insurance_docs['embeddings'] + product_docs['embeddings']
    all_metadatas = insurance_docs['metadatas'] + product_docs['metadatas']
    
    # Add collection source to metadata
    for i, meta in enumerate(all_metadatas):
        if i < len(insurance_docs['ids']):
            meta['original_collection'] = 'insurance_products'
        else:
            meta['original_collection'] = 'product_design'
    
    # Batch upsert
    batch_size = 100
    for i in range(0, len(all_ids), batch_size):
        chroma_service.upsert.remote(
            collection_name="unified_docs",
            ids=all_ids[i:i+batch_size],
            documents=all_docs[i:i+batch_size],
            embeddings=all_embeddings[i:i+batch_size],
            metadatas=all_metadatas[i:i+batch_size]
        )
        print(f"   Batch {i//batch_size + 1}/{(len(all_ids)-1)//batch_size + 1}")
    
    print(f"✅ Merged {len(all_ids)} documents into unified_docs collection")
    return {"total_docs": len(all_ids)}
```

**Then update `rag_api.py` to use `unified_docs` collection.**

---

## 🔧 **Implementation: Option 3 (Add Collection Parameter)**

### **Allow Dynamic Collection Selection**

Modify `mcp_server.py` to specify collections:

```python
response = requests.post(
    config.RAG_API_URL,
    json={
        "question": requirement,
        "top_k": 5,
        "collections": ["product_design", "insurance_products"]  # ← New parameter
    },
    headers={"Content-Type": "application/json"},
    timeout=180
)
```

Then update `rag_api.py` to accept and use the `collections` parameter.

---

## 📊 **Comparison:**

| Option | Pros | Cons | Effort |
|--------|------|------|--------|
| **1. Query Both** | ✅ Simple<br>✅ Keeps collections separate<br>✅ Easy to debug | ❌ 2x queries (slower) | ⭐ Low |
| **2. Merge Collections** | ✅ Single query (faster)<br>✅ Unified search | ❌ Loses collection distinction<br>❌ Need to reindex if sources change | ⭐⭐ Medium |
| **3. Dynamic Selection** | ✅ Flexible<br>✅ User controls sources | ❌ More complex<br>❌ Requires API changes | ⭐⭐⭐ High |

---

## 🚀 **Recommended: Option 1 (Query Both)**

**Why?**
- Quickest to implement
- Keeps your existing collections intact
- Easy to verify it's working
- Can optimize later if needed

**Steps:**
1. Update `src/rag/rag_api.py` with the code above
2. Redeploy: `modal deploy src/rag/rag_api.py`
3. Test your queries - you should now see PDFs referenced!

---

## 🔍 **Verify It's Working:**

After implementing the fix, check the API response:

```json
{
  "answer": "...",
  "sources": [
    {
      "source": "insurance_policy.pdf",
      "collection": "insurance_products"  ← PDF from insurance collection
    },
    {
      "source": "product_design.docx",
      "collection": "product_design"  ← Product doc
    }
  ]
}
```

You should see sources from **BOTH** collections!

---

## 📝 **Summary:**

**Current State:**
- ❌ Only queries `product_design` collection
- ❌ Ignores `insurance_products` collection (PDFs)

**After Fix:**
- ✅ Queries BOTH collections
- ✅ Retrieves PDFs AND product docs
- ✅ Marks source collection in metadata

**Next Step:** Choose an option and implement!

