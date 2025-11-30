import modal
import os

app = modal.App("finetune-census-phi3")

# Volumes
vol_dataset = modal.Volume.from_name("finetune-dataset")
vol_checkpoints = modal.Volume.from_name("model-checkpoints", create_if_missing=True)

# Image: Build from CUDA base to ensure compatibility
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
    volumes={
        "/data/dataset": vol_dataset,
        "/data/checkpoints": vol_checkpoints
    },
    gpu="H200",  # Fastest GPU - 3-4x faster than A100
    timeout=86400, # 24 hours
)
def finetune():
    from unsloth import FastLanguageModel
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from datasets import load_dataset
    import torch
    
    print("🚀 Starting Fine-tuning Job...")
    
    # 1. Configuration
    max_seq_length = 2048 # Can go up to 4096 for Phi-3
    dtype = None # Auto detection
    load_in_4bit = True # Use 4bit quantization to reduce memory usage
    
    model_name = "unsloth/Phi-3-mini-4k-instruct"
    
    # 2. Load Model and Tokenizer
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=dtype,
        load_in_4bit=load_in_4bit,
    )
    
    # 3. Add LoRA Adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=16, # Rank
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj",],
        lora_alpha=16,
        lora_dropout=0, # Supports any, but = 0 is optimized
        bias="none",    # Supports any, but = "none" is optimized
        use_gradient_checkpointing="unsloth", # True or "unsloth" for very long context
        random_state=3407,
        use_rslora=False,  # Rank stabilized LoRA
        loftq_config=None, # LoftQ
    )
    
    # 4. Load Dataset
    # We generated JSONL files.
    # Format: {"instruction": ..., "input": ..., "output": ...}
    dataset = load_dataset("json", data_files={"train": "/data/dataset/train.jsonl", "test": "/data/dataset/val.jsonl"})
    
    # 5. Formatting Function
    # Alpaca format
    alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""

    EOS_TOKEN = tokenizer.eos_token # Must add EOS_TOKEN
    def formatting_prompts_func(examples):
        instructions = examples["instruction"]
        inputs       = examples["input"]
        outputs      = examples["output"]
        texts = []
        for instruction, input, output in zip(instructions, inputs, outputs):
            # Must add EOS_TOKEN, otherwise your generation will go on forever!
            text = alpaca_prompt.format(instruction, input, output) + EOS_TOKEN
            texts.append(text)
        return { "text" : texts, }

    dataset = dataset.map(formatting_prompts_func, batched=True)
    
    # 6. Training Arguments (Optimized for H200)
    training_args = TrainingArguments(
        per_device_train_batch_size=4,  # Increased for H200's 141GB memory
        gradient_accumulation_steps=2,  # Effective batch size = 8
        warmup_steps=100,  # Increased for larger dataset
        max_steps=10000,  # ~4% of full epoch, completes in ~90 minutes
        # num_train_epochs=1,  # Full epoch takes ~30 hours with 1.9M samples
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=100,  # Log less frequently
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="outputs",
        report_to="none",  # Disable wandb logging
        save_strategy="steps",
        save_steps=10000,  # Save checkpoints every 10k steps
        save_total_limit=2,  # Keep only 2 checkpoints
    )
    
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        dataset_num_proc=2,
        packing=False, # Can make training 5x faster for short sequences
        args=training_args,
    )
    
    # 7. Train
    print("Training...")
    trainer_stats = trainer.train()
    
    # 8. Save Model
    print("Saving model to /data/checkpoints/phi3-census-lora...")
    model.save_pretrained("/data/checkpoints/phi3-census-lora")
    tokenizer.save_pretrained("/data/checkpoints/phi3-census-lora")
    
    # Also save to GGUF if possible? Unsloth supports it.
    # model.save_pretrained_gguf("/data/checkpoints/phi3-census-gguf", tokenizer, quantization_method = "q4_k_m")
    
    # Commit volume
    vol_checkpoints.commit()
    print("✅ Fine-tuning Complete!")

@app.local_entrypoint()
def main():
    finetune.remote()
