import modal

app = modal.App("phi3-inference-gpu")

vol_checkpoints = modal.Volume.from_name("model-checkpoints")

image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        "torch==2.4.0",
        "transformers==4.44.2",
        "peft==0.12.0",
        "bitsandbytes==0.43.3",
        "accelerate==0.33.0",
        "fastapi",
    )
)

@app.cls(
    image=image,
    gpu="A10G",
    volumes={"/data/checkpoints": vol_checkpoints},
    container_idle_timeout=300,
)
class Model:
    @modal.enter()
    def load_model(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import PeftModel
        
        print("Loading fine-tuned model...")
        
        # Load base model with 4-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        
        base_model = AutoModelForCausalLM.from_pretrained(
            "microsoft/Phi-3-mini-4k-instruct",
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        
        # Load fine-tuned LoRA weights
        self.model = PeftModel.from_pretrained(base_model, "/data/checkpoints/final_model")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            "/data/checkpoints/final_model",
            trust_remote_code=True,
        )
        
        print("Model loaded successfully!")
    
    @modal.web_endpoint(method="POST")
    def ask(self, data: dict):
        try:
            prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{data.get('question', '')}

### Input:
{data.get('context', 'Context: Japan Census data.')}

### Response:
"""
            inputs = self.tokenizer([prompt], return_tensors="pt").to("cuda")
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=150,
                temperature=0.1,
                do_sample=True,
                top_p=0.9,
            )
            response = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
            
            if "### Response:\n" in response:
                answer = response.split("### Response:\n")[1].strip()
            else:
                answer = response
            
            return {"answer": answer}
        except Exception as e:
            return {"error": str(e)}
