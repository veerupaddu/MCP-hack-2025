"""
Dual RAG Query API - Queries both existing_products and product_design collections
Returns merged context from both sources for User Story Agent to use
"""

import modal

app = modal.App("insurance-rag-dual-query")
vol = modal.Volume.from_name("mcp-hack-ins-products", create_if_missing=True)

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch>=2.0.0", "transformers>=4.30.0", "sentence-transformers>=2.2.0",
        "huggingface_hub>=0.15.0", "langchain-community>=0.0.13",
        "chromadb>=0.4.0", "fastapi>=0.100.0", "uvicorn[standard]>=0.20.0",
    )
)

EXISTING_KW = ["existing", "current", "competitor", "metlife", "aig", "sonpo", "japan post", "market", "compare"]
DESIGN_KW = ["tokyodrive", "tokyo drive", "new product", "our product", "design", "pricing tier", "coverage", "feature"]


@app.cls(image=image, volumes={"/insurance-data": vol}, timeout=300, scaledown_window=300, max_containers=2, min_containers=0)
class DualRAGRetriever:
    """Retriever that queries both existing_products and product_design collections"""
    
    @modal.enter()
    def enter(self):
        from langchain_community.embeddings import HuggingFaceEmbeddings
        import chromadb
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL, 
            model_kwargs={'device': 'cpu'}, 
            encode_kwargs={'normalize_embeddings': True}
        )
        self.chroma_client = chromadb.PersistentClient(path="/insurance-data/chroma_db")
        self.collections = {}
        for name in ['existing_products', 'product_design', 'langchain']:
            try: 
                self.collections[name] = self.chroma_client.get_collection(name)
                print(f"Connected to {name}: {self.collections[name].count()} docs")
            except Exception as e: 
                print(f"Collection {name} not found: {e}")
    
    def _detect_source(self, question):
        q = question.lower()
        existing_score = sum(1 for kw in EXISTING_KW if kw in q)
        design_score = sum(1 for kw in DESIGN_KW if kw in q)
        if existing_score > design_score: 
            return "existing"
        elif design_score > existing_score: 
            return "design"
        return "both"
    
    def _query_collection(self, name, question, top_k=3):
        if name not in self.collections: 
            return []
        query_embedding = self.embeddings.embed_query(question)
        results = self.collections[name].query(
            query_embeddings=[query_embedding], 
            n_results=top_k
        )
        docs = []
        if results and results.get('documents') and results['documents']:
            for i, doc_text in enumerate(results['documents'][0]):
                meta = {}
                if results.get('metadatas') and results['metadatas'][0]:
                    meta = results['metadatas'][0][i]
                meta['collection'] = name
                docs.append({
                    "content": doc_text[:800],
                    "metadata": meta
                })
        return docs
    
    @modal.method()
    def retrieve(self, question, source="auto", top_k=3):
        """Retrieve relevant documents from one or both collections"""
        import time
        start = time.time()
        
        detected = source if source != "auto" else self._detect_source(question)
        all_docs = []
        sources_queried = []
        
        if detected in ["existing", "both"]:
            docs = self._query_collection("existing_products", question, top_k)
            if not docs:
                docs = self._query_collection("langchain", question, top_k)
            all_docs.extend(docs)
            sources_queried.append("existing_products")
        
        if detected in ["design", "both"]:
            docs = self._query_collection("product_design", question, top_k)
            all_docs.extend(docs)
            sources_queried.append("product_design")
        
        return {
            "documents": all_docs,
            "sources_queried": sources_queried,
            "detected_source": detected,
            "retrieval_time": time.time() - start,
            "success": len(all_docs) > 0
        }


# FastAPI Web Endpoint
@app.function(image=image, volumes={"/insurance-data": vol}, min_containers=0)
@modal.concurrent(max_inputs=10)
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List, Optional
    
    class RetrieveRequest(BaseModel):
        question: str
        source: str = "auto"  # "auto", "existing", "design", "both"
        top_k: int = 3
    
    class DocumentInfo(BaseModel):
        content: str
        metadata: dict
    
    class RetrieveResponse(BaseModel):
        documents: List[dict]
        sources_queried: List[str]
        detected_source: str
        retrieval_time: float
        success: bool
    
    web_app = FastAPI(title="Dual RAG Retriever API", version="1.0.0")
    
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    retriever = DualRAGRetriever()
    
    @web_app.get("/")
    async def root():
        return {
            "service": "Dual RAG Retriever API",
            "version": "1.0.0",
            "collections": ["existing_products", "product_design"],
            "endpoints": {
                "retrieve": "POST /retrieve",
                "health": "GET /health"
            }
        }
    
    @web_app.get("/health")
    async def health():
        return {"status": "healthy", "service": "dual-rag-retriever"}
    
    @web_app.post("/retrieve", response_model=RetrieveResponse)
    async def retrieve_docs(request: RetrieveRequest):
        try:
            result = retriever.retrieve.remote(
                question=request.question,
                source=request.source,
                top_k=request.top_k
            )
            return RetrieveResponse(**result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.post("/query/existing")
    async def query_existing(request: RetrieveRequest):
        request.source = "existing"
        return await retrieve_docs(request)
    
    @web_app.post("/query/design")
    async def query_design(request: RetrieveRequest):
        request.source = "design"
        return await retrieve_docs(request)
    
    @web_app.post("/query/both")
    async def query_both(request: RetrieveRequest):
        request.source = "both"
        return await retrieve_docs(request)
    
    return web_app


@app.local_entrypoint()
def test_retrieve(question: str = "What are the pricing tiers for TokyoDrive?"):
    """Test the dual retriever"""
    print(f"Question: {question}\n")
    
    retriever = DualRAGRetriever()
    result = retriever.retrieve.remote(question)
    
    print(f"Detected source: {result['detected_source']}")
    print(f"Sources queried: {result['sources_queried']}")
    print(f"Documents found: {len(result['documents'])}")
    print(f"Retrieval time: {result['retrieval_time']:.3f}s")
    
    for i, doc in enumerate(result['documents'], 1):
        print(f"\n--- Document {i} ---")
        print(f"Collection: {doc['metadata'].get('collection')}")
        print(f"Filename: {doc['metadata'].get('filename', doc['metadata'].get('source', 'Unknown'))}")
        print(f"Content: {doc['content'][:200]}...")
