# Modal RAG Performance Optimization Guide

**Current Performance**: >1 minute per query  
**Target Performance**: <5 seconds per query

## 🔍 Performance Bottleneck Analysis

### Current Architecture Issues

1. **Model Loading Time** (~30-45 seconds)
   - Mistral-7B (13GB) loads on every cold start
   - Embedding model loads separately
   - No model caching between requests

2. **LLM Inference Time** (~15-30 seconds)
   - Mistral-7B is slow for inference
   - Running on A10G GPU (good, but model is large)
   - No inference optimization (quantization, etc.)

3. **Network Latency** (~2-5 seconds)
   - Remote ChromaDB calls
   - Modal container communication overhead

---

## 🚀 Optimization Strategies (Ranked by Impact)

### 1. **Keep Containers Warm** ⭐⭐⭐⭐⭐
**Impact**: Eliminates 30-45s cold start time

**Current**:
```python
min_containers=1  # Already doing this ✅
```

**Why it helps**: Your container stays loaded with models in memory. First query after deployment is slow, but subsequent queries are fast.

**Cost**: ~$0.50-1.00/hour for warm A10G container

---

### 2. **Switch to Smaller/Faster LLM** ⭐⭐⭐⭐⭐
**Impact**: Reduces inference from 15-30s to 2-5s

**Options**:

#### Option A: Mistral-7B-Instruct-v0.2 (Quantized)
```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

self.model = AutoModelForCausalLM.from_pretrained(
    LLM_MODEL,
    quantization_config=quantization_config,
    device_map="auto"
)
```
- **Speed**: 3-5x faster (5-10s → 1-3s)
- **Quality**: Minimal degradation
- **Memory**: 13GB → 3.5GB

#### Option B: Switch to Phi-3-mini (3.8B)
```python
LLM_MODEL = "microsoft/Phi-3-mini-4k-instruct"
```
- **Speed**: 5-10x faster than Mistral-7B
- **Quality**: Good for RAG tasks
- **Memory**: ~8GB → 4GB
- **Inference**: 2-4 seconds

#### Option C: Use TinyLlama-1.1B
```python
LLM_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
```
- **Speed**: 10-20x faster
- **Quality**: Lower, but acceptable for simple queries
- **Memory**: ~2GB
- **Inference**: <1 second

---

### 3. **Use vLLM for Inference** ⭐⭐⭐⭐
**Impact**: 2-5x faster inference

```python
# Install vLLM
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "vllm==0.6.0",
    # ... other packages
)

# In RAGModel.enter()
from vllm import LLM, SamplingParams

self.llm_engine = LLM(
    model=LLM_MODEL,
    tensor_parallel_size=1,
    gpu_memory_utilization=0.9,
    max_model_len=2048  # Shorter context for speed
)

# In query method
sampling_params = SamplingParams(
    temperature=0.7,
    max_tokens=256,
    top_p=0.9
)
outputs = self.llm_engine.generate([prompt], sampling_params)
```

**Benefits**:
- Continuous batching
- PagedAttention (efficient memory)
- Optimized CUDA kernels
- 2-5x faster than HuggingFace pipeline

---

### 4. **Optimize Embedding Generation** ⭐⭐⭐
**Impact**: Reduces query embedding time from 1-2s to 0.2-0.5s

#### Option A: Use Smaller Embedding Model
```python
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# 384 dimensions vs 384 (bge-small is already good)
```

#### Option B: Use ONNX Runtime
```python
from optimum.onnxruntime import ORTModelForFeatureExtraction

self.embeddings = ORTModelForFeatureExtraction.from_pretrained(
    EMBEDDING_MODEL,
    export=True,
    provider="CUDAExecutionProvider"
)
```
- **Speed**: 2-3x faster
- **Quality**: Identical

---

### 5. **Reduce Context Window** ⭐⭐⭐
**Impact**: Faster LLM processing

```python
# In query method
sampling_params = SamplingParams(
    max_tokens=128,  # Instead of 256 or 512
    temperature=0.7
)

# Reduce retrieved documents
top_k = 2  # Instead of 3
```

**Why**: Less tokens to process = faster inference

---

### 6. **Cache ChromaDB Queries** ⭐⭐
**Impact**: Saves 1-2s on repeated queries

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def get_cached_docs(query_hash):
    return self.retriever.get_relevant_documents(query)

# In query method
query_hash = hashlib.md5(question.encode()).hexdigest()
docs = get_cached_docs(query_hash)
```

---

### 7. **Use Faster GPU** ⭐⭐
**Impact**: 1.5-2x faster inference

```python
@app.cls(
    gpu="A100",  # Instead of A10G
    # or
    gpu="H100",  # Even faster
)
```

**Cost**: A100 is 2-3x more expensive than A10G

---

### 8. **Parallel Processing** ⭐⭐
**Impact**: Overlap embedding + retrieval

```python
import asyncio

