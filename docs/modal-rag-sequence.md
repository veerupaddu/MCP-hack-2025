# Modal RAG System - Sequence Diagrams

This document provides sequence diagrams for the Modal RAG (Retrieval Augmented Generation) application.

## 1. Indexing Flow (create_vector_db)

```mermaid
sequenceDiagram
    participant User
    participant Modal
    participant CreateVectorDB as create_vector_db()
    participant PDFLoader
    participant TextSplitter
    participant Embeddings as HuggingFaceEmbeddings<br/>(CUDA)
    participant ChromaDB as Remote ChromaDB

    User->>Modal: modal run modal-rag.py::index
    Modal->>CreateVectorDB: Execute function
    
    CreateVectorDB->>PDFLoader: Load PDFs from /insurance-data
    PDFLoader-->>CreateVectorDB: Return documents
    
    CreateVectorDB->>TextSplitter: Split documents (chunk_size=1000)
    TextSplitter-->>CreateVectorDB: Return chunks
    
    CreateVectorDB->>Embeddings: Initialize (device='cuda')
    CreateVectorDB->>Embeddings: Generate embeddings for chunks
    Embeddings-->>CreateVectorDB: Return embeddings
    
    CreateVectorDB->>ChromaDB: Connect to remote service
    CreateVectorDB->>ChromaDB: Upsert chunks + embeddings
    ChromaDB-->>CreateVectorDB: Confirm storage
    
    CreateVectorDB-->>Modal: Complete
    Modal-->>User: Success message
```

## 2. Query Flow (RAGModel.query)

```mermaid
sequenceDiagram
    participant User
    participant Modal
    participant QueryEntrypoint as query()
    participant RAGModel
    participant Embeddings as HuggingFaceEmbeddings<br/>(CUDA)
    participant ChromaRetriever as RemoteChromaRetriever
    participant ChromaDB as Remote ChromaDB
    participant LLM as Mistral-7B<br/>(A10G GPU)
    participant RAGChain as LangChain RAG

    User->>Modal: modal run modal-rag.py::query --question "..."
    Modal->>QueryEntrypoint: Execute local entrypoint
    QueryEntrypoint->>RAGModel: Instantiate RAGModel()
    
    Note over RAGModel: @modal.enter() lifecycle
    RAGModel->>Embeddings: Load embedding model (CUDA)
    RAGModel->>ChromaDB: Connect to remote service
    RAGModel->>LLM: Load Mistral-7B (A10G GPU)
    RAGModel->>RAGModel: Initialize RemoteChromaRetriever
    
    QueryEntrypoint->>RAGModel: query.remote(question)
    
    RAGModel->>ChromaRetriever: Create retriever instance
    RAGModel->>RAGChain: Build RAG chain
    
    RAGChain->>ChromaRetriever: Retrieve relevant docs
    ChromaRetriever->>Embeddings: embed_query(question)
    Embeddings-->>ChromaRetriever: Query embedding
    ChromaRetriever->>ChromaDB: query(embedding, k=3)
    ChromaDB-->>ChromaRetriever: Top-k documents
    ChromaRetriever-->>RAGChain: Return documents
    
    RAGChain->>LLM: Generate answer with context
    LLM-->>RAGChain: Generated answer
    RAGChain-->>RAGModel: Return result
    
    RAGModel-->>QueryEntrypoint: Return {answer, sources}
    QueryEntrypoint-->>User: Display answer + sources
```

## 3. Web Endpoint Flow (RAGModel.web_query)

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant Modal as Modal Platform
    participant WebEndpoint as RAGModel.web_query
    participant QueryMethod as RAGModel.query
    participant RAGChain
    participant ChromaDB
    participant LLM

    User->>Browser: GET https://.../web_query?question=...
    Browser->>Modal: HTTP GET request
    Modal->>WebEndpoint: Route to @modal.fastapi_endpoint
    
    WebEndpoint->>QueryMethod: Call query.local(question)
    
    Note over QueryMethod,LLM: Same flow as Query diagram
    QueryMethod->>RAGChain: Build chain
    RAGChain->>ChromaDB: Retrieve docs
    RAGChain->>LLM: Generate answer
    LLM-->>QueryMethod: Return result
    
    QueryMethod-->>WebEndpoint: Return {answer, sources}
    WebEndpoint-->>Modal: JSON response
    Modal-->>Browser: HTTP 200 + JSON
    Browser-->>User: Display result
```

## 4. Container Lifecycle (RAGModel)

```mermaid
sequenceDiagram
    participant Modal
    participant Container
    participant RAGModel
    participant GPU as A10G GPU
    participant Volume as Modal Volume
    participant ChromaDB

    Modal->>Container: Start container (min_containers=1)
    Container->>GPU: Allocate GPU
    Container->>Volume: Mount /insurance-data
    
    Container->>RAGModel: Call @modal.enter()
    
    Note over RAGModel: Initialization phase
    RAGModel->>RAGModel: Load HuggingFaceEmbeddings (CUDA)
    RAGModel->>ChromaDB: Connect to remote service
    RAGModel->>RAGModel: Load Mistral-7B (GPU)
    RAGModel->>RAGModel: Create RemoteChromaRetriever class
    
    RAGModel-->>Container: Ready
    Container-->>Modal: Container warm and ready
    
    Note over Modal,Container: Container stays warm (min_containers=1)
    
    loop Handle requests
        Modal->>RAGModel: Invoke query() method
        RAGModel-->>Modal: Return result
    end
    
    Note over Modal,Container: Container persists until scaled down
```

## Key Components

### Modal Configuration
- **App Name**: `insurance-rag`
- **Volume**: `mcp-hack-ins-products` mounted at `/insurance-data`
- **GPU**: A10G for RAGModel class
- **Autoscaling**: `min_containers=1`, `max_containers=1` (always warm)

### Models
- **LLM**: `mistralai/Mistral-7B-Instruct-v0.3` (GPU, float16)
- **Embeddings**: `BAAI/bge-small-en-v1.5` (GPU, CUDA)

### Storage
- **Vector DB**: Remote ChromaDB service (`chroma-server-v2`)
- **Collection**: `insurance_products`
- **Chunk Size**: 1000 characters with 200 overlap

### Endpoints
- **Local Entrypoints**: `list`, `index`, `query`
- **Web Endpoint**: `RAGModel.web_query` (FastAPI GET endpoint)
