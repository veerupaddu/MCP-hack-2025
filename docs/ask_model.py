import modal

app = modal.App("ask-finetuned-model")

vol_checkpoints = modal.Volume.from_name("model-checkpoints")

image = modal.Image.from_registry("nvidia/cuda:12.1.1-devel-ubuntu22.04", add_python="3.10") \
    .apt_install("git") \
    .run_commands(
        "pip install --upgrade pip",
        "pip install packaging ninja psutil",
        "pip install unsloth_zoo",
        "pip install torchvision",
        "pip install xformers trl peft accelerate bitsandbytes scipy huggingface_hub protobuf sentencepiece einops",
        "pip install --no-deps 'unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git'"
    ) \
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})

@app.function(
    image=image,
    volumes={"/data/checkpoints": vol_checkpoints},
    gpu="A10G",
    timeout=600
)
def ask_question(question: str, context: str = "Context: Japan Census data."):
    from unsloth import FastLanguageModel
    
    print(f"Loading model...")
    
    model_path = "/data/checkpoints/phi3-census-lora"
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_path,
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)
    
    alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
"""
    
    inputs = tokenizer(
        [alpaca_prompt.format(question, context)], 
        return_tensors="pt"
    ).to("cuda")
    
    outputs = model.generate(**inputs, max_new_tokens=150, use_cache=True, temperature=0.1)
    response = tokenizer.batch_decode(outputs)[0]
    
    # Extract answer
    if "### Response:\n" in response:
        answer = response.split("### Response:\n")[1].split("
