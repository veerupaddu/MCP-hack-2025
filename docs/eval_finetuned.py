import modal

app = modal.App("eval-finetuned-census")

# Volumes
vol_checkpoints = modal.Volume.from_name("model-checkpoints")

# Image: Same as training to ensure compatibility
image = modal.Image.from_registry("nvidia/cuda:12.1.1-devel-ubuntu22.04", add_python="3.10") \
    .apt_install("git") \
    .run_commands(
        "pip install --upgrade pip",
        "pip install packaging ninja psutil",
        "pip install unsloth_zoo",  # This will install compatible torch/torchvision
        "pip install torchvision",  # Ensure torchvision is installed
        # Skip flash-attn - it causes OOM during build and is optional
        "pip install xformers trl peft accelerate bitsandbytes wandb scipy huggingface_hub protobuf sentencepiece einops",
        "pip install --no-deps 'unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git'"
    ) \
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})

@app.function(
    image=image,
    volumes={"/data/checkpoints": vol_checkpoints},
    gpu="A10G", # Inference can run on smaller GPU
    timeout=600
)
def evaluate_model(questions: list):
    from unsloth import FastLanguageModel
    import torch
    
    print("🚀 Loading Fine-tuned Model...")
    
    max_seq_length = 2048
    dtype = None
    load_in_4bit = True
    
    # Load model + adapter
    # Note: We saved to /data/checkpoints/phi3-census-lora
    model_path = "/data/checkpoints/phi3-census-lora"
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_path, # Load from local path (volume)
        max_seq_length=max_seq_length,
        dtype=dtype,
        load_in_4bit=load_in_4bit,
    )
    FastLanguageModel.for_inference(model)
    
    print("✅ Model Loaded. Running Inference...")
    
    results = []
    
    alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
"""
    
    for q in questions:
        instruction = q["question"]
        input_context = q.get("context", "")
        
        inputs = tokenizer(
            [alpaca_prompt.format(instruction, input_context)], 
            return_tensors="pt"
        ).to("cuda")
        
        outputs = model.generate(**inputs, max_new_tokens=128, use_cache=True)
        response = tokenizer.batch_decode(outputs)
        
        # Extract response part
        full_text = response[0]
        # Simple parsing
        if "### Response:\n" in full_text:
            answer = full_text.split("### Response:\n")[1].split("<|endoftext|>")[0]
        else:
            answer = full_text
            
        results.append({
            "question": instruction,
            "answer": answer.strip()
        })
        
    return results

@app.local_entrypoint()
def main():
    questions = [
        {
            "question": "What is the population of Tokyo?",
            "context": "Context: Japan Census data."
        },
        {
            "question": "What is the average income in Osaka?",
            "context": "Context: Japan Economy & Labor data."
        },
        {
             "question": "How many households are in Hokkaido?",
             "context": "Context: Japan Census data."
        }
    ]
    
    answers = evaluate_model.remote(questions)
    
    for item in answers:
        print(f"\nQ: {item['question']}")
        print(f"A: {item['answer']}")
