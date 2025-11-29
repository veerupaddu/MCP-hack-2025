import modal

app = modal.App("census-qa-api")
vol_checkpoints = modal.Volume.from_name("model-checkpoints")

image = modal.Image.from_registry("nvidia/cuda:12.1.1-devel-ubuntu22.04", add_python="3.10") \
    .apt_install("git") \
    .run_commands(
        "pip install --upgrade pip",
        "pip install --upgrade pip packaging ninja psutil unsloth_zoo torchvision fastapi",
        "pip install xformers trl peft accelerate bitsandbytes scipy huggingface_hub protobuf sentencepiece einops",
        "pip install --no-deps 'unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git'"
    ) \
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})

@app.cls(image=image, volumes={"/data/checkpoints": vol_checkpoints}, gpu="A10G", keep_warm=1)
class Model:
    @modal.enter()
    def load(self):
        from unsloth import FastLanguageModel
        print("Loading model...")
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            "/data/checkpoints/phi3-census-lora",
            max_seq_length=2048,
            dtype=None,
            load_in_4bit=True,
        )
        FastLanguageModel.for_inference(self.model)
        print("Model loaded!")
    
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
            outputs = self.model.generate(**inputs, max_new_tokens=150, temperature=0.1, use_cache=True)
            response = self.tokenizer.batch_decode(outputs)[0]
            
            if "### Response:\n" in response:
                answer = response.split("### Response:\n")[1].split("<|endoftext|>")[0].strip()
            else:
                answer = response.strip()
                
            return {"question": data.get('question'), "answer": answer}
        except Exception as e:
            print(f"Error: {str(e)}")
            return {"error": str(e)}

@app.local_entrypoint()
def main():
    print("To deploy: modal deploy docs/api_endpoint.py")
