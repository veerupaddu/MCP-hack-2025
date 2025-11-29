# Nebius Deployment Guide

This guide covers deploying the Insurance Product Design RAG system to Nebius cloud platform.

## Overview

Your current setup uses **Modal** for:
- GPU-accelerated RAG inference (vLLM)
- Vector database (ChromaDB)
- Document storage (Modal Volumes)

For **Nebius**, we'll adapt this to use:
- Nebius GPU instances for inference
- Self-hosted or managed ChromaDB
- Object storage or persistent volumes for documents

## Deployment Options

### Option 1: Full VM Deployment (Recommended for Production)
Deploy everything on a single Nebius VM with GPU.

**Pros:**
- Full control
- Lower latency (everything local)
- Cost-effective for consistent usage

**Cons:**
- Requires infrastructure management
- Manual scaling

### Option 2: Container-Based Deployment
Use Nebius Container Service with GPU support.

**Pros:**
- Easier scaling
- Better isolation
- CI/CD friendly

**Cons:**
- Slightly more complex setup
- Container orchestration needed

### Option 3: Hybrid (Recommended)
- RAG inference on Nebius GPU VM
- Web app on lightweight VM or container
- ChromaDB on separate instance or managed service

## Prerequisites

1. **Nebius Account**
   - Sign up at https://nebius.com
   - Create a project
   - Set up billing

2. **Nebius CLI** (optional but recommended)
   ```bash
   # Install Nebius CLI
   pip install nebius-cli
   ```

3. **Docker** (for container deployment)
   ```bash
   # Install Docker if not already installed
   ```

## Step-by-Step Deployment

### Step 1: Prepare Deployment Files

Create the following structure:

```
deployment/
├── Dockerfile.rag          # RAG service container
├── Dockerfile.web          # Web app container
├── docker-compose.yml       # Orchestration (optional)
├── requirements.txt        # Python dependencies
└── nebius-config.yaml      # Nebius configuration
```

### Step 2: Create Dockerfile for RAG Service

Create `deployment/Dockerfile.rag`:

```dockerfile
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /app

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/rag/ /app/src/rag/
COPY src/web/query_product_design.py /app/

# Set environment variables
ENV PYTHONPATH=/app
ENV CUDA_VISIBLE_DEVICES=0

# Expose port (if running as service)
EXPOSE 8000

# Default command
CMD ["python3", "-m", "src.rag.rag_service"]
```

### Step 3: Create RAG Service (Standalone)

Create `src/rag/rag_service.py` (Nebius-compatible version):

```python
"""
Standalone RAG service for Nebius deployment
Replaces Modal-specific code with standard Python/Flask
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
from pathlib import Path

# Import your RAG components (adapted for Nebius)
from langchain_community.embeddings import HuggingFaceEmbeddings
from vllm import LLM, SamplingParams
from langchain.schema import Document
import chromadb

app = Flask(__name__)
CORS(app)

# Configuration
LLM_MODEL = "microsoft/Phi-3-mini-4k-instruct"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "/data/chroma")
DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", "/data/documents")

# Initialize models (load once at startup)
print("🚀 Initializing RAG service...")

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={'device': 'cuda'},
    encode_kwargs={'normalize_embeddings': True}
)

print("   Loading LLM...")
llm_engine = LLM(
    model=LLM_MODEL,
    dtype="float16",
    gpu_memory_utilization=0.85,
    max_model_len=4096,
    trust_remote_code=True,
    enforce_eager=True
)

sampling_params = SamplingParams(
    temperature=0.7,
    max_tokens=1536,
    top_p=0.9,
    stop=["\n\n\n", "Question:", "Context:", "<|end|>"]
)

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
collection = chroma_client.get_or_create_collection("product_design")

print("✅ RAG service ready!")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/query', methods=['POST'])
def query():
    """Query the RAG system"""
    data = request.json
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({"error": "Question is required"}), 400
    
    start_time = time.time()
    
    # Generate query embedding
    query_embedding = embeddings.embed_query(question)
    
    # Retrieve from ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )
    
    retrieval_time = time.time() - start_time
    
    if not results['documents'] or len(results['documents'][0]) == 0:
        return jsonify({
            "question": question,
            "answer": "No relevant information found.",
            "retrieval_time": retrieval_time,
            "generation_time": 0,
            "sources": []
        })
    
    # Build context
    context = "\n\n".join(results['documents'][0])
    
    # Generate prompt
    prompt = f"""<|system|>
You are a helpful AI assistant that answers questions about the TokyoDrive Insurance product design document. 
Provide comprehensive, detailed answers with specific information from the document.<|end|>
<|user|>
Context from Product Design Document:
{context}

Question:
{question}<|end|>
<|assistant|>"""
    
    # Generate answer
    gen_start = time.time()
    outputs = llm_engine.generate(prompts=[prompt], sampling_params=sampling_params)
    answer = outputs[0].outputs[0].text.strip()
    generation_time = time.time() - gen_start
    
    # Prepare sources
    sources = []
    for i, doc in enumerate(results['documents'][0]):
        sources.append({
            "content": doc[:500],
            "metadata": results.get('metadatas', [[{}]])[0][i] if results.get('metadatas') else {}
        })
    
    return jsonify({
        "question": question,
        "answer": answer,
        "retrieval_time": retrieval_time,
        "generation_time": generation_time,
        "sources": sources
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
```

