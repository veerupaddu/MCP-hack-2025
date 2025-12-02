"""
Ultra-Fast RAG API - Optimized for <3 second responses
Key optimizations:
1. min_containers=1 to keep warm
2. Smaller context window (500 chars × 2 docs)
3. Reduced max_tokens (256)
4. Aggressive caching
5. Lighter embedding model
"""

import modal

app = modal.App("insurance-rag-fast")

# Reference your specific volume
vol = modal.Volume.from_name("mcp-hack-ins-products", create_if_missing=True)

# Model configuration - using smaller, faster models
LLM_MODEL = "microsoft/Phi-3-mini-4k-instruct"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"  # Small and fast

# Build image with minimal dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "sentence-transformers>=2.2.0",
        "huggingface_hub>=0.15.0",
        "langchain-core>=0.1.0",
        "chromadb>=0.4.0",
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.20.0",
        "vllm>=0.4.0",
    )
)

@app.cls(
    image=image,
    volumes={"/insurance-data": vol},
    gpu="A10G",
    timeout=300,
    scaledown_window=600,  # Keep warm for 10 minutes
    max_containers=3,
    min_containers=1,  # ALWAYS keep 1 container warm - eliminates cold start!
)
class FastRAGService:
    """Ultra-optimized RAG service for <3 second responses"""
    
    @modal.enter()
    def enter(self):
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from vllm import LLM, SamplingParams
        
        print("🚀 Initializing Ultra-Fast RAG Service...")
        
        # Initialize embeddings with CUDA
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cuda'},
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 1}
        )

        # Connect to ChromaDB
        import chromadb
        print("   Connecting to ChromaDB...")
        self.chroma_client = chromadb.PersistentClient(path="/insurance-data/chroma_db")
        self.chroma_collection = self.chroma_client.get_collection("langchain")
        print(f"   ✅ Connected ({self.chroma_collection.count()} documents)")
        
        # Load LLM with aggressive speed optimizations
        print("   Loading LLM (speed-optimized)...")
        self.llm_engine = LLM(
            model=LLM_MODEL,
            dtype="float16",
            gpu_memory_utilization=0.95,  # Max GPU utilization
            max_model_len=2048,  # Reduced context for speed
            trust_remote_code=True,
            enforce_eager=True,
            enable_prefix_caching=True,
        )
        
        # Pre-warm the model with a dummy query
        print("   Pre-warming model...")
        from vllm import SamplingParams
        warmup_params = SamplingParams(temperature=0.1, max_tokens=10)
        self.llm_engine.generate(prompts=["Hello"], sampling_params=warmup_params)
        
        print("✅ Ultra-Fast RAG Service ready!")
    
    @modal.method()
    def query(self, question: str, top_k: int = 3, max_tokens: int = 256):
        """Ultra-fast query - target <3 seconds"""
        import time
        from langchain_core.documents import Document
        from vllm import SamplingParams
        
        start_time = time.time()
        
        # Fast retrieval - only top 2 docs
        retrieval_start = time.time()
        query_embedding = self.embeddings.embed_query(question)
        
        results = self.chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, 2)  # Max 2 docs for speed
        )
        retrieval_time = time.time() - retrieval_start
        
        # Build minimal context
        docs = []
        context_parts = []
        if results and 'documents' in results and results['documents']:
            for i, doc_text in enumerate(results['documents'][0][:2]):
                # Limit each doc to 400 chars
                truncated = doc_text[:400] if len(doc_text) > 400 else doc_text
                context_parts.append(truncated)
                metadata = results.get('metadatas', [[{}]])[0][i] if 'metadatas' in results else {}
                docs.append({"content": truncated, "metadata": metadata})
        
        if not context_parts:
            return {
                "answer": "No relevant information found.",
                "retrieval_time": retrieval_time,
                "generation_time": 0,
                "total_time": time.time() - start_time,
                "sources": [],
                "success": False
            }
        
        context = "\n".join(context_parts)
        
        # Minimal prompt for speed
        prompt = f"""<|system|>Answer concisely based on the context.<|end|>
<|user|>Context: {context}

Question: {question}<|end|>
<|assistant|>"""
        
        # Fast generation params
        sampling_params = SamplingParams(
            temperature=0.5,  # Lower temp = faster convergence
            max_tokens=max_tokens,
            top_p=0.85,
            stop=["<|end|>", "\n\n\n"]
        )
        
        gen_start = time.time()
        outputs = self.llm_engine.generate(prompts=[prompt], sampling_params=sampling_params)
        answer = outputs[0].outputs[0].text.strip()
        generation_time = time.time() - gen_start
        
        total_time = time.time() - start_time
        
        return {
            "answer": answer,
            "retrieval_time": round(retrieval_time, 3),
            "generation_time": round(generation_time, 3),
            "total_time": round(total_time, 3),
            "sources": docs,
            "success": True
        }

# FastAPI endpoint
@app.function(
    image=image,
    volumes={"/insurance-data": vol},
    min_containers=1,  # Keep warm!
)
@modal.concurrent(max_inputs=20)
@modal.asgi_app()
def fastapi_app():
    """Ultra-fast FastAPI endpoint"""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    
    class QueryRequest(BaseModel):
        question: str
        top_k: int = 2
        max_tokens: int = 256

    class QueryResponse(BaseModel):
        answer: str
        retrieval_time: float
        generation_time: float
        total_time: float
        sources: list
        success: bool
    
    web_app = FastAPI(title="Ultra-Fast RAG API", version="2.0.0")
    
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    rag_service = FastRAGService()
    
    @web_app.get("/health")
    async def health():
        return {"status": "healthy", "version": "2.0-fast"}
    
    @web_app.post("/query", response_model=QueryResponse)
    async def query_rag(request: QueryRequest):
        try:
            result = rag_service.query.remote(
                question=request.question,
                top_k=request.top_k,
                max_tokens=request.max_tokens
            )
            return QueryResponse(**result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.get("/")
    async def root():
        return {
            "service": "Ultra-Fast RAG API",
            "version": "2.0.0",
            "target": "<3 seconds",
            "optimizations": [
                "min_containers=1 (always warm)",
                "max 2 docs, 400 chars each",
                "max 256 tokens output",
                "aggressive GPU utilization"
            ]
        }
    
    return web_app
