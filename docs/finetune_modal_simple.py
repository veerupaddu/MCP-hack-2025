import modal
import os

app = modal.App("finetune-census-phi3-simple")

# Volumes
vol_dataset = modal.Volume.from_name("finetune-dataset")
vol_checkpoints = modal.Volume.from_name("model-checkpoints", create_if_missing=True)

# Simple image without Unsloth - just use standard HuggingFace + PEFT
image = modal.Image.debian_slim(python_version="3.10") \
    .pip_install(
        "torch==2.4.0",
        "transformers==4.41.2",
        "peft==0.11.1",
        "trl==0.9.4",
        "accelerate==0.30.1",
        "bitsandbytes==0.43.1",
        "datasets==2.19.2",
        "scipy==1.13.1"
    )

@app.function(
    image=image,
    volumes={
        "/data/dataset": vol_dataset,
        "/data/checkpoints": vol_checkpoints
    },
    gpu="A100-80GB",
    timeout=86400,
)
def finetune():
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer
    from datasets import load_dataset
    import torch
    
    print("🚀 Starting Fine-tuning Job...")
    
    # Configuration
    model_name = "microsoft/Phi-3-mini-4k-instruct"
    max_seq_length = 2048
    
    # Load model with 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    
    print(f"Loading model: {model_name}")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    # Prepare model for training
    model = prepare_model_for_kbit_training(model)
    
    # LoRA configuration
    peft_config = LoraConfig(
        r=16,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    
    # Load dataset
    print("Loading dataset...")
    dataset = load_dataset("json", data_files={
        "train": "/data/dataset/train.jsonl",
        "test": "/data/dataset/val.jsonl"
    })
    
    # Formatting function
    def formatting_prompts_func(examples):
        alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""
        
        instructions = examples["instruction"]
        inputs = examples["input"]
        outputs = examples["output"]
        texts = []
        
        for instruction, input_text, output in zip(instructions, inputs, outputs):
            text = alpaca_prompt.format(instruction, input_text, output) + tokenizer.eos_token
            texts.append(text)
        
        return {"text": texts}
    
    dataset = dataset.map(formatting_prompts_func, batched=True)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir="/tmp/outputs",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=10,
        max_steps=100,  # Short test run
        save_steps=50,
        save_total_limit=2,
        fp16=True,
        optim="paged_adamw_8bit",
        warmup_steps=5,
        lr_scheduler_type="linear",
    )
    
    # Trainer
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        tokenizer=tokenizer,
        packing=False,
    )
    
    # Train
    print("Starting training...")
    trainer.train()
    
    # Save
    print("Saving model...")
    model.save_pretrained("/data/checkpoints/phi3-census-lora")
    tokenizer.save_pretrained("/data/checkpoints/phi3-census-lora")
    
    vol_checkpoints.commit()
    print("✅ Fine-tuning Complete!")

@app.local_entrypoint()
def main():
    finetune.remote()
