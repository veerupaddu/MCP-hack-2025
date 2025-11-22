import modal

app = modal.App("insurance-rag")

# Reference your specific volume
vol = modal.Volume.from_name("mcp-hack-ins-products", create_if_missing=True)

# Model configuration
LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# Build image with ALL required dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "langchain==0.3.7",
        "langchain-community==0.3.7",
        "langchain-text-splitters==0.3.2",
        "sentence-transformers==3.3.0",
        "chromadb==0.5.20",
        "pypdf==5.1.0",
        "cryptography==43.0.3",
        "transformers==4.46.2",
        "torch==2.5.1",
        "accelerate==1.1.1",
        "huggingface_hub==0.26.2",
        "sentencepiece==0.2.0",  # Added for tokenizer
        "protobuf==5.29.2"  # Required by sentencepiece
    )
)

@app.function(image=image, volumes={"/insurance-data": vol})
def list_files():
    """List all files in the volume"""
    import os
    files = []
    for root, dirs, filenames in os.walk("/insurance-data"):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            files.append(full_path)
    return files

@app.function(
    image=image,
    volumes={"/insurance-data": vol},
    gpu="T4",
    timeout=900
)
def create_vector_db():
    """Create vector database from insurance PDFs"""
    from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    print("🔍 Loading documents from /insurance-data...")
    
    loader = DirectoryLoader(
        "/insurance-data",
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        silent_errors=True
    )
    
    try:
        documents = loader.load()
    except Exception as e:
        print(f"⚠️ Warning during loading: {e}")
        documents = []
    
    print(f"📄 Loaded {len(documents)} document pages")
    
    if len(documents) == 0:
        return {
            "status": "error",
            "message": "No PDF files could be loaded",
            "total_documents": 0,
            "total_chunks": 0
        }
    
    print("✂️ Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    print(f"📦 Created {len(chunks)} chunks")
    
    print("🧠 Creating embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cuda'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    print("💾 Building vector database...")
    
    # Connect to remote Chroma service
    chroma_service = modal.Cls.from_name("chroma-server-v2", "ChromaDB")()
    
    # Prepare data for upsert
    ids = [f"id_{i}" for i in range(len(chunks))]
    documents = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]
    
    # Generate embeddings locally
    print("   Generating embeddings locally...")
    embeddings_list = embeddings.embed_documents(documents)
    
    # Upsert to remote Chroma
    print("   Upserting to remote Chroma DB...")
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_embs = embeddings_list[i:i+batch_size]
        
        chroma_service.upsert.remote(
            collection_name="insurance_products",
            ids=batch_ids,
            documents=batch_docs,
            embeddings=batch_embs,
            metadatas=batch_metas
        )
        print(f"   Upserted batch {i//batch_size + 1}/{(len(ids)-1)//batch_size + 1}")

    print("✅ Vector database created and persisted remotely!")
    
    return {
        "status": "success",
        "total_documents": len(documents),
        "total_chunks": len(chunks)
    }

@app.cls(
    image=image,
    volumes={"/insurance-data": vol},
    gpu="A10G",
    timeout=600,
    concurrency_limit=1,  # Keep one container alive
    keep_warm=1          # Keep one container warm
)
class RAGModel:
    @modal.enter()
    def enter(self):
        from langchain_community.vectorstores import Chroma
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.llms import HuggingFacePipeline
        from langchain.chains import RetrievalQA
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        import torch
        from typing import Any, List
        from langchain_core.retrievers import BaseRetriever
        from langchain_core.documents import Document

        print("🔄 Loading embeddings...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cuda'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        print("📚 Connecting to remote Chroma DB...")
        self.chroma_service = modal.Cls.from_name("chroma-server-v2", "ChromaDB")()
        
        class RemoteChromaRetriever(BaseRetriever):
            chroma_service: Any
            embeddings: Any
            k: int = 3
            
            def _get_relevant_documents(self, query: str) -> List[Document]:
                query_embedding = self.embeddings.embed_query(query)
                results = self.chroma_service.query.remote(
                    collection_name="insurance_products",
                    query_embeddings=[query_embedding],
                    n_results=self.k
                )
                
                documents = []
                if results['documents']:
                    for i in range(len(results['documents'][0])):
                        doc = Document(
                            page_content=results['documents'][0][i],
                            metadata=results['metadatas'][0][i] if results['metadatas'] else {}
                        )
                        documents.append(doc)
                return documents
                
            async def _aget_relevant_documents(self, query: str) -> List[Document]:
                return self._get_relevant_documents(query)

        self.RemoteChromaRetriever = RemoteChromaRetriever

        print("🤖 Loading LLM model...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            LLM_MODEL,
            use_fast=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            LLM_MODEL,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=512,
            temperature=0.1,
            do_sample=True
        )
        
        self.llm = HuggingFacePipeline(pipeline=pipe)
        print("✅ Model loaded and ready!")

    @modal.method()
    def query(self, question: str, top_k: int = 3):
        from langchain.chains import RetrievalQA
        
        print(f"❓ Query: {question}")
        
        retriever = self.RemoteChromaRetriever(
            chroma_service=self.chroma_service,
            embeddings=self.embeddings,
            k=top_k
        )
        
        print("⚙️ Creating RAG chain...")
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        print("🔎 Searching and generating answer...")
        result = qa_chain.invoke({"query": question})
        
        return {
            "question": question,
            "answer": result["result"],
            "sources": [
                {
                    "content": doc.page_content[:300],
                    "metadata": doc.metadata
                }
                for doc in result["source_documents"]
            ]
        }

    @modal.web_endpoint(method="GET")
    def web_query(self, question: str):
        return self.query.local(question)

@app.local_entrypoint()
def list():
    """List files in volume"""
    print("📁 Listing files in mcp-hack-ins-products volume...")
    files = list_files.remote()
    print(f"\n✅ Found {len(files)} files:")
    for f in files:
        print(f"  📄 {f}")

@app.local_entrypoint()
def index():
    """Create vector database"""
    print("🚀 Starting vector database creation...")
    result = create_vector_db.remote()
    print(f"\n{'='*60}")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Documents processed: {result['total_documents']}")
        print(f"Text chunks created: {result['total_chunks']}")
        print("✅ Vector database is ready for queries!")
    else:
        print(f"❌ Error: {result['message']}")
    print(f"{'='*60}")

@app.local_entrypoint()
def query(question: str = "What insurance products are available?"):
    """Query the RAG system"""
    print(f"🤔 Question: {question}\n")
    
    # Lookup the deployed RAGModel from the insurance-rag app
    # This connects to the persistent container instead of creating a new one
    model = modal.Cls.from_name("insurance-rag", "RAGModel")()
    result = model.query.remote(question)
    
    print(f"{'='*60}")
    print(f"💡 Answer:\n{result['answer']}")
    print(f"\n{'='*60}")
    print(f"📖 Sources ({len(result['sources'])}):")
    for i, source in enumerate(result['sources'], 1):
        print(f"\n  [{i}] {source['metadata'].get('source', 'Unknown')}")
        print(f"      Page: {source['metadata'].get('page', 'N/A')}")
        print(f"      Preview: {source['content'][:150]}...")
    print(f"{'='*60}")
