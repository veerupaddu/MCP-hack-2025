# RAG Sources & Controls Explained

## 📚 **What Sources Does RAG Use?**

Your RAG system uses documents from the Modal volume `mcp-hack-ins-products` stored in ChromaDB.

### **Current Data Sources:**

#### 1. **Document Types Indexed:**
- ✅ **Word Documents** (`.docx`) - Product design specs
- ✅ **PDF Files** (`.pdf`) - Insurance documents, policies
- ✅ **Excel Files** (`.xlsx`, `.xls`) - Data tables, statistics
- ❌ **Markdown Files** (`.md`) - **EXCLUDED** (as per your request)

#### 2. **Specific Files Indexed:**
Based on your configuration, the RAG system looks for:
- Files containing `tokyo_auto_insurance` in the name
- Files containing `product_design` in the name
- All PDFs in `/insurance-data/` directory

#### 3. **Collection Name:**
- **Collection**: `product_design` (in ChromaDB)
- **Total Documents**: ~3,766 chunks (as shown in your diagram)

---

## 🔧 **How Document Chunking Works:**

### **Chunking Parameters:**
```python
chunk_size=1000        # Each chunk is ~1000 characters
chunk_overlap=200      # 200 characters overlap between chunks
```

**Why overlap?** To maintain context across chunk boundaries.

**Example:**
```
Document: "The Tokyo auto insurance product offers three tiers: Basic, Standard, and Premium..."

Chunk 1: "The Tokyo auto insurance product offers three tiers: Basic, Standard, and Premium. 
          Basic tier includes liability coverage up to ¥50M..."
          
Chunk 2: "...Basic tier includes liability coverage up to ¥50M. Standard tier adds comprehensive 
          coverage and roadside assistance..."
```

---

## 🎯 **Retrieval Controls (top_k Parameter)**

### **Current Default:**
```python
top_k = 5  # Retrieves 5 most relevant chunks
```

### **What `top_k` Does:**
- Searches the vector database for the **most similar** chunks to your query
- Returns the **top K** results based on cosine similarity
- More chunks = more context, but also more noise

### **How to Adjust:**

#### **In `mcp_server.py`:**
```python
response = requests.post(
    config.RAG_API_URL,
    json={"question": requirement, "top_k": 5},  # ← Change this number
    headers={"Content-Type": "application/json"},
    timeout=180
)
```

#### **Recommended Values:**
- `top_k=3`: **Fast**, focused answers (less context)
- `top_k=5`: **Balanced** (current default)
- `top_k=10`: **Comprehensive**, but slower and may include irrelevant info
- `top_k=15`: **Maximum context**, risk of confusion

---

## 🔍 **Why RAG Might Not Use All Sources:**

### **1. Semantic Similarity Filtering**
RAG uses **vector similarity** to find relevant chunks:
- Only retrieves chunks **semantically similar** to your query
- If your query is about "pricing", it won't retrieve chunks about "claims process"

### **2. Limited by `top_k`**
- If `top_k=5`, only 5 chunks are retrieved
- Even if 100 chunks are relevant, only the top 5 are used

### **3. Context Window Limit**
The LLM (Phi-3-mini) has a **4096 token limit**:
```
Prompt template + Query + Retrieved chunks + Answer space = 4096 tokens
```
- If chunks are too long, some may be truncated
- Current `max_tokens=1024` for answer, leaving ~3000 tokens for context

### **4. Collection Scope**
RAG only searches the `product_design` collection:
```python
collection_name="product_design"
```
- If you have multiple collections, only this one is queried
- Other collections (if any) are ignored

---

## 🎛️ **How to Control RAG Behavior:**

### **Option 1: Increase `top_k` (More Context)**

**Edit `mcp/mcp_server.py` line 84:**
```python
json={"question": requirement, "top_k": 10},  # Increased from 5 to 10
```

**Effect:**
- ✅ More comprehensive answers
- ✅ Uses more source documents
- ❌ Slower response time
- ❌ May include less relevant info

---

### **Option 2: Adjust Chunk Size (Reindex Required)**

**Edit `src/rag/modal-rag-product-design.py` line 252-254:**
```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,    # Increased from 1000
    chunk_overlap=300   # Increased from 200
)
```

