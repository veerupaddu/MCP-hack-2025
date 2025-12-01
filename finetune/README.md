# Fine-tuning Phi-3 on Japanese Census & Economy Data

This directory contains the complete pipeline for fine-tuning Microsoft's Phi-3-mini-4k-instruct model on Japanese statistical data from e-Stat.

## 📁 Project Structure

```
finetune/
├── README.md                    # This file - overview and quick start
├── 01-data-preparation.md       # Data download and CSV conversion
├── 02-dataset-generation.md     # Creating training dataset from CSVs
├── 03-model-training.md         # Fine-tuning with Unsloth
├── 04-evaluation.md             # Testing the fine-tuned model
└── 05-next-steps.md             # Future improvements and integration
```

## 🎯 Objective

Fine-tune Phi-3-mini to answer statistical questions about Japanese census, economy, and labor data without requiring RAG for every query.

## 🚀 Quick Start

### Prerequisites
- Modal account with GPU access (A100-80GB recommended)
- Python 3.10+
- Modal CLI installed and authenticated

### Complete Pipeline

```bash
# 1. Download census data (if not already done)
modal run src/finetune/download_census_modal.py

# 2. Convert Excel files to CSV
modal run --detach src/finetune/convert_census_to_csv.py

# 3. Clean up filenames
modal run src/finetune/fix_csv_filenames.py

# 4. Generate training dataset
modal run src/finetune/prepare_finetune_data.py

# 5. Fine-tune the model
modal run --detach src/finetune/finetune_modal.py

# 6. Evaluate the model
modal run src/finetune/eval_finetuned.py
```

## 📊 Results Summary

- **Dataset Size**: 2-3 million QA pairs (all rows from all CSVs)
- **Source Files**: 6,888 CSV files from census and economy data
- **Training Time**: ~45-60 minutes on H200 GPU
- **Training Cost**: ~$4.50-6.00 on H200
- **Final Loss**: ~0.08-0.10 (excellent performance)
- **Model Size**: LoRA adapters (~100MB) on top of Phi-3-mini (3.8B params)
- **GPU**: H200 (141GB memory, 3-4x faster than A100)

## 🔑 Key Features

- ✅ **Unsloth Integration**: 2x faster training with optimized kernels
- ✅ **4-bit Quantization**: Efficient memory usage via bitsandbytes
- ✅ **LoRA Fine-tuning**: Only train 0.5% of parameters
- ✅ **Modal Volumes**: Persistent storage for data and checkpoints
- ✅ **Parallel Processing**: Fast CSV conversion with 100 concurrent workers

## 📦 Modal Volumes

| Volume Name | Purpose | Size |
|-------------|---------|------|
| `census-data` | Raw census Excel/CSV files | ~2GB |
| `economy-labor-data` | Economy & labor Excel/CSV files | ~100MB |
| `finetune-dataset` | Training JSONL files | ~500MB |
| `model-checkpoints` | Fine-tuned LoRA adapters | ~100MB |

## 🛠️ Scripts Overview

| Script | Purpose | Runtime |
|--------|---------|---------|
| [download_census_modal.py](../src/finetune/download_census_modal.py) | Download census data from e-Stat | ~15 min |
| [convert_census_to_csv.py](../src/finetune/convert_census_to_csv.py) | Convert Excel to CSV with readable names | ~10 min |
| [fix_csv_filenames.py](../src/finetune/fix_csv_filenames.py) | Clean URL-encoded filenames | ~1 min |
| [prepare_finetune_data.py](../src/finetune/prepare_finetune_data.py) | Generate QA pairs from CSVs | ~5 min |
| [finetune_modal.py](../src/finetune/finetune_modal.py) | Fine-tune Phi-3 with Unsloth | ~2.5 min (60 steps) |
| [eval_finetuned.py](../src/finetune/eval_finetuned.py) | Test fine-tuned model | ~30 sec |

## 📚 Documentation

For detailed information, see the individual documentation files:

1. **[Data Preparation](01-data-preparation.md)** - Downloading and processing raw data
2. **[Dataset Generation](02-dataset-generation.md)** - Creating training examples
3. **[Model Training](03-model-training.md)** - Fine-tuning configuration and process
4. **[Evaluation](04-evaluation.md)** - Testing and validation
5. **[Next Steps](05-next-steps.md)** - Improvements and integration ideas

## 💡 Quick Tips

- **Cost**: A100 costs ~$1.10/hr. 60-step training = ~$0.05
- **Scaling**: Increase `max_steps` in `finetune_modal.py` for better results
- **Debugging**: Use `modal run` (without `--detach`) to see live logs
- **Monitoring**: Check Modal dashboard for GPU utilization and logs

## 🐛 Troubleshooting

See [03-model-training.md](03-model-training.md#troubleshooting) for common issues and solutions.

## 📄 License

This project uses data from e-Stat (Statistics Bureau of Japan) and Microsoft's Phi-3 model.
