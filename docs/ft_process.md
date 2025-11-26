# Fine-Tuning Process for Japan Insurance Product Design

## Overview
This document outlines the recommended approach for fine-tuning a language model using LoRA for Japan-specific insurance product design.

## 1. Base Model Selection

### Recommended Models
- **For Japanese**: 
  - **Llama 3.1 8B/70B** (multilingual, good Japanese support)
  - **Qwen 2.5** (excellent Asian language performance)
  - **Japanese-specific**: `rinna/japanese-gpt-neox-3.6b` or `cyberagent/open-calm-7b`
- **For English with Japanese context**: Llama 3.1 or Mistral 7B

## 2. Dataset Preparation

### Data Sources

#### A. Census/Demographics Data (from e-Stat)
- Population age distribution
- Income levels by region
- Household composition
- Employment statistics

#### B. Insurance Domain Data
- Existing insurance product documents
- Coverage details, exclusions, premiums
- Target demographics for existing products

#### C. Synthetic Training Data
Create QA pairs or instruction-tuning format:

```json
{
  "instruction": "Design an insurance product for Tokyo residents aged 30-45 with average household income of ¥6M",
  "input": "Demographics: Tokyo, Age 30-45, Income ¥6M, Household size 3",
  "output": "Recommended product: Family Health Insurance with..."
}
```

## 3. LoRA Configuration

### Recommended Hyperparameters

```python
from peft import LoraConfig

lora_config = LoraConfig(
    r=16,                    # Rank (start with 16, can go up to 64)
    lora_alpha=32,           # Scaling factor (typically 2x rank)
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
```

### Parameter Tuning Guide
- **r (rank)**: Start with 16, increase to 32-64 for more capacity
- **lora_alpha**: Typically 2x the rank value
- **target_modules**: Focus on attention layers for efficiency
- **lora_dropout**: 0.05-0.1 for regularization

## 4. Training Framework

### Option 1: Unsloth (Recommended - Fastest)

```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/llama-3-8b-bnb-4bit",
    max_seq_length = 2048,
    dtype = None,
    load_in_4bit = True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
)
```

### Option 2: Axolotl (More Configurable)

```yaml
# config.yml
base_model: meta-llama/Llama-3.1-8B
model_type: LlamaForCausalLM
tokenizer_type: AutoTokenizer

adapter: lora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
lora_target_modules:
  - q_proj
  - v_proj
  - k_proj
  - o_proj

datasets:
  - path: data/insurance_training.jsonl
    type: alpaca

sequence_len: 2048
micro_batch_size: 4
gradient_accumulation_steps: 4
num_epochs: 3
learning_rate: 0.0002
```

## 5. Data Processing Pipeline

### Step-by-Step Process

1. **Extract Census Data**
   ```bash
   python3 download_census_data.py --workers 100
   ```

2. **Convert to Structured Format**
   - Parse Excel/CSV files
   - Extract key demographics (age, income, location, household)
   - Create demographic profiles

3. **Combine with Insurance Documents**
   - Extract text from insurance PDFs
   - Create context-aware examples
   - Map demographics to product features

4. **Generate Training Pairs**
   - Use GPT-4/Claude to create synthetic examples
   - Format: Instruction → Input → Output
   - Include diverse scenarios

5. **Format for Training**
   - Convert to Alpaca or ShareGPT format
   - Split into train/validation sets (90/10)
   - Save as JSONL

### Example Training Data Format

```json
{
  "instruction": "Based on the following demographic data, design an appropriate insurance product.",
  "input": "Location: Tokyo\nAge Group: 30-45\nAverage Income: ¥6,000,000\nHousehold Size: 3\nEmployment: Full-time",
  "output": "Product Recommendation: Comprehensive Family Health Insurance\n\nKey Features:\n- Coverage: ¥10M medical expenses\n- Premium: ¥15,000/month\n- Target: Young families with stable income\n- Benefits: Hospitalization, outpatient, dental\n- Exclusions: Pre-existing conditions (first year)\n\nRationale: This demographic shows stable income and family responsibility, making comprehensive health coverage with moderate premiums ideal."
}
```

## 6. Training Configuration

### Recommended Settings

```python
training_args = TrainingArguments(
    output_dir="./insurance-lora",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_strategy="epoch",
    evaluation_strategy="epoch",
    warmup_ratio=0.1,
    lr_scheduler_type="cosine",
)
```

## 7. Evaluation Strategy

### Quantitative Metrics
- **Perplexity**: Measure on held-out insurance product descriptions
- **BLEU/ROUGE**: Compare generated products to reference designs
- **Accuracy**: Classification of appropriate product types

### Qualitative Evaluation
- **Human Review**: Insurance experts evaluate product designs
- **Coherence**: Check logical consistency of recommendations
- **Domain Accuracy**: Verify compliance with insurance regulations

### Domain-Specific Tests
- Test on real demographic scenarios
- Validate premium calculations
- Check coverage appropriateness

## 8. Deployment Considerations

### Model Serving
- Use vLLM or TGI for efficient inference
- Quantize to 4-bit for production (GPTQ/AWQ)
- Deploy on Modal, RunPod, or local GPU

### Monitoring
- Track inference latency
- Monitor output quality
- Collect user feedback for continuous improvement

## Next Steps

1. **Data Processing**: Create script to convert census data to training format
2. **Training Pipeline**: Set up Unsloth/Axolotl environment
3. **Synthetic Generation**: Use LLM to create insurance examples from demographics
4. **Fine-tune**: Run LoRA training
5. **Evaluate**: Test on held-out scenarios
6. **Deploy**: Serve model for product design queries