### Step 4: Create Requirements File

Create `deployment/requirements.txt`:

```txt
flask==3.0.0
flask-cors==4.0.0
vllm==0.6.3.post1
langchain==0.3.7
langchain-community==0.3.7
langchain-text-splitters==0.3.2
sentence-transformers==3.3.0
chromadb==0.5.20
pypdf==5.1.0
python-docx==1.1.0
markdown==3.5.1
cryptography==43.0.3
transformers==4.46.2
torch==2.4.0
huggingface_hub==0.26.2
```

### Step 5: Update Web App for Nebius

Modify `src/web/web_app.py` to call Nebius RAG service instead of Modal:

```python
# In query_rag function, replace Modal call with HTTP request:

import requests

def query_rag(question: str):
    """Query the RAG system via Nebius service"""
    rag_service_url = os.getenv("RAG_SERVICE_URL", "http://localhost:8000")
    
    try:
        response = requests.post(
            f"{rag_service_url}/query",
            json={"question": question},
            timeout=180
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Error connecting to RAG service: {str(e)}"
        }
```

### Step 6: Create Nebius VM

1. **Via Nebius Console:**
   - Go to Compute → Virtual Machines
   - Create new VM
   - Select GPU instance (e.g., n1-standard-4 with GPU)
   - Choose Ubuntu 22.04 LTS
   - Configure network (allow ports 5000, 8000)
   - Create and connect via SSH

2. **Via CLI:**
   ```bash
   nebius compute instance create \
     --name rag-service \
     --zone us-central1-a \
     --machine-type n1-standard-4 \
     --accelerator type=nvidia-tesla-t4,count=1 \
     --image-family ubuntu-2204-lts \
     --image-project ubuntu-os-cloud \
     --boot-disk-size 100GB
   ```

### Step 7: Deploy to Nebius VM

```bash
# SSH into your Nebius VM
ssh user@<nebius-vm-ip>

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone your repository
git clone <your-repo-url>
cd mcp-hack

# Build and run RAG service
cd deployment
docker build -f Dockerfile.rag -t rag-service .
docker run -d \
  --name rag-service \
  --gpus all \
  -p 8000:8000 \
  -v /data/chroma:/data/chroma \
  -v /data/documents:/data/documents \
  rag-service

# Build and run web app
docker build -f Dockerfile.web -t web-app .
docker run -d \
  --name web-app \
  -p 5000:5000 \
  -e RAG_SERVICE_URL=http://localhost:8000 \
  web-app
```

### Step 8: Index Documents

```bash
# SSH into VM
ssh user@<nebius-vm-ip>

# Run indexing script
docker exec -it rag-service python3 -m src.rag.index_documents
```

## Alternative: Using Nebius Container Service

If Nebius has a container service (similar to GKE):

```yaml
# deployment/nebius-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rag-service
  template:
    metadata:
      labels:
        app: rag-service
    spec:
      containers:
      - name: rag-service
        image: your-registry/rag-service:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            nvidia.com/gpu: 1
          limits:
            nvidia.com/gpu: 1
        env:
        - name: CHROMA_PERSIST_DIR
          value: "/data/chroma"
        volumeMounts:
        - name: chroma-data
          mountPath: /data/chroma
      volumes:
      - name: chroma-data
        persistentVolumeClaim:
          claimName: chroma-pvc
```

## Migration Checklist

- [ ] Create Nebius account and project
- [ ] Set up Nebius VM with GPU
- [ ] Create RAG service (standalone, no Modal)
- [ ] Set up ChromaDB (local or managed)
- [ ] Update web app to use HTTP API instead of Modal
- [ ] Create Dockerfiles
- [ ] Deploy RAG service
- [ ] Deploy web app
- [ ] Index documents
- [ ] Test end-to-end
- [ ] Set up monitoring
- [ ] Configure auto-scaling (if needed)

## Cost Estimation

**Nebius GPU VM (n1-standard-4 + T4):**
- ~$0.35-0.50/hour
- ~$250-360/month (if running 24/7)

**Storage:**
- ChromaDB data: ~$0.10/GB/month
- Documents: ~$0.02/GB/month

**Total estimated:** $300-400/month for 24/7 operation

## Next Steps

1. Review this guide
2. Choose deployment option (VM recommended)
3. Create Nebius account
4. Follow step-by-step instructions
5. Test deployment
6. Monitor and optimize

## Support

For Nebius-specific issues:
- Nebius Documentation: https://nebius.com/docs
- Nebius Support: support@nebius.com

For application issues, see `docs/guides/TROUBLESHOOTING.md`.

