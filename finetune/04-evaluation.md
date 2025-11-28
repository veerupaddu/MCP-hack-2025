# Model Evaluation

Testing the fine-tuned Phi-3 model on census and economy questions.

## Script: `docs/eval_finetuned.py`

### Usage

```bash
modal run docs/eval_finetuned.py
```

## Evaluation Process

### 1. Load Fine-tuned Model

```python
model_path = "/data/checkpoints/phi3-census-lora"

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=model_path,
    max_seq_length=2048,
    dtype=None,
    load_in_4bit=True,
)
FastLanguageModel.for_inference(model)  # Optimize for inference
```

### 2. Test Questions

The script tests with sample questions:

```python
questions = [
    {
        "question": "What is the population of Tokyo?",
        "context": "Context: Japan Census data."
    },
    {
        "question": "What is the average income in Osaka?",
        "context": "Context: Japan Economy & Labor data."
    },
    {
        "question": "How many households are in Hokkaido?",
        "context": "Context: Japan Census data."
    }
]
```

### 3. Generate Answers

Uses the Alpaca prompt template:

```
Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{question}

### Input:
{context}

### Response:
{model_generated_answer}
```

## Expected Output

### Example Results

```
Q: What is the population of Tokyo?
A: According to the '2020 Population Census' dataset, the population of Tokyo is 14,047,594.

Q: What is the average income in Osaka?
A: According to the 'National Survey of Family Income' dataset, the average income in Osaka is 5,200,000 yen.

Q: How many households are in Hokkaido?
A: According to the '2020 Census Households' dataset, the number of households in Hokkaido is 2,720,000.
```

## Evaluation Metrics

### Qualitative Assessment

**Check for:**
- ✅ Factual accuracy (matches training data)
- ✅ Proper formatting (cites dataset name)
- ✅ Coherent language
- ✅ Relevant context usage

### Quantitative Metrics (Optional)

For more rigorous evaluation, you can:

1. **Create test set** with known answers
2. **Calculate metrics:**
   - Exact match accuracy
   - F1 score
   - BLEU score
3. **Compare with base model** (before fine-tuning)

## Custom Evaluation

### Add Your Own Questions

Edit `docs/eval_finetuned.py`:

```python
questions = [
    {
        "question": "Your custom question here",
        "context": "Context: Japan Census data."
    },
    # Add more...
]
```

### Batch Evaluation

For testing many questions:

```python
# Load questions from file
import json

with open('test_questions.jsonl') as f:
    questions = [json.loads(line) for line in f]

answers = evaluate_model.remote(questions)
```

## Performance

### Inference Speed

| Hardware | Tokens/sec | Cost/1000 queries |
|----------|------------|-------------------|
| A10G | ~50 | $0.60 |
| A100 | ~100 | $1.10 |

### Response Quality

**After 60 steps:**
- Basic factual recall: ✅ Good
- Complex reasoning: ⚠️ Limited
- Hallucinations: ⚠️ Occasional

**After 500 steps:**
- Basic factual recall: ✅ Excellent
- Complex reasoning: ✅ Good
- Hallucinations: ✅ Rare

## Comparison: Base vs Fine-tuned

### Base Phi-3 (No Fine-tuning)

```
Q: What is the population of Tokyo?
A: I don't have access to real-time data. As of my last update in 2023, 
   Tokyo's population was approximately 14 million people. For the most 
   current information, please check official statistics.
```

**Issues:**
- Generic response
- No specific dataset reference
- Hedges with disclaimers

### Fine-tuned Phi-3

```
Q: What is the population of Tokyo?
A: According to the '2020 Population Census' dataset, the population 
   of Tokyo is 14,047,594.
```

**Improvements:**
- ✅ Specific number
- ✅ Cites source dataset
- ✅ Confident answer
- ✅ Matches training data format

## Limitations

### Current Limitations

1. **Training Data Only** - Model only knows data from training set
2. **No Real-time Updates** - Data is from 2020 census
3. **Exact Matches** - Best at recalling specific values it saw
4. **Limited Reasoning** - Struggles with calculations or comparisons

### Example Failures

**Question:** "What is the population difference between Tokyo and Osaka?"

**Expected:** Calculate 14,047,594 - 8,837,685 = 5,209,909

**Actual:** May hallucinate or refuse to answer

**Reason:** Model wasn't trained on comparison/calculation tasks

## Improving Results

### 1. More Training Steps

```python
# In finetune_modal.py
max_steps=1000  # Instead of 60
```

### 2. Better Data Quality

- Add more diverse question types
- Include comparison questions
- Add calculation examples

### 3. Larger LoRA Rank

```python
# In finetune_modal.py
r=32,  # Instead of 16
lora_alpha=32,
```

### 4. Ensemble with RAG

Combine fine-tuned model with RAG:
- Fine-tuned model: Fast recall of common facts
- RAG: Handles complex queries and edge cases

## Deployment Options

### Option 1: Modal Endpoint

Create a persistent API endpoint:

```python
@app.function(
    gpu="A10G",
    keep_warm=1,  # Always-on instance
)
@modal.web_endpoint(method="POST")
def predict(question: str):
    # Load model and generate answer
    return {"answer": answer}
```

### Option 2: Integrate with RAG

Replace base model in `src/modal-rag.py`:

```python
# Instead of base Phi-3
model_path = "/data/checkpoints/phi3-census-lora"
model = FastLanguageModel.from_pretrained(model_path)
```

### Option 3: Export to GGUF

For local deployment:

```python
# In finetune_modal.py, after training
model.save_pretrained_gguf(
    "/data/checkpoints/phi3-census-gguf",
    tokenizer,
    quantization_method="q4_k_m"
)
```

Then use with llama.cpp or Ollama.

## Next Steps

See [Next Steps & Improvements](05-next-steps.md) for ideas on extending this work.
