import modal

app = modal.App("eval-finetuned")

vol_checkpoints = modal.Volume.from_name("model-checkpoints")

image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        "torch==2.4.0",
        "transformers==4.44.2",
        "peft==0.12.0",
        "bitsandbytes==0.43.3",
        "accelerate==0.33.0",
    )
)

@app.function(
    image=image,
    gpu="A10G",
    volumes={"/data/checkpoints": vol_checkpoints}
)
def evaluate():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import PeftModel
    
    print("📦 Loading fine-tuned model...")
    
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
    model = PeftModel.from_pretrained(base_model, "/data/checkpoints/final_model")
    
    tokenizer = AutoTokenizer.from_pretrained(
        "/data/checkpoints/final_model",
        trust_remote_code=True,
    )
    
    # Test questions
    test_cases = [
        {
            "question": "What is the population of Tokyo?",
            "context": "Japan Census data"
        },
        {
            "question": "What is the population of Hokkaido?",
            "context": "Japan Census data"
        },
        {
            "question": "What is the Members per private household for Sapporo-shi?",
            "context": "Japan Census data"
        }
    ]
    
    print("\n" + "="*80)
    print("🧪 EVALUATION RESULTS")
    print("="*80 + "\n")
    
    for i, test in enumerate(test_cases, 1):
        prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{test['question']}

### Input:
Context: {test['context']}.

### Response:
"""
        
        inputs = tokenizer([prompt], return_tensors="pt").to("cuda")
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.1,
            do_sample=True,
            top_p=0.9,
        )
        response = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
        
        # Extract answer
        if "### Response:\n" in response:
            answer = response.split("### Response:\n")[1].strip()
        else:
            answer = response
        
        print(f"Q{i}: {test['question']}")
        print(f"A{i}: {answer}")
        print("-" * 80 + "\n")

@app.local_entrypoint()
def main():
    evaluate.remote()