**Then reindex:**
```bash
modal run src/rag/modal-rag-product-design.py::index_product_design
```

**Effect:**
- ✅ Larger chunks = more context per retrieval
- ❌ Fewer total chunks in database
- ❌ May exceed context window faster

---

### **Option 3: Increase LLM Context Window**

**Edit `src/rag/rag_api.py` line 122:**
```python
max_tokens=1536,  # Increased from 1024
```

**Effect:**
- ✅ Longer, more detailed answers
- ❌ Slower generation
- ❌ May exceed 3-second target

---

### **Option 4: Use Multiple Collections**

**Current:** Only searches `product_design` collection

**To add more sources:**
1. Create additional collections (e.g., `insurance_policies`, `claims_data`)
2. Modify query to search multiple collections
3. Merge results before sending to LLM

---

### **Option 5: Adjust Similarity Threshold**

**Add to retrieval logic:**
```python
# Only use chunks with similarity > 0.7
filtered_docs = [doc for doc in docs if doc.similarity > 0.7]
```

**Effect:**
- ✅ Higher quality, more relevant chunks
- ❌ May retrieve fewer documents

---

## 📊 **Current RAG Pipeline:**

```
User Query
    ↓
[1] Convert query to embedding (BAAI/bge-small-en-v1.5)
    ↓
[2] Search ChromaDB "product_design" collection
    ↓
[3] Retrieve top_k=5 most similar chunks
    ↓
[4] Combine chunks into context
    ↓
[5] Send to LLM (Phi-3-mini via vLLM)
    ↓
[6] Generate answer (max 1024 tokens)
    ↓
Response
```

---

## 🔬 **How to Inspect What's Being Retrieved:**

### **Method 1: Check Logs**
When RAG runs, it prints:
```
[RAG] Calling remote endpoint: ...
```

### **Method 2: Inspect ChromaDB**
```bash
modal run src/rag/inspect_rag_docs.py
```

This shows:
- Total documents in collection
- Unique sources
- Sample documents

### **Method 3: Add Debug Logging**

**Edit `mcp/mcp_server.py` line 91-93:**
```python
answer = result.get("answer", "")
sources = result.get("sources", [])

# ADD THIS:
print(f"[DEBUG] Retrieved {len(sources)} sources:")
for i, source in enumerate(sources):
    print(f"  [{i+1}] {source.get('source', 'Unknown')} - {source.get('page_content', '')[:100]}...")
```

---

## 🎯 **Recommended Settings for Your Use Case:**

### **For Comprehensive Answers (Use All Available Sources):**
```python
# In mcp_server.py
json={"question": requirement, "top_k": 10}

# In rag_api.py
max_tokens=1536
```

### **For Fast, Focused Answers:**
```python
# In mcp_server.py
json={"question": requirement, "top_k": 3}

# In rag_api.py
max_tokens=512
```

### **For Balanced Performance (Current):**
```python
# In mcp_server.py
json={"question": requirement, "top_k": 5}

# In rag_api.py
max_tokens=1024
```

---

## 🚀 **Quick Fixes:**

### **"RAG not using enough sources"**
→ Increase `top_k` from 5 to 10

### **"RAG answers are too generic"**
→ Check if documents are properly indexed: `modal run src/rag/inspect_rag_docs.py`

### **"RAG is slow"**
→ Decrease `top_k` from 5 to 3

### **"RAG gives irrelevant answers"**
→ Your query might not match document content semantically. Try rephrasing.

---

## 📝 **Summary:**

**Current Configuration:**
- **Sources**: Word, PDF, Excel files in `mcp-hack-ins-products` volume
- **Collection**: `product_design` (3,766 chunks)
- **Retrieval**: Top 5 most similar chunks (`top_k=5`)
- **Chunk Size**: 1000 characters with 200 overlap
- **LLM Output**: Max 1024 tokens
- **Timeout**: 180 seconds

**To Use More Sources:**
1. Increase `top_k` to 10 or 15
2. Verify all documents are indexed
3. Consider larger chunk sizes (requires reindexing)

**Trade-offs:**
- More sources = More comprehensive but slower
- Fewer sources = Faster but may miss information

