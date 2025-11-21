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
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="/insurance-data/chroma_db"
    )
    
    vol.commit()
    print("✅ Vector database created and persisted!")
    
    return {
        "status": "success",
        "total_documents": len(documents),
        "total_chunks": len(chunks)
    }

@app.function(
    image=image,
    volumes={"/insurance-data": vol},
    gpu="A10G",
    timeout=600
)
def query_insurance_rag(question: str, top_k: int = 3):
    """Query the insurance RAG system"""
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.llms import HuggingFacePipeline
    from langchain.chains import RetrievalQA
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    import torch
    
    print(f"❓ Query: {question}")
    
    print("🔄 Loading embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cuda'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    print("📚 Loading vector database...")
    vectordb = Chroma(
        persist_directory="/insurance-data/chroma_db",
        embedding_function=embeddings
    )
    
    print("🤖 Loading LLM model...")
    tokenizer = AutoTokenizer.from_pretrained(
        LLM_MODEL,
        use_fast=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        LLM_MODEL,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=512,
        temperature=0.1,
        do_sample=True
    )
    
    llm = HuggingFacePipeline(pipeline=pipe)
    
    print("⚙️ Creating RAG chain...")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectordb.as_retriever(search_kwargs={"k": top_k}),
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
    result = query_insurance_rag.remote(question)
    print(f"{'='*60}")
    print(f"💡 Answer:\n{result['answer']}")
    print(f"\n{'='*60}")
    print(f"📖 Sources ({len(result['sources'])}):")
    for i, source in enumerate(result['sources'], 1):
        print(f"\n  [{i}] {source['metadata'].get('source', 'Unknown')}")
        print(f"      Page: {source['metadata'].get('page', 'N/A')}")
        print(f"      Preview: {source['content'][:150]}...")
    print(f"{'='*60}")
