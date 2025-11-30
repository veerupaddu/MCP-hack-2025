import modal

app = modal.App("rag-vllm-optimized")

# Volumes
vol_data = modal.Volume.from_name("mcp-hack-ins-products")
vol_checkpoints = modal.Volume.from_name("model-checkpoints")

# Image with vLLM and RAG dependencies
image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        "vllm==0.6.3",
        "torch==2.4.0",
        "transformers==4.46.3",
        "accelerate==0.33.0",
        "fastapi",
        "hf_transfer",
        "langchain==0.3.7",
        "langchain-community==0.3.7",
        "sentence-transformers==3.3.0",
        "chromadb==0.5.20",
        "pypdf==5.1.0",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

@app.cls(
    image=image,
    gpu="A10G",
    volumes={
        "/insurance-data": vol_data,
        "/data/checkpoints": vol_checkpoints
    },
    scaledown_window=300,
)
class RAGModel:
    @modal.enter()
    def load_resources(self):
        import os
        import time
        from vllm import LLM, SamplingParams
        from vllm.engine.arg_utils import EngineArgs
        from vllm.engine.async_llm_engine import AsyncLLMEngine
        from langchain_community.vectorstores import Chroma
        from langchain_community.embeddings import HuggingFaceEmbeddings
        
        print("🚀 Loading resources...")
        start_time = time.time()
        
        # 1. Load Embeddings (for retrieval)
        print("📚 Loading embedding model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={'device': 'cuda'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # 2. Load Vector DB (Local mode for speed)
        print("💾 Loading local ChromaDB...")
        # Check if chroma_db exists in volume
        db_path = "/insurance-data/chroma_db"
        if os.path.exists(db_path):
            self.vector_db = Chroma(
                persist_directory=db_path,
                embedding_function=self.embeddings,
                collection_name="langchain"
            )
            print(f"✅ Loaded ChromaDB from {db_path}")
        else:
            print(f"⚠️ Warning: ChromaDB not found at {db_path}")
            self.vector_db = None
            
        # 3. Load vLLM Engine
        print("🤖 Loading vLLM engine...")
        
        # Check if merged model exists (from fine-tuning task)
        model_path = "/data/checkpoints/merged_model"
        if not os.path.exists(model_path):
            print("⚠️ Merged model not found, falling back to base model")
            model_path = "microsoft/Phi-3-mini-4k-instruct"
        else:
            print(f"✅ Loading fine-tuned model from {model_path}")
            
        engine_args = EngineArgs(
            model=model_path,
            tensor_parallel_size=1,
            dtype="auto",
            gpu_memory_utilization=0.70, # Leave room for embedding model
            enforce_eager=False,
            trust_remote_code=True,
        )
        
        # Fix for vLLM 0.6.3 compatibility
        if not hasattr(engine_args, "disable_log_requests"):
            engine_args.disable_log_requests = False
            
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)
        
        self.sampling_params = SamplingParams(
            temperature=0.1,
            top_p=0.9,
            max_tokens=512,
            stop=["<|end|>"]
        )
        
        print(f"✅ All resources loaded in {time.time() - start_time:.2f}s")

    @modal.fastapi_endpoint(method="POST")
    async def query(self, data: dict):
        import uuid
        import time
        
        start_time = time.time()
        question = data.get('question', '')
        
        if not question:
            return {"error": "Question is required"}
            
        # 1. Retrieve Context
        retrieval_start = time.time()
        context = ""
        sources = []
        
        if self.vector_db:
            try:
                docs = self.vector_db.similarity_search(question, k=3)
                context = "\n\n".join([doc.page_content for doc in docs])
                sources = [{"content": doc.page_content[:200], "metadata": doc.metadata} for doc in docs]
            except Exception as e:
                print(f"Retrieval error: {e}")
                context = "No context available due to error."
        
        retrieval_time = time.time() - retrieval_start
        
        # 2. Generate Answer
        prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
You are a helpful insurance assistant. Answer the question based ONLY on the provided context.

### Input:
Context:
{context}

Question:
{question}

### Response:
"""
        
        request_id = str(uuid.uuid4())
        results_generator = self.engine.generate(prompt, self.sampling_params, request_id)
        
        final_output = None
        async for request_output in results_generator:
            final_output = request_output
            
        text_output = final_output.outputs[0].text.strip()
        
        # Clean up response
        if "### Response:\n" in text_output:
            answer = text_output.split("### Response:\n")[1].strip()
        else:
            answer = text_output
            
        total_time = time.time() - start_time
        
        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "metrics": {
                "retrieval_ms": round(retrieval_time * 1000, 2),
                "total_latency_ms": round(total_time * 1000, 2)
            }
        }
