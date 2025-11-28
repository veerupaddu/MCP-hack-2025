# Next Steps & Improvements

Ideas for extending and improving the fine-tuning pipeline.

## 🚀 Immediate Improvements

### 1. Longer Training

**Current:** 60 steps (~2.5 min)
**Recommended:** 500-1000 steps (~20-40 min)

```python
# Edit docs/finetune_modal.py line 118
max_steps=1000,
```

**Expected improvements:**
- Lower loss (0.17 → 0.10)
- Better generalization
- Fewer hallucinations

### 2. Larger LoRA Rank

**Current:** r=16
**Try:** r=32 or r=64

```python
# Edit docs/finetune_modal.py
peft_config = LoraConfig(
    r=32,  # More capacity
    lora_alpha=32,
    # ... rest stays same
)
```

**Trade-offs:**
- ✅ Better performance
- ❌ Slower training
- ❌ Larger checkpoint size

### 3. Full Epoch Training

Instead of fixed steps, train for full epochs:

```python
# Replace max_steps with:
num_train_epochs=1,  # ~80,000 steps for 192k samples
```

**Warning:** This will take ~3-4 hours on A100

## 📊 Data Enhancements

### 1. Add More Question Types

**Current:** Simple lookup questions

**Add:**
- **Comparison:** "Which prefecture has more population, Tokyo or Osaka?"
- **Calculation:** "What is the population density of Tokyo?"
- **Aggregation:** "What is the total population of all prefectures?"
- **Trend:** "How has the population changed from 2015 to 2020?"

**Implementation:**

```python
# In prepare_finetune_data.py
def generate_comparison_qa(row1, row2, col, title):
    if row1[col] > row2[col]:
        answer = f"{row1['label']} has higher {col} than {row2['label']}"
    # ...
```

### 2. Multi-turn Conversations

Create conversational datasets:

```json
{
  "messages": [
    {"role": "user", "content": "What is Tokyo's population?"},
    {"role": "assistant", "content": "14,047,594"},
    {"role": "user", "content": "And Osaka?"},
    {"role": "assistant", "content": "8,837,685"}
  ]
}
```

### 3. Incorporate Time Series

Add historical data (2015, 2010, 2005 census):

```json
{
  "instruction": "How has Tokyo's population changed from 2015 to 2020?",
  "output": "Tokyo's population increased from 13,515,271 in 2015 to 14,047,594 in 2020, a growth of 532,323 people."
}
```

## 🔧 Technical Improvements

### 1. Hyperparameter Tuning

**Current settings are defaults. Try:**

| Parameter | Current | Try |
|-----------|---------|-----|
| Learning rate | 2e-4 | 1e-4, 5e-5 |
| Batch size | 2 | 4, 8 |
| Warmup steps | 5 | 10, 50 |
| Weight decay | 0.01 | 0.001, 0.1 |

**Use wandb for tracking:**

```python
# In finetune_modal.py
report_to="wandb",  # Enable logging
```

### 2. Gradient Checkpointing

Reduce memory usage:

```python
model.gradient_checkpointing_enable()
```

Allows larger batch sizes or longer sequences.

### 3. Mixed Precision Training

Already using bf16, but can optimize further:

```python
from torch.cuda.amp import autocast

with autocast():
    outputs = model(**inputs)
```

### 4. Flash Attention

If you can build it (requires more memory):

```python
# In image definition
.run_commands(
    "pip install flash-attn --no-build-isolation"
)
```

**Benefits:**
- 2-3x faster training
- Lower memory usage

## 🌐 Integration Ideas

### 1. RAG + Fine-tuned Model Hybrid

**Architecture:**

```
User Query
    ↓
┌───────────────┐
│ Query Router  │ ← Classify: factual lookup vs complex reasoning
└───────────────┘
    ↓         ↓
Fine-tuned   RAG
(Fast)       (Accurate)
```

**Implementation:**

```python
def answer_query(question):
    if is_simple_lookup(question):
        return finetuned_model.generate(question)
    else:
        return rag_system.query(question)
```

### 2. API Endpoint

Deploy as a REST API:

```python
@app.function(gpu="A10G", keep_warm=1)
@modal.web_endpoint(method="POST")
def census_qa(request: dict):
    question = request["question"]
    answer = model.generate(question)
    return {"answer": answer, "source": "fine-tuned-phi3"}
```

**Usage:**

