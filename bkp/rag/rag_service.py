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
LLM_MODEL = os.getenv("LLM_MODEL", "microsoft/Phi-3-mini-4k-instruct")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "/data/chroma")
DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", "/data/documents")

# Global variables for models (loaded at startup)
embeddings = None
llm_engine = None
sampling_params = None
collection = None

def initialize_models():
    """Initialize models at startup"""
    global embeddings, llm_engine, sampling_params, collection
    
    print("🚀 Initializing RAG service...")
    
    # Initialize embeddings
    print("   Loading embeddings model...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cuda'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Initialize LLM
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
    print("   Connecting to ChromaDB...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    collection = chroma_client.get_or_create_collection("product_design")
    
    print("✅ RAG service ready!")

# Initialize on startup
initialize_models()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "llm_model": LLM_MODEL,
        "embedding_model": EMBEDDING_MODEL
    }), 200

@app.route('/query', methods=['POST'])
def query():
    """Query the RAG system"""
    data = request.json
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({"error": "Question is required"}), 400
    
    start_time = time.time()
    
    try:
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
                "answer": "No relevant information found in the product design document.",
                "retrieval_time": retrieval_time,
                "generation_time": 0,
                "sources": []
            })
        
        # Build context
        context = "\n\n".join(results['documents'][0])
        
        # Generate prompt
        prompt = f"""<|system|>
You are a helpful AI assistant that answers questions about the TokyoDrive Insurance product design document. 
Provide comprehensive, detailed answers with specific information from the document.
Structure your answer clearly with specific numbers, percentages, and data points.
Be thorough and cite specific details from the context. If information is not available, say so clearly.<|end|>
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
            "sources": sources,
            "success": True
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8000))
    app.run(host='0.0.0.0', port=port, debug=False)

