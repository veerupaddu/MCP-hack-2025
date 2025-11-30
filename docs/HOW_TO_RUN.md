# 🚀 How to Run the AI Development Agent

This guide provides sequential instructions to set up and run all components of the AI Development Agent: the **MCP Server** (Backend/Integration Hub) and the **Web Dashboard** (Frontend).

---

## 📋 Prerequisites

- **Python 3.10+** (Recommended: 3.11 or 3.12)
  - *Note: Python 3.13 requires a specific fix for Gradio (included in instructions).*
- **JIRA Account** (for real integration)
- **Git**

---

## 🛠️ Step 1: Setup & Run MCP Server

The MCP Server is the core "brain" that handles RAG, Fine-tuning queries, and JIRA integration.

### 1. Navigate to directory
```bash
cd mcp
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt

# ⚠️ Python 3.13 Fix: If you are using Python 3.13, run this extra command:
pip install audioop-lts
```

### 4. Configure Environment
Create a `.env` file in the `mcp/` directory:
```bash
touch .env
```

Add your credentials to `.env`:
```env
# JIRA Configuration
JIRA_URL="https://your-domain.atlassian.net"
JIRA_EMAIL="your-email@example.com"
JIRA_API_TOKEN="your-api-token"
JIRA_PROJECT_KEY="PROJ"

# RAG Configuration
RAG_ENABLED="true"
# URL from Step 1.5 below
RAG_API_URL="https://your-modal-url.modal.run"
```

### 5. Start the Server
```bash
python mcp_server.py
```
✅ **Success**: You should see `Running on local URL: http://0.0.0.0:7860`

---

## 🚀 Step 1.5: Deploy RAG System (Optional)

To enable real RAG capabilities instead of mock data, deploy the RAG system on Modal.

### 1. Deploy the RAG App
```bash
cd ..  # Go back to root if in mcp/
./venv/bin/modal deploy src/rag/modal-rag-product-design.py
```

### 2. Get the URL
After deployment, you will see a URL ending in `...-api-query.modal.run`.
Copy this URL and add it to your `mcp/.env` file as `RAG_API_URL`.

---

## 🖥️ Step 2: Setup & Run Dashboard

The Dashboard is the user interface where you interact with the agent.

### 1. Open a new terminal and navigate
```bash
cd dashboard
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the Dashboard
```bash
python server.py
```
✅ **Success**: You should see `Uvicorn running on http://0.0.0.0:8000`

---

## 🌐 Step 3: Access the Application

1. Open your browser to **http://localhost:8000**
2. Enter a requirement (e.g., "Create a login page with 2FA")
3. Watch the agent analyze, query RAG, and create JIRA epics/stories!

---

## 🧠 Advanced: Fine-Tuning Pipeline

If you want to train your own domain-specific model, follow these steps.

### Dataset Generation Results (Reference)
- **Training Samples**: 201,651
- **Validation Samples**: 22,407
- **Total Dataset**: 224,058 high-quality QA pairs

### Step 1: Fine-Tune the Model
Run the fine-tuning job on Modal with H200 GPU:
```bash
cd /Users/veeru/agents/mcp-hack
./venv/bin/modal run --detach src/finetune/finetune_modal.py
```

### Step 2: Evaluate the Model
After training completes, test the model:
```bash
./venv/bin/modal run src/finetune/eval_finetuned.py
```

### Step 3: Deploy Inference API
**Option B: High-Performance vLLM Endpoint (Recommended)**
1. **Merge Model**:
   ```bash
   ./venv/bin/modal run src/finetune/merge_model.py
   ```
2. **Deploy vLLM Endpoint**:
   ```bash
   ./venv/bin/modal deploy src/finetune/api_endpoint_vllm.py
   ```

### Step 4: Test the API
```bash
curl -X POST https://YOUR-MODAL-URL/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the population of Tokyo?",
    "context": "Japan Census data"
  }'
```

### Troubleshooting Fine-Tuning
- **Logs**: `modal app logs mcp-hack::finetune-phi3-modal`
- **Volumes**: `modal volume list`