```bash
curl -X POST https://your-modal-endpoint.modal.run \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the population of Tokyo?"}'
```

### 3. Chatbot Interface

Build a Gradio/Streamlit UI:

```python
import gradio as gr

def chat(message, history):
    response = model.generate(message)
    return response

gr.ChatInterface(chat).launch()
```

### 4. Slack/Discord Bot

Integrate with messaging platforms:

```python
@slack_app.event("message")
def handle_message(event):
    question = event["text"]
    if "census" in question.lower():
        answer = finetuned_model.generate(question)
        slack_client.chat_postMessage(
            channel=event["channel"],
            text=answer
        )
```

## 📈 Advanced Techniques

### 1. Instruction Tuning

Add system prompts and roles:

```json
{
  "system": "You are a Japanese census data expert.",
  "instruction": "Answer questions about population statistics.",
  "input": "What is Tokyo's population?",
  "output": "According to the 2020 census, Tokyo has 14,047,594 residents."
}
```

### 2. RLHF (Reinforcement Learning from Human Feedback)

**Steps:**
1. Generate multiple answers
2. Human ranks them
3. Train reward model
4. Use PPO to optimize

**Tools:** TRL's `PPOTrainer`

### 3. Multi-task Learning

Train on multiple tasks simultaneously:
- Census QA
- Economy QA
- General knowledge
- Summarization

### 4. Continual Learning

Update model with new data without forgetting:

```python
# Elastic Weight Consolidation (EWC)
from ewc import EWC

ewc = EWC(model, old_tasks_data)
loss = task_loss + ewc.penalty(model)
```

## 🔬 Evaluation Improvements

### 1. Automated Metrics

Create test set with ground truth:

```python
def evaluate_accuracy(model, test_set):
    correct = 0
    for item in test_set:
        pred = model.generate(item["question"])
        if pred == item["answer"]:
            correct += 1
    return correct / len(test_set)
```

### 2. Human Evaluation

Set up annotation interface:

```python
# Gradio interface for rating answers
def rate_answer(question, answer):
    rating = gr.Radio(["Excellent", "Good", "Poor"])
    # Collect ratings for analysis
```

### 3. A/B Testing

Compare base vs fine-tuned:

```python
def ab_test(questions):
    for q in questions:
        base_answer = base_model.generate(q)
        ft_answer = finetuned_model.generate(q)
        # Show both, collect preferences
```

## 💡 Creative Applications

### 1. Data Visualization Assistant

```
User: "Show me population by prefecture"
Model: Generates data + visualization code
```

### 2. Report Generation

```
User: "Create a summary of Tokyo demographics"
Model: Generates formatted report with stats
```

### 3. Trend Analysis

```
User: "What are the population trends?"
Model: Analyzes historical data and predicts
```

### 4. Policy Recommendations

```
User: "Which areas need more schools?"
Model: Analyzes population density + age distribution
```

## 🎯 Production Readiness

### 1. Model Versioning

```python
# Save with version tags
model.save_pretrained(f"/checkpoints/phi3-v{VERSION}")

# Track in metadata
metadata = {
    "version": "1.0.0",
    "training_steps": 1000,
    "dataset_size": 214148,
    "loss": 0.10,
    "timestamp": "2025-11-28"
}
```

### 2. Monitoring

```python
# Log predictions
def log_prediction(question, answer, latency):
    logger.info({
        "question": question,
        "answer": answer,
        "latency_ms": latency,
        "timestamp": now()
    })
```

### 3. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_answer(question):
    return model.generate(question)
```

### 4. Rate Limiting

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("10/minute")
def predict(question):
    return model.generate(question)
```

## 📚 Further Reading

- [Unsloth Documentation](https://github.com/unslothai/unsloth)
- [PEFT Library](https://github.com/huggingface/peft)
- [TRL (Transformer Reinforcement Learning)](https://github.com/huggingface/trl)
- [Modal Documentation](https://modal.com/docs)
- [Phi-3 Technical Report](https://arxiv.org/abs/2404.14219)

## 🤝 Contributing

Ideas for community contributions:
1. Add more data sources (labor statistics, economic indicators)
2. Implement evaluation benchmarks
3. Create UI/UX for non-technical users
4. Optimize for different hardware (CPU, smaller GPUs)
5. Multi-language support (English + Japanese)

---

**Questions or suggestions?** Open an issue or contribute to the project!
