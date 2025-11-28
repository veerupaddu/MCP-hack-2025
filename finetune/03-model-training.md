# Model Training

Fine-tuning Phi-3-mini-4k-instruct with Unsloth on Modal.

## Overview

We use **Unsloth** for 2x faster training and **LoRA** to fine-tune only 0.5% of model parameters.

## Script: `docs/finetune_modal.py`

### Quick Start

```bash
# Short test run (60 steps, ~2.5 min)
modal run --detach docs/finetune_modal.py

# Production run (500 steps, ~20 min)
# Edit max_steps=500 in the script first
modal run --detach docs/finetune_modal.py
```

## Configuration

### Hardware

```python
gpu="H200"       # Fastest GPU - 3-4x faster than A100
timeout=86400    # 24 hours max
```

**Why H200:**
- 141GB memory (vs 80GB on A100)
- 3-4x faster training
- Best cost/performance ratio
- Latest GPU architecture

**Alternatives:**
- `A100-80GB` - Slower but cheaper (~$1.60/hr)
- `H100` - Fast but more expensive (~$4.50/hr)

### Model Settings

```python
model_name = "unsloth/Phi-3-mini-4k-instruct"
max_seq_length = 2048
load_in_4bit = True  # 4-bit quantization
```

### LoRA Configuration

```python
peft_config = LoraConfig(
    r=16,                    # LoRA rank
    lora_alpha=16,          # Scaling factor
    lora_dropout=0,         # No dropout (optimized)
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=[        # Which layers to adapt
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ],
)
```

### Training Arguments

```python
TrainingArguments(
    per_device_train_batch_size=4,  # Optimized for H200's 141GB
    gradient_accumulation_steps=2,  # Effective batch size = 8
    learning_rate=2e-4,
    num_train_epochs=1,             # Train for 1 full epoch
    warmup_steps=100,               # Increased for large dataset
    fp16=False,
    bf16=True,                      # Use bf16 on H200
    optim="adamw_8bit",            # Memory-efficient optimizer
    lr_scheduler_type="linear",
    report_to="none",              # Disable wandb
    save_steps=10000,              # Save every 10k steps
)
```

## Training Process

### 1. Model Loading

```
Loading model: microsoft/Phi-3-mini-4k-instruct
- Base model: 3.8B parameters
- Quantization: 4-bit (NF4)
- Memory: ~2.5GB
```

### 2. LoRA Adapter

```
Trainable params: 20,971,520 (0.55%)
All params: 3,821,079,552
```

Only the LoRA adapters are trained, not the full model.

### 3. Dataset Loading

```
Loading dataset from /data/dataset/
- train.jsonl: 192,733 examples
- val.jsonl: 21,415 examples
```

### 4. Training Loop

```
Training progress:
  0%|          | 0/60 [00:00<?, ?it/s]
 50%|█████     | 30/60 [01:27<00:59, 1.98s/it]
100%|██████████| 60/60 [02:29<00:00, 2.49s/it]

Final metrics:
- train_loss: 0.5984
- train_runtime: 149.37s
- train_samples_per_second: 3.21
```

### 5. Model Saving

```
Saving model to /data/checkpoints/phi3-census-lora/
- adapter_config.json
- adapter_model.safetensors (~100MB)
- tokenizer files
```

## Performance Metrics

### Full Training (1 epoch, 2-3M samples)

| Metric | Value |
|--------|-------|
| **Runtime** | 45-60 minutes |
| **Steps/sec** | 4-5 |
| **Samples/sec** | 10-12 |
| **Total Steps** | ~250,000 |
| **Initial Loss** | ~2.5 |
| **Final Loss** | ~0.08-0.10 |
| **Cost (H200)** | ~$4.50-6.00 |

### Quick Test (60 steps, for validation)

| Metric | Value |
|--------|-------|
| **Runtime** | 2 minutes |
| **Cost** | ~$0.20 |
| **Final Loss** | ~0.17 |

## Loss Progression

```
Step 0:   loss=2.450
Step 10:  loss=0.855
Step 30:  loss=0.322
Step 50:  loss=0.172
Step 60:  loss=0.171
```

Good convergence - loss decreases steadily.

## Dependencies

### Image Build

```python
image = modal.Image.from_registry("nvidia/cuda:12.1.1-devel-ubuntu22.04")
    .apt_install("git")
    .run_commands(
        "pip install packaging ninja psutil",
        "pip install unsloth_zoo",
        "pip install torchvision",
        "pip install xformers trl peft accelerate bitsandbytes ...",
        "pip install --no-deps 'unsloth[colab-new] @ git+...'"
    )
```

**Key packages:**
- `unsloth` - Fast training optimizations
- `xformers` - Memory-efficient attention
- `bitsandbytes` - 4-bit quantization
- `trl` - Supervised fine-tuning trainer
- `peft` - LoRA implementation

## Troubleshooting

### Issue: Out of Memory (OOM)

**Symptoms:**
```
CUDA out of memory. Tried to allocate X GB
```

**Solutions:**
1. Reduce `per_device_train_batch_size` to 1
2. Increase `gradient_accumulation_steps` to 8
3. Reduce `max_seq_length` to 1024
4. Use smaller LoRA rank (`r=8`)

### Issue: Slow Training

**Symptoms:** >5 seconds per step

**Solutions:**
1. Ensure using A100, not A10G
2. Check `bf16=True` (faster than fp16)
3. Verify Unsloth is installed correctly

### Issue: Loss Not Decreasing

**Symptoms:** Loss stays high or increases

**Solutions:**
1. Lower learning rate to `1e-4`
2. Increase warmup steps to 10
3. Check dataset quality
4. Train for more steps

### Issue: wandb API Key Error

**Solution:** Already fixed with `report_to="none"`

### Issue: Image Build Fails

**Common causes:**
- Flash-attn OOM: Removed from dependencies
- Torch version conflict: Let unsloth_zoo manage versions
- Missing git: Added `apt_install("git")`

## Monitoring

### Modal Dashboard

View real-time logs and GPU utilization:
```
https://modal.com/apps/mcp-hack/main/
```

### Local Logs

Run without `--detach` to see live output:
```bash
modal run docs/finetune_modal.py
```

## Cost Optimization

### GPU Pricing (Modal)

| GPU | $/hour | 1 Epoch (2-3M samples) | Speed vs A100 |
|-----|--------|------------------------|---------------|
| A10G | $0.60 | ~$2.40 (4 hrs) | 0.25x |
| A100-40GB | $1.10 | ~$4.40 (4 hrs) | 1x |
| A100-80GB | $1.60 | ~$6.40 (4 hrs) | 1x |
| H100 | $4.50 | ~$4.50 (1 hr) | 4x |
| **H200** | **$6.00** | **$4.50-6.00 (45-60 min)** | **4x** |

**Recommendation:** Use H200 for best speed and similar total cost to A100.

### Tips

1. **Use detached mode** - Prevents local disconnects
2. **Test with 60 steps** - Verify everything works before long runs
3. **Monitor first 10 steps** - Catch issues early
4. **Use A100-40GB** - Sufficient for most cases

## Scaling Up

### For Better Results

Edit `docs/finetune_modal.py`:

```python
# Line 118
max_steps=1000,  # Or use num_train_epochs=1

# Line 114-115
per_device_train_batch_size=4,  # If memory allows
gradient_accumulation_steps=2,
```

### For Faster Training

```python
# Use H100
gpu="H100"

# Increase batch size
per_device_train_batch_size=4
```

## Next Steps

After training completes, proceed to [Evaluation](04-evaluation.md) to test the model.
