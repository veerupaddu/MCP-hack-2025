"""
Fast API endpoint for RAG system - optimized for <3 second responses
"""

import modal

app = modal.App("insurance-rag-api")

# Reference your specific volume
vol = modal.Volume.from_name("mcp-hack-ins-products", create_if_missing=True)

# Model configuration
LLM_MODEL = "microsoft/Phi-3-mini-4k-instruct"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# Build image with dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        # Core ML dependencies (compatible versions)
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "sentence-transformers>=2.2.0",
        "huggingface_hub>=0.15.0",

        # LangChain (compatible versions)
        "langchain>=0.1.0",
        "langchain-community>=0.0.13",
        "langchain-core>=0.1.0",  # For Document class

        # Document processing
        "pypdf>=4.0.0",
        "python-docx>=1.1.0",
        "openpyxl>=3.1.0",
        "pandas>=2.0.0",
        "xlrd>=2.0.0",

        # Vector database
        "chromadb>=0.4.0",

        # Web framework
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.20.0",

        # LLM inference (vLLM - latest stable)
        "vllm>=0.4.0",

        # Utilities
        "cryptography>=41.0.0",
    )
)

@app.cls(
    image=image,
    volumes={"/insurance-data": vol},
    gpu="A10G",
    timeout=600,  # 10 minutes for LLM loading and query processing
    scaledown_window=300,  # Keep warm for 5 minutes after last request
    max_containers=2,  # Allow scaling
    min_containers=0,  # Start from 0 to save costs (will auto-scale on demand)
)
class FastRAGService:
    """Optimized RAG service for fast API responses"""
    
    @modal.enter()
    def enter(self):
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from vllm import LLM, SamplingParams
        from langchain_core.documents import Document
        
        print("🚀 Initializing Fast RAG Service...")
        
        # Initialize embeddings (faster model)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cuda'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Connect to Chroma directly (not remote service)
        import chromadb
        print("   Connecting to ChromaDB...")
        self.chroma_client = chromadb.PersistentClient(path="/insurance-data/chroma_db")
        self.chroma_collection = self.chroma_client.get_collection("langchain")
        print(f"   ✅ Connected to langchain collection ({self.chroma_collection.count()} documents)")
        
        # Custom retriever with direct ChromaDB access
        class DirectChromaRetriever:
            def __init__(self, collection, embeddings, k=5):
                self.collection = collection
                self.embeddings = embeddings
                self.k = k
            
            def get_relevant_documents(self, query: str):
                # Generate query embedding
                query_embedding = self.embeddings.embed_query(query)
                
                print(f"   Querying langchain collection (top {self.k})...")
                # Query directly
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=self.k
                )
                
                docs = []
                
                # Add retrieved docs
                if results and 'documents' in results and len(results['documents']) > 0:
                    for i, doc_text in enumerate(results['documents'][0]):
                        metadata = results.get('metadatas', [[{}]])[0][i] if 'metadatas' in results else {}
                        metadata['collection'] = 'langchain'
                        docs.append(Document(page_content=doc_text, metadata=metadata))
                    print(f"   ✅ Retrieved {len(results['documents'][0])} docs from langchain")
                    # Print sources for debugging
                    for i, meta in enumerate(results.get('metadatas', [[]])[0][:3]):
                        print(f"      {i+1}. {meta.get('source', 'Unknown')[:80]}")
                else:
                    print(f"   ⚠️  No documents found")
                
                print(f"   📊 Total documents retrieved: {len(docs)}")
                return docs
        
        self.Retriever = DirectChromaRetriever
        
        # Load LLM with optimized settings for speed
        print("   Loading LLM (optimized for speed)...")
        self.llm_engine = LLM(
            model=LLM_MODEL,
            dtype="float16",
            gpu_memory_utilization=0.9,  # Higher utilization for speed
            max_model_len=4096,
            trust_remote_code=True,
            enforce_eager=True,
            enable_prefix_caching=True,  # Cache prefixes for faster generation
        )
        
        # Optimized sampling params for speed
        self.default_sampling_params = SamplingParams(
            temperature=0.7,
            max_tokens=1024,  # Reduced from 1536 for faster responses
            top_p=0.9,
            stop=["\n\n\n", "Question:", "Context:", "<|end|>"]
        )
        
        print("✅ Fast RAG Service ready!")
    
    @modal.method()
    def query(self, question: str, top_k: int = 5, max_tokens: int = 1024):
        """Fast query method optimized for <3 second responses"""
        import time
        start_time = time.time()
        
        # Retrieve documents
        retrieval_start = time.time()
        retriever = self.Retriever(
            collection=self.chroma_collection,
            embeddings=self.embeddings,
            k=top_k
        )
        docs = retriever.get_relevant_documents(question)
        retrieval_time = time.time() - retrieval_start
        
        if not docs:
            return {
                "answer": "No relevant information found in the product design document.",
                "retrieval_time": retrieval_time,
                "generation_time": 0,
                "total_time": time.time() - start_time,
                "sources": [],
                "success": False
            }
        
        # Build context (limit size for speed)
        context = "\n\n".join([doc.page_content[:800] for doc in docs[:3]])  # Limit to top 3 docs, 800 chars each
        
        # Create prompt
        prompt = f"""<|system|>
You are a helpful AI assistant. Answer questions about the TokyoDrive Insurance product design document concisely and accurately.<|end|>
<|user|>
Context:
{context}

Question:
{question}<|end|>
<|assistant|>"""
        
        # Generate with optimized params
        from vllm import SamplingParams
        sampling_params = SamplingParams(
            temperature=0.7,
            max_tokens=max_tokens,
            top_p=0.9,
            stop=["\n\n\n", "Question:", "Context:", "<|end|>"]
        )
        
        gen_start = time.time()
        outputs = self.llm_engine.generate(prompts=[prompt], sampling_params=sampling_params)
        answer = outputs[0].outputs[0].text.strip()
        generation_time = time.time() - gen_start
        
        # Prepare sources (limited for speed)
        sources = []
        for doc in docs[:3]:  # Limit to 3 sources
            sources.append({
                "content": doc.page_content[:300],
                "metadata": doc.metadata
            })
        
        total_time = time.time() - start_time
        
        return {
            "answer": answer,
            "retrieval_time": retrieval_time,
            "generation_time": generation_time,
            "total_time": total_time,
            "sources": sources,
            "success": True
        }

