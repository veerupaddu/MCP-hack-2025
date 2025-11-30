import modal

app = modal.App("census-qa-api-cpu")
vol_checkpoints = modal.Volume.from_name("model-checkpoints")

# CPU-only image (no CUDA)
image = modal.Image.debian_slim(python_version="3.10") \
    .pip_install(
        "torch",
        "transformers",
        "peft",
        "accelerate",
        "bitsandbytes",
        "scipy",
        "huggingface_hub",
        "protobuf",
        "sentencepiece",
        "fastapi"
    )

@app.cls(
    image=image,
    volumes={"/data/checkpoints": vol_checkpoints},
    cpu=4,  # Use CPU instead of GPU
    memory=8192,  # 8GB RAM
    keep_warm=1
)
class ModelCPU:
    @modal.enter()
    def load(self):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        
        print("Loading model on CPU...")
        
        # Load base model
        base_model = "microsoft/Phi-3-mini-4k-instruct"
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        
        # Load with PEFT adapter (no quantization on CPU)
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype="auto",
            device_map="cpu"
        )
        
        # Load LoRA adapter
        self.model = PeftModel.from_pretrained(
            model,
            "/data/checkpoints/phi3-census-lora"
        )
        
        print("Model loaded on CPU!")
    
    @modal.web_endpoint(method="POST")
    def ask(self, data: dict):
        prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{data.get('question', '')}

### Input:
{data.get('context', 'Context: Japan Census data.')}

### Response:
"""
        
        inputs = self.tokenizer([prompt], return_tensors="pt")
        outputs = self.model.generate(**inputs, max_new_tokens=150, temperature=0.1)
        response = self.tokenizer.batch_decode(outputs)[0]
        
        if "### Response:\n" in response:
            answer = response.split("### Response:\n")[1].split("<|endoftext|>")[0].strip()
        else:
            answer = response.strip()
        
        return {"question": data.get('question'), "answer": answer}

@app.local_entrypoint()
def main():
    print("CPU-based API endpoint")
    print("Deploy with: modal deploy docs/api_endpoint_cpu.py")
    print("Note: CPU inference is 10-20x slower than GPU")
