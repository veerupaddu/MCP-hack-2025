import modal

app = modal.App("merge-adapter")

vol_checkpoints = modal.Volume.from_name("model-checkpoints")

image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        "torch==2.4.0",
        "transformers==4.44.2",
        "peft==0.12.0",
        "bitsandbytes==0.43.3",
        "accelerate==0.33.0",
        "hf_transfer",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

@app.function(
    image=image,
    gpu="A10G",
    volumes={"/data/checkpoints": vol_checkpoints},
    timeout=1800
)
def merge_model():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    import os
    
    print("🚀 Starting model merge...")
    
    # Check if adapter exists
    if not os.path.exists("/data/checkpoints/final_model"):
        print("❌ Error: Adapter not found at /data/checkpoints/final_model")
        return
    
    print("📦 Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        "microsoft/Phi-3-mini-4k-instruct",
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    
    print("🔗 Loading adapter...")
    model_to_merge = PeftModel.from_pretrained(base_model, "/data/checkpoints/final_model")
    
    print("🔄 Merging...")
    merged_model = model_to_merge.merge_and_unload()
    
    print("💾 Saving merged model to /data/checkpoints/merged_model...")
    merged_model.save_pretrained("/data/checkpoints/merged_model", safe_serialization=True)
    
    tokenizer = AutoTokenizer.from_pretrained(
        "microsoft/Phi-3-mini-4k-instruct",
        trust_remote_code=True,
    )
    tokenizer.save_pretrained("/data/checkpoints/merged_model")
    
    vol_checkpoints.commit()
    print("✅ Merge complete!")

@app.local_entrypoint()
def main():
    merge_model.remote()