# Deploy as web endpoint
@app.function(
    image=image,
    volumes={"/insurance-data": vol},
)
@modal.concurrent(max_inputs=10)  # Handle multiple concurrent requests
@modal.asgi_app()
def fastapi_app():
    """Deploy FastAPI app - all imports inside to avoid local dependency issues"""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    
    # Request/Response models
    class QueryRequest(BaseModel):
        question: str
        top_k: int = 5
        max_tokens: int = 1024  # Reduced for faster responses

    class QueryResponse(BaseModel):
        answer: str
        retrieval_time: float
        generation_time: float
        total_time: float
        sources: list
        success: bool
    
    # FastAPI app
    web_app = FastAPI(title="Product Design RAG API", version="1.0.0")
    
    # CORS
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize RAG service
    rag_service = FastRAGService()
    
    @web_app.get("/health")
    async def health():
        """Health check endpoint"""
        return {"status": "healthy", "service": "rag-api"}
    
    @web_app.post("/query", response_model=QueryResponse)
    async def query_rag(request: QueryRequest):
        """
        Query the RAG system - optimized for <3 second responses
        
        Args:
            question: The question to ask
            top_k: Number of documents to retrieve (default: 5)
            max_tokens: Maximum tokens in response (default: 1024)
        
        Returns:
            QueryResponse with answer, timing, and sources
        """
        try:
            result = rag_service.query.remote(
                question=request.question,
                top_k=request.top_k,
                max_tokens=request.max_tokens
            )
            
            if not result.get("success", True):
                raise HTTPException(status_code=404, detail="No relevant information found")
            
            return QueryResponse(**result)
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
    
    @web_app.get("/")
    async def root():
        """API root endpoint"""
        return {
            "service": "Product Design RAG API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "query": "/query (POST)"
            },
            "target_response_time": "<3 seconds"
        }
    
    return web_app
