import modal

app = modal.App("phi3-inference-vllm")

vol_checkpoints = modal.Volume.from_name("model-checkpoints")

# vLLM image
image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        "vllm==0.6.3",
        "torch==2.4.0",
        "transformers==4.46.3",
        "accelerate==0.33.0",
        "fastapi",
        "hf_transfer",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

@app.cls(
    image=image,
    gpu="A10G",
    volumes={"/data/checkpoints": vol_checkpoints},
    scaledown_window=300,
)
class Model:
    @modal.enter()
    def load_model(self):
        from vllm import LLM, SamplingParams
        from vllm.engine.arg_utils import EngineArgs
        from vllm.engine.async_llm_engine import AsyncLLMEngine
        
        print("🚀 Loading vLLM engine...")
        
        # Check if merged model exists, otherwise use base model
        import os
        model_path = "/data/checkpoints/merged_model"
        if not os.path.exists(model_path):
            print("⚠️ Merged model not found, falling back to base model (no fine-tuning)")
            model_path = "microsoft/Phi-3-mini-4k-instruct"
        else:
            print(f"✅ Loading fine-tuned model from {model_path}")
            
        engine_args = EngineArgs(
            model=model_path,
            tensor_parallel_size=1,
            dtype="auto",
            gpu_memory_utilization=0.90,
            enforce_eager=False,
            trust_remote_code=True,
        )
        
        # Manually set disable_log_requests on the engine args object if needed, 
        # or just let AsyncLLMEngine handle defaults.
        # The issue is that AsyncLLMEngine.from_engine_args tries to access it from engine_args
        # but it's not in the __init__. We can monkey-patch it or use a different init method.
        
        # Fix: vLLM 0.6.3 compatibility
        if not hasattr(engine_args, "disable_log_requests"):
            engine_args.disable_log_requests = False
            
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)
        print("✅ vLLM engine loaded!")
        
        # Default sampling params
        self.sampling_params = SamplingParams(
            temperature=0.1,
            top_p=0.9,
            max_tokens=256,
            stop=["<|end|>"]
        )

    @modal.fastapi_endpoint(method="POST")
    async def ask(self, data: dict):
        import uuid
        import time
        
        start_time = time.time()
        
        question = data.get('question', '')
        context = data.get('context', 'Context: Japan Census data.')
        
        prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{question}

### Input:
{context}

### Response:
"""
        
        request_id = str(uuid.uuid4())
        results_generator = self.engine.generate(prompt, self.sampling_params, request_id)
        
        # Stream results (but we'll just wait for the final one for this API)
        final_output = None
        async for request_output in results_generator:
            final_output = request_output
            
        text_output = final_output.outputs[0].text.strip()
        
        # Clean up response
        if "### Response:\n" in text_output:
            answer = text_output.split("### Response:\n")[1].strip()
        else:
            answer = text_output
            
        latency = time.time() - start_time
        
        return {
            "answer": answer,
            "latency_ms": round(latency * 1000, 2),
            "model": "phi-3-mini-ft-vllm"
        }
