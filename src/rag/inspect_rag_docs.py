import modal

app = modal.App("inspect-rag-docs")
vol = modal.Volume.from_name("mcp-hack-ins-products")

image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        "chromadb==0.5.20",
        "langchain==0.3.7",
        "langchain-community==0.3.7",
        "sentence-transformers==3.3.0",
        "torch==2.4.0",
        "transformers==4.46.3",
    )
)

@app.function(image=image, volumes={"/data": vol}, gpu="T4")
def inspect_docs():
    import chromadb
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    import os
    
    print("🔍 Inspecting ChromaDB at /data/chroma_db")
    
    # 1. Direct ChromaDB Inspection
    client = chromadb.PersistentClient(path="/data/chroma_db")
    try:
        coll = client.get_collection("langchain")
        count = coll.count()
        print(f"✅ Found collection 'langchain' with {count} documents")
        
        # Get a sample
        peek = coll.peek(limit=5)
        print("\n📄 Sample Documents (Direct Peek):")
        if peek['metadatas']:
            for i, meta in enumerate(peek['metadatas']):
                print(f"  [{i}] Source: {meta.get('source', 'Unknown')} | Page: {meta.get('page', '?')}")
                # print(f"      Content: {peek['documents'][i][:100]}...")
        
        # List unique sources
        print("\n📚 Unique Sources in DB:")
        # This might be slow for large DBs, but 3k is fine
        all_data = coll.get(include=['metadatas'])
        sources = set()
        for meta in all_data['metadatas']:
            if meta:
                sources.add(meta.get('source', 'Unknown'))
        
        for s in sorted(list(sources)):
            print(f"  - {s}")
            
    except Exception as e:
        print(f"❌ Error accessing collection directly: {e}")
        return

    # 2. Test Retrieval with LangChain & Embeddings
    print("\n🧪 Testing Retrieval with BAAI/bge-small-en-v1.5...")
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={'device': 'cuda'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        db = Chroma(
            client=client,
            collection_name="langchain",
            embedding_function=embeddings
        )
        
        query = "What insurance products are available?"
        print(f"\n❓ Query: '{query}'")
        
        docs = db.similarity_search(query, k=3)
        print(f"✅ Retrieved {len(docs)} documents:")
        for i, doc in enumerate(docs):
            print(f"  [{i}] Source: {doc.metadata.get('source')} | Score: N/A (similarity_search)")
            print(f"      Content: {doc.page_content[:150]}...")
            
    except Exception as e:
        print(f"❌ Error during retrieval test: {e}")

@app.local_entrypoint()
def main():
    inspect_docs.remote()
