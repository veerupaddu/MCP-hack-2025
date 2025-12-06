"""
RAG Indexing for Existing Insurance Products
Indexes all PDF documents from insurance company folders into 'existing_products' collection.

Folders indexed:
- /insurance-data/aig/
- /insurance-data/metlife/
- /insurance-data/sonpo/
- /insurance-data/japan_post/
"""

import modal

app = modal.App("insurance-rag-existing-products")

# Reference the volume
vol = modal.Volume.from_name("mcp-hack-ins-products", create_if_missing=True)

# Model configuration
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# Source folders to index
SOURCE_FOLDERS = [
    "/insurance-data/aig",
    "/insurance-data/metlife", 
    "/insurance-data/sonpo",
    "/insurance-data/japan_post"
]

# Build image
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "sentence-transformers>=2.2.0",
        "huggingface_hub>=0.15.0",
        "langchain>=0.1.0",
        "langchain-community>=0.0.13",
        "langchain-text-splitters>=0.2.0",
        "langchain-core>=0.1.0",
        "langchain-huggingface>=0.0.3",  # New HuggingFace integration
        "chromadb>=0.4.0",
        "pypdf>=4.0.0",
        "cryptography>=3.1",  # For AES-encrypted PDFs
    )
)


@app.function(image=image, volumes={"/insurance-data": vol})
def list_existing_product_files():
    """List all PDF files from insurance company folders"""
    import os
    
    print("🔍 Scanning existing insurance product folders...")
    all_files = []
    
    for folder in SOURCE_FOLDERS:
        if os.path.exists(folder):
            print(f"\n📁 {folder}:")
            for file in os.listdir(folder):
                if file.endswith('.pdf'):
                    full_path = os.path.join(folder, file)
                    all_files.append(full_path)
                    print(f"  📄 {file}")
        else:
            print(f"  ⚠️ Folder not found: {folder}")
    
    print(f"\n✅ Found {len(all_files)} PDF files total")
    return all_files


@app.function(image=image, volumes={"/insurance-data": vol}, timeout=600)
def load_existing_products():
    """Load all existing insurance product PDFs"""
    import os
    from pypdf import PdfReader
    
    documents = []
    
    print("📚 Loading existing insurance product PDFs...")
    
    for folder in SOURCE_FOLDERS:
        if not os.path.exists(folder):
            print(f"  ⚠️ Skipping non-existent folder: {folder}")
            continue
            
        # Extract company name from folder
        company = os.path.basename(folder)
        print(f"\n📁 Processing {company}/")
        
        for file in os.listdir(folder):
            if not file.endswith('.pdf'):
                continue
                
            full_path = os.path.join(folder, file)
            
            try:
                reader = PdfReader(full_path)
                text_content = []
                
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
                
                full_text = '\n'.join(text_content)
                
                if not full_text.strip():
                    print(f"  ⚠️ No text extracted: {file}")
                    continue
                
                documents.append({
                    'page_content': full_text,
                    'metadata': {
                        'source': full_path,
                        'filename': file,
                        'company': company,
                        'type': 'existing_product',
                        'format': 'pdf'
                    }
                })
                print(f"  ✅ {file} ({len(full_text):,} chars)")
                
            except Exception as e:
                print(f"  ❌ Error loading {file}: {e}")
    
    print(f"\n✅ Loaded {len(documents)} documents total")
    return documents


@app.function(
    image=image,
    volumes={"/insurance-data": vol},
    gpu="T4",
    timeout=1800
)
def index_existing_products():
    """Create vector index for existing insurance products"""
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    import chromadb
    
    print("🚀 Indexing existing insurance products...")
    
    # Load documents
    documents = load_existing_products.remote()
    
    if not documents:
        return {
            "status": "error",
            "message": "No documents found to index",
            "total_documents": 0,
            "total_chunks": 0
        }
    
    # Split into chunks
    print("\n✂️ Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    langchain_docs = [
        Document(page_content=doc['page_content'], metadata=doc['metadata'])
        for doc in documents
    ]
    
    chunks = text_splitter.split_documents(langchain_docs)
    print(f"📦 Created {len(chunks)} chunks")
    
    # Create embeddings
    print("\n🧠 Creating embeddings...")
    import torch
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"   Using device: {device}")
    
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': device},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Store in ChromaDB
    print("\n💾 Storing in ChromaDB (existing_products collection)...")
    chroma_client = chromadb.PersistentClient(path="/insurance-data/chroma_db")
    
    # Delete existing collection if exists
    try:
        chroma_client.delete_collection("existing_products")
        print("   Deleted old collection")
    except:
        pass
    
    collection = chroma_client.create_collection(
        name="existing_products",
        metadata={"description": "Existing insurance product PDFs from various companies"}
    )
    
    # Generate embeddings and upsert
    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        
        ids = [f"existing_{i+j}" for j in range(len(batch))]
        documents_text = [chunk.page_content for chunk in batch]
        metadatas = [chunk.metadata for chunk in batch]
        embeddings_list = embeddings.embed_documents(documents_text)
        
        collection.add(
            ids=ids,
            documents=documents_text,
            embeddings=embeddings_list,
            metadatas=metadatas
        )
        print(f"   Batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} complete")
    
    # Commit to volume
    vol.commit()
    
    print("\n✅ Indexing complete!")
    
    return {
        "status": "success",
        "collection": "existing_products",
        "total_documents": len(documents),
        "total_chunks": len(chunks),
        "companies": list(set(doc['metadata']['company'] for doc in documents))
    }


@app.local_entrypoint()
def main():
    """Run the indexing process"""
    print("=" * 60)
    print("Existing Insurance Products Indexer")
    print("=" * 60)
    
    # First list files
    print("\n📋 Checking available files...")
    files = list_existing_product_files.remote()
    
    if not files:
        print("\n❌ No PDF files found in source folders!")
        print("   Make sure files are uploaded to the volume:")
        for folder in SOURCE_FOLDERS:
            print(f"   - {folder}")
        return
    
    # Index documents
    print("\n🚀 Starting indexing...")
    result = index_existing_products.remote()
    
    print("\n" + "=" * 60)
    print("Result:")
    print(f"  Status: {result['status']}")
    if result['status'] == 'success':
        print(f"  Documents indexed: {result['total_documents']}")
        print(f"  Chunks created: {result['total_chunks']}")
        print(f"  Companies: {', '.join(result['companies'])}")
    else:
        print(f"  Error: {result.get('message', 'Unknown error')}")
    print("=" * 60)
