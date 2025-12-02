"""
Open Source LLM Inference API on Modal
Optimized for fast responses (<3 seconds)
"""

import modal

app = modal.App("llm-inference-api")

# Model options - uncomment the one you want
MODEL_ID = "microsoft/Phi-3-mini-4k-instruct"  # Fast, good quality
# MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.3"  # Great instruction following
# MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"  # Very fast
# MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"  # Good for coding

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "vllm>=0.4.0",
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.20.0",
    )
)

@app.cls(
    image=image,
    gpu="A10G",
    timeout=300,
    scaledown_window=600,  # Keep warm for 10 minutes
    max_containers=2,
)
class LLMService:
    """Fast LLM inference service using vLLM"""
    
    @modal.enter()
    def load_model(self):
        from vllm import LLM, SamplingParams
        
        print(f"🚀 Loading model: {MODEL_ID}")
        self.llm = LLM(
            model=MODEL_ID,
            dtype="float16",
            gpu_memory_utilization=0.9,
            max_model_len=4096,
            trust_remote_code=True,
            enforce_eager=True,
        )
        
        # Pre-warm
        warmup = SamplingParams(max_tokens=10, temperature=0.1)
        self.llm.generate(["Hello"], warmup)
        print("✅ Model ready!")
    
    @modal.method()
    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7) -> dict:
        """Generate text from prompt"""
        import time
        from vllm import SamplingParams
        
        start = time.time()
        
        params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
            stop=["<|end|>", "</s>", "[/INST]"]
        )
        
        outputs = self.llm.generate([prompt], params)
        text = outputs[0].outputs[0].text.strip()
        
        return {
            "text": text,
            "model": MODEL_ID,
            "latency_ms": round((time.time() - start) * 1000, 2)
        }


# FastAPI Web Endpoint
@app.function(image=image)
@modal.concurrent(max_inputs=20)
@modal.asgi_app()
def fastapi_app():
    """FastAPI endpoint for LLM inference"""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    
    class GenerateRequest(BaseModel):
        prompt: str
        max_tokens: int = 256
        temperature: float = 0.7
        system_prompt: str = None
    
    class ChatRequest(BaseModel):
        message: str
        system_prompt: str = "You are a helpful AI assistant."
        max_tokens: int = 256
    
    class GenerateResponse(BaseModel):
        text: str
        model: str
        latency_ms: float
    
    web_app = FastAPI(title="LLM Inference API", version="1.0.0")
    
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    llm_service = LLMService()
    
    @web_app.get("/health")
    async def health():
        return {"status": "healthy", "model": MODEL_ID}
    
    @web_app.post("/generate", response_model=GenerateResponse)
    async def generate(request: GenerateRequest):
        """Generate text from a prompt"""
        try:
            # Build prompt with optional system prompt
            if request.system_prompt:
                full_prompt = f"<|system|>{request.system_prompt}<|end|>\n<|user|>{request.prompt}<|end|>\n<|assistant|>"
            else:
                full_prompt = request.prompt
            
            result = llm_service.generate.remote(
                prompt=full_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            return GenerateResponse(**result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.post("/chat", response_model=GenerateResponse)
    async def chat(request: ChatRequest):
        """Chat-style interaction"""
        try:
            prompt = f"<|system|>{request.system_prompt}<|end|>\n<|user|>{request.message}<|end|>\n<|assistant|>"
            
            result = llm_service.generate.remote(
                prompt=prompt,
                max_tokens=request.max_tokens,
                temperature=0.7
            )
            return GenerateResponse(**result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @web_app.get("/")
    async def root():
        return {
            "service": "LLM Inference API",
            "model": MODEL_ID,
            "endpoints": {
                "health": "GET /health",
                "generate": "POST /generate",
                "chat": "POST /chat"
            }
        }
    
    return web_app


# CLI for testing
@app.local_entrypoint()
def main(prompt: str = "What is the capital of France?"):
    """Test the LLM locally"""
    service = LLMService()
    result = service.generate.remote(prompt)
    print(f"\n📝 Prompt: {prompt}")
    print(f"🤖 Response: {result['text']}")
    print(f"⏱️  Latency: {result['latency_ms']}ms")
