# Adding More Training Data

This guide shows you how to increase your training dataset size.

## Current Dataset

- **Size**: 214,148 QA pairs
- **Sampling**: 50 rows per CSV file
- **Files**: 6,888 CSV files

## Method 1: Increase Sampling (Recommended ✅)

**Already done!** The sampling has been increased from 50 to 100 rows per CSV.

### Regenerate Dataset

```bash
modal run docs/prepare_finetune_data.py
```

**Expected new size**: ~428,000 QA pairs (2x increase)

### Adjust Sampling Further

Edit `docs/prepare_finetune_data.py` line 77:

```python
# For 3x data (150 rows per file)
sample_rows = 150

# For 5x data (250 rows per file)
sample_rows = 250

# For ALL rows (no limit)
sample_rows = None  # Then remove the sampling logic
```

**Trade-offs:**
- ✅ More data = better model performance
- ❌ Longer dataset generation time
- ❌ Longer training time
- ❌ More storage needed

---

## Method 2: Add New Data Sources

### Step 1: Find New Datasets

Visit [e-Stat](https://www.e-stat.go.jp/) and find dataset IDs:

**Examples:**
- Health Statistics: `toukei=00450012`
- Education Statistics: `toukei=00400001`
- Housing Statistics: `toukei=00200522`
- Transportation: `toukei=00600330`

### Step 2: Create Download Script

Create `docs/download_additional_data.py`:

```python
import modal

app = modal.App("download-additional-data")
volume = modal.Volume.from_name("additional-data", create_if_missing=True)

DATASETS = {
    "health": "00450012",
    "education": "00400001",
    "housing": "00200522",
}

# ... (similar to download_economy_labor_modal.py)
```

### Step 3: Download and Convert

```bash
# Download
modal run docs/download_additional_data.py

# Convert to CSV
modal run docs/convert_additional_to_csv.py
```

### Step 4: Update Dataset Generator

Edit `docs/prepare_finetune_data.py` to include new volume:

```python
vol_additional = modal.Volume.from_name("additional-data")

@app.function(
    volumes={
        "/data/census": vol_census,
        "/data/economy": vol_economy,
        "/data/additional": vol_additional,  # Add this
    }
)
def list_csv_files():
    # Add loop for /data/additional
    for root, _, filenames in os.walk("/data/additional"):
        if f.lower().endswith('.csv'):
            files.append({
                "path": os.path.join(root, f),
                "source": "Japan Additional Statistics"
            })
```

### Step 5: Regenerate Dataset

```bash
modal run docs/prepare_finetune_data.py
```

---

## Method 3: Add Custom QA Pairs

For high-quality, manually curated questions.

### Step 1: Create Custom Pairs

Edit `docs/create_custom_qa.py` and add your questions:

```python
custom_qa_pairs = [
    {
        "instruction": "Your question here",
        "input": "Context: Japan Census data.",
        "output": "Your answer here"
    },
    # Add more...
]
```

### Step 2: Generate JSONL

```bash
python docs/create_custom_qa.py
```

### Step 3: Upload to Modal Volume

```python
import modal

app = modal.App("upload-custom-data")
vol = modal.Volume.from_name("finetune-dataset")

@app.function(volumes={"/data": vol})
def upload_custom():
    import shutil
    shutil.copy("custom_train.jsonl", "/data/custom_train.jsonl")
    vol.commit()

@app.local_entrypoint()
def main():
    upload_custom.remote()
```

### Step 4: Merge with Existing Data

Edit `docs/prepare_finetune_data.py` to load and merge:

```python
# After generating all_data
custom_path = "/data/dataset/custom_train.jsonl"
if os.path.exists(custom_path):
    with open(custom_path) as f:
        for line in f:
            all_data.append(json.loads(line))
```

---

## Method 4: Generate Synthetic Data

Use GPT-4 or Claude to generate more questions:

```python
import anthropic

client = anthropic.Anthropic(api_key="your-key")

def generate_questions(csv_data):
    prompt = f"""
    Given this census data:
    {csv_data}
    
    Generate 10 diverse questions and answers about this data.
    Format as JSON with 'instruction', 'input', 'output' fields.
    """
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content
```

---

## Method 5: Data Augmentation

Create variations of existing questions:

```python
def augment_question(qa_pair):
    variations = []
    
    # Rephrase question
    variations.append({
        "instruction": f"Can you tell me {qa_pair['instruction'].lower()}",
        "input": qa_pair["input"],
        "output": qa_pair["output"]
    })
    
    # Different context
    variations.append({
        "instruction": qa_pair["instruction"],
        "input": "Context: Statistical data from Japan.",
        "output": qa_pair["output"]
    })
    
    return variations
```

---

## Recommended Approach

**For best results, combine methods:**

1. ✅ **Increase sampling to 100-150 rows** (Method 1)
2. ✅ **Add 500-1000 custom QA pairs** (Method 3)
3. ✅ **Download 1-2 additional datasets** (Method 2)

**Expected total:** ~500,000 - 600,000 QA pairs

---

## After Adding Data

### 1. Regenerate Dataset

```bash
modal run docs/prepare_finetune_data.py
```

### 2. Verify Dataset Size

```bash
# Check train.jsonl size
wc -l /data/dataset/train.jsonl
```

### 3. Retrain Model

```bash
# Increase training steps proportionally
# Edit docs/finetune_modal.py:
# max_steps = 500  # or num_train_epochs = 1

modal run --detach docs/finetune_modal.py
```

### 4. Compare Results

Run evaluation on both models:
- Old model (214K data, 60 steps)
- New model (500K data, 500 steps)

---

## Troubleshooting

### Dataset Too Large

**Issue:** Out of memory during dataset loading

**Solution:**
```python
# Use streaming dataset
from datasets import load_dataset

dataset = load_dataset(
    "json",
    data_files={"train": "train.jsonl"},
    streaming=True  # Don't load all at once
)
```

### Training Too Slow

**Issue:** 500K samples takes too long

**Solution:**
- Use `num_train_epochs=0.5` (half epoch)
- Increase batch size to 4 or 8
- Use H100 instead of A100

### Low Quality Data

**Issue:** Generated questions are repetitive

**Solution:**
- Add more diverse question templates
- Sample from different columns
- Add custom high-quality pairs

---

## Next Steps

After adding more data, see [03-model-training.md](03-model-training.md) for training configuration.