async def query_async(self, question: str):
    # Run embedding and LLM prep in parallel
    embedding_task = asyncio.create_task(
        self.get_query_embedding(question)
    )
    
    # ... rest of async pipeline
```

---

## 🎯 Recommended Implementation Plan

### Phase 1: Quick Wins (Get to <10s)
1. ✅ **Keep containers warm** (already done)
2. **Add 4-bit quantization** to Mistral-7B
3. **Reduce max_tokens** to 128
4. **Use top_k=2** instead of 3

**Expected**: 60s → 8-12s

---

### Phase 2: Major Speedup (Get to <5s)
1. **Switch to vLLM** for inference
2. **Use Phi-3-mini** instead of Mistral-7B
3. **Optimize embeddings** with ONNX

**Expected**: 8-12s → 3-5s

---

### Phase 3: Ultra-Fast (Get to <2s)
1. **Use TinyLlama** for simple queries
2. **Implement query caching**
3. **Upgrade to A100 GPU**

**Expected**: 3-5s → 1-2s

---

## 📊 Performance Comparison Table

| Configuration | Cold Start | Warm Query | Cost/Hour | Quality |
|--------------|------------|------------|-----------|---------|
| **Current** (Mistral-7B, A10G) | 45s | 15-30s | $0.50 | ⭐⭐⭐⭐⭐ |
| **Phase 1** (Quantized, warm) | 30s | 8-12s | $0.50 | ⭐⭐⭐⭐ |
| **Phase 2** (vLLM + Phi-3) | 20s | 3-5s | $0.50 | ⭐⭐⭐⭐ |
| **Phase 3** (TinyLlama, A100) | 10s | 1-2s | $1.50 | ⭐⭐⭐ |

---

## 🔧 Code Changes for Phase 2 (Recommended)

### 1. Update model configuration
```python
LLM_MODEL = "microsoft/Phi-3-mini-4k-instruct"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"  # Keep same
```

### 2. Add vLLM to dependencies
```python
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "vllm==0.6.0",
    "langchain==0.3.7",
    # ... rest
)
```

### 3. Update RAGModel.enter()
```python
from vllm import LLM, SamplingParams

self.llm_engine = LLM(
    model=LLM_MODEL,
    tensor_parallel_size=1,
    gpu_memory_utilization=0.85,
    max_model_len=2048
)

self.sampling_params = SamplingParams(
    temperature=0.7,
    max_tokens=128,
    top_p=0.9
)
```

### 4. Update query method
```python
# Build prompt
prompt = f"""Use the following context to answer the question.

Context: {context}

Question: {question}

Answer:"""

# Generate with vLLM
outputs = self.llm_engine.generate([prompt], self.sampling_params)
answer = outputs[0].outputs[0].text
```

---

## 💰 Cost vs Performance Trade-offs

| Approach | Speed Gain | Cost Change | Implementation |
|----------|-----------|-------------|----------------|
| Quantization | 3-5x | $0 | Easy |
| vLLM | 2-5x | $0 | Medium |
| Smaller model | 5-10x | $0 | Easy |
| A100 GPU | 1.5-2x | +200% | Easy |
| Caching | Variable | $0 | Medium |

---

## 🎬 Next Steps

1. **Measure current performance** with logging
2. **Implement Phase 1** (quantization + reduce tokens)
3. **Test and measure** improvement
4. **Implement Phase 2** if needed (vLLM + Phi-3)
5. **Monitor** and iterate

---

## 📝 Performance Monitoring Code

Add this to track performance:

```python
import time

@modal.method()
def query(self, question: str, top_k: int = 2):
    start = time.time()
    
    # Embedding time
    embed_start = time.time()
    retriever = self.RemoteChromaRetriever(...)
    embed_time = time.time() - embed_start
    
    # Retrieval time
    retrieval_start = time.time()
    docs = retriever.get_relevant_documents(question)
    retrieval_time = time.time() - retrieval_start
    
    # LLM time
    llm_start = time.time()
    result = chain.invoke({"question": question})
    llm_time = time.time() - llm_start
    
    total_time = time.time() - start
    
    print(f"⏱️ Performance:")
    print(f"  Embedding: {embed_time:.2f}s")
    print(f"  Retrieval: {retrieval_time:.2f}s")
    print(f"  LLM: {llm_time:.2f}s")
    print(f"  Total: {total_time:.2f}s")
    
    return result
```

This will help you identify the exact bottleneck!
