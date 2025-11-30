import modal
import os

app = modal.App("finetune-phi3-modal")

# Volumes
vol_dataset = modal.Volume.from_name("finetune-dataset")
vol_checkpoints = modal.Volume.from_name("model-checkpoints", create_if_missing=True)

# Image with all dependencies (v5 - using standard transformers without unsloth)
image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        "torch==2.4.0",
        "transformers==4.44.2",
        "datasets==2.20.0",
        "trl==0.9.6",
        "peft==0.12.0",
        "bitsandbytes==0.43.3",
        "accelerate==0.33.0",
        "scipy==1.14.0",
        "hf_transfer",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

@app.function(
    image=image,
    gpu="H200",
    timeout=10800,  # 3 hours
    volumes={
        "/data/dataset": vol_dataset,
        "/data/checkpoints": vol_checkpoints
    }
)
def finetune():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, BitsAndBytesConfig
    from datasets import load_dataset
    from trl import SFTTrainer
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    
    print("🚀 Starting fine-tuning job...")
    
    # Load model with 4-bit quantization
    print("📦 Loading base model...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        "microsoft/Phi-3-mini-4k-instruct",
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    
    tokenizer = AutoTokenizer.from_pretrained(
        "microsoft/Phi-3-mini-4k-instruct",
        trust_remote_code=True,
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    # Prepare model for training
    model = prepare_model_for_kbit_training(model)
    
    # Configure LoRA
    print("⚙️ Configuring LoRA...")
    peft_config = LoraConfig(
        r=16,
        lora_alpha=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    
    # Load dataset
    print("📊 Loading training dataset...")
    dataset = load_dataset("json", data_files={
        "train": "/data/dataset/train.jsonl",
        "validation": "/data/dataset/val.jsonl"
    })
    
    print(f"✅ Loaded {len(dataset['train'])} training samples")
    print(f"✅ Loaded {len(dataset['validation'])} validation samples")
    
    # Alpaca prompt template
    alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""
    
    EOS_TOKEN = tokenizer.eos_token
    
    def formatting_prompts_func(examples):
        instructions = examples["instruction"]
        inputs = examples["input"]
        outputs = examples["output"]
        texts = []
        for instruction, input_text, output in zip(instructions, inputs, outputs):
            text = alpaca_prompt.format(instruction, input_text, output) + EOS_TOKEN
            texts.append(text)
        return {"text": texts}
    
    dataset = dataset.map(formatting_prompts_func, batched=True)
    
    # Training arguments
    print("🎯 Setting up training configuration...")
    training_args = TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=100,
        max_steps=10000,
        learning_rate=2e-4,
        fp16=False,
        bf16=True,
        logging_steps=10,
        optim="paged_adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=42,
        output_dir="/tmp/outputs",
        report_to="none",
        save_strategy="steps",
        save_steps=1000,
        save_total_limit=3,
    )
    
    # Trainer
    print("🏋️ Initializing trainer...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        dataset_text_field="text",
        max_seq_length=2048,
        packing=False,
        args=training_args,
    )
    
    # Train
    print("🔥 Starting training...")
    trainer.train()
    
    # Save model
    # Save adapter
    print("💾 Saving adapter...")
    model.save_pretrained("/data/checkpoints/final_model")
    tokenizer.save_pretrained("/data/checkpoints/final_model")
    
    # Merge and save full model for vLLM
    print("🔄 Merging model for vLLM optimization...")
    # Reload base model in bfloat16 (not 4-bit) for merging
    base_model = AutoModelForCausalLM.from_pretrained(
        "microsoft/Phi-3-mini-4k-instruct",
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    
    # Load adapter
    from peft import PeftModel
    model_to_merge = PeftModel.from_pretrained(base_model, "/data/checkpoints/final_model")
    
    # Merge
    merged_model = model_to_merge.merge_and_unload()
    
    # Save merged model
    print("💾 Saving merged model to /data/checkpoints/merged_model...")
    merged_model.save_pretrained("/data/checkpoints/merged_model", safe_serialization=True)
    tokenizer.save_pretrained("/data/checkpoints/merged_model")
    
    vol_checkpoints.commit()
    
    print("✅ Fine-tuning & Merging complete! Merged model saved for vLLM.")

@app.local_entrypoint()
def main():
    finetune.remote()
