# How to Run the Fine-Tuning Pipeline

This guide walks you through the complete pipeline from data generation to model deployment.

---

## 📊 Dataset Generation Results

### Final Statistics
- **Training Samples**: 201,651
- **Validation Samples**: 22,407
- **Total Dataset**: 224,058 high-quality QA pairs
- **Improvement**: 150x more data than previous approach

### Batch Performance
| Batch | Files | Data Points | Status |
|-------|-------|-------------|--------|
| 1 | 1,000 | 100,611 | ✅ Excellent |
| 2 | 1,000 | 39,960 | ✅ Good |
| 3 | 1,000 | 0 | ⚠️ Complex files |
| 4 | 1,000 | 600 | ⚠️ Runner issue |
| 5 | 1,000 | 54,627 | ✅ Excellent |
| 6 | 1,000 | 5,400 | ✅ Good |
| 7 | 888 | 22,860 | ✅ Good |

---

## 🚀 Step-by-Step Instructions

### Step 1: Fine-Tune the Model

Run the fine-tuning job on Modal with H200 GPU:

```bash
cd /Users/veeru/agents/mcp-hack

# Start fine-tuning in detached mode
./venv/bin/modal run --detach src/finetune/finetune_modal.py
```

**What happens:**
- Loads 201,651 training samples from `finetune-dataset` volume
- Trains Phi-3-mini-4k-instruct with LoRA on H200 GPU
- Runs for ~90-120 minutes
- Saves model to `model-checkpoints` volume

**Monitor progress:**
```bash
# View live logs
modal app logs mcp-hack::finetune-phi3-modal
```

---

### Step 2: Evaluate the Model

After training completes, test the model:

```bash
./venv/bin/modal run src/finetune/eval_finetuned.py
```

This will run sample questions and show the model's answers.

---

### Step 3: Deploy API Endpoint

### 4. Deploy Inference API

You have three options for deployment. For production use with low latency (<3s), **Option B** is recommended.

**Option A: Standard GPU Endpoint (A10G)**
Good for testing, uses standard Transformers library.
```bash
./venv/bin/modal deploy src/finetune/api_endpoint.py
```

**Option B: High-Performance vLLM Endpoint (Recommended)**
Uses vLLM for <3s latency. Requires model merging first.

1. **Merge Model**: Convert LoRA adapter to full model
   ```bash
   ./venv/bin/modal run src/finetune/merge_model.py
   ```

2. **Deploy vLLM Endpoint**:
   ```bash
   ./venv/bin/modal deploy src/finetune/api_endpoint_vllm.py
   ```

**Option C: CPU Endpoint**
Slowest, but cheapest. Good for debugging without GPU quota.
```bash
./venv/bin/modal deploy src/finetune/api_endpoint_cpu.py
```

**Get the endpoint URL:**
```bash
modal app list
```

---

### Step 4: Test the API

```bash
# Example API call
curl -X POST https://YOUR-MODAL-URL/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the population of Tokyo?",
    "context": "Japan Census data"
  }'
```

---

## 📁 Key Files

### Data Processing
- `src/finetune/prepare_finetune_data.py` - Generates dataset from CSV files
- `docs/clean_sample.py` - Local testing script for data cleaning

### Model Training
- `src/finetune/finetune_modal.py` - Fine-tuning script (H200 GPU)
- `src/finetune/eval_finetuned.py` - Evaluation script

### API Deployment
- `src/finetune/api_endpoint.py` - GPU inference endpoint (A10G)
- `src/finetune/api_endpoint_cpu.py` - CPU inference endpoint (when created)

### Documentation
- `diagrams/finetuning.svg` - Visual pipeline diagram
- `finetune/04-evaluation.md` - Evaluation results

---

## 🔧 Modal Volumes

The pipeline uses these Modal volumes:

| Volume | Purpose | Size |
|--------|---------|------|
| `census-data` | Raw census CSV files | 6,838 files |
| `economy-labor-data` | Raw economy CSV files | 50 files |
| `finetune-dataset` | Generated JSONL training data | 224K samples |
| `model-checkpoints` | Fine-tuned model weights | ~7GB |

---

## 💡 Tips

### If Training Fails
```bash
# Check logs for errors
modal app logs mcp-hack::finetune-phi3-modal

# Restart training
./venv/bin/modal run --detach docs/finetune_modal.py
```

### If You Need to Regenerate Data
```bash
# Regenerate with new logic
./venv/bin/modal run --detach src/finetune/prepare_finetune_data.py
```

### View Volume Contents
```bash
# List files in a volume
modal volume ls finetune-dataset

# Download a file
modal volume get finetune-dataset train.jsonl finetune/train.jsonl
```

---

## 📈 Expected Timeline

| Step | Duration | Notes |
|------|----------|-------|
| Data Generation | ✅ Complete | 224K samples ready |
| Fine-Tuning | ~90-120 min | H200 GPU |
| Evaluation | ~5 min | Quick tests |
| API Deployment | ~2 min | Instant after deploy |

---

## 🎯 Next Steps

1. **Run fine-tuning** (see Step 1 above)
2. **Wait for completion** (~2 hours)
3. **Evaluate results** (see Step 2)
4. **Deploy API** (see Step 3)
5. **Test with real queries** (see Step 4)

---

## 📞 Troubleshooting

**Issue**: "Volume not found"
```bash
# List all volumes
modal volume list
```

**Issue**: "Out of memory during training"
- Reduce `per_device_train_batch_size` in `src/finetune/finetune_modal.py`
- Current: 2 (already optimized for H200)

**Issue**: "Model not loading in API"
- Ensure fine-tuning completed successfully
- Check `model-checkpoints` volume has files

---

## ✅ Success Criteria

After completing all steps, you should have:
- ✅ Fine-tuned Phi-3-mini model
- ✅ Deployed API endpoint
- ✅ Model answering questions about Japanese census/economy data
- ✅ Improved accuracy over base model

---

**Ready to start?** Run the fine-tuning command from Step 1!
