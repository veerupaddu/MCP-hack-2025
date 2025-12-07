# 🚀 How to Run the AI Development Agent

This guide follows the logical data flow: **Backend (AI Models) → Middleware (MCP Server) → Frontend (Dashboard)**.

---

## 📋 Prerequisites

- **Python 3.10+** (Recommended: 3.11)
- **Modal Account** (for RAG & Fine-tuning)
- **JIRA Account** (optional, for integration)

---

## 🧠 Step 1: Deploy AI Backend (Modal)

First, we need to get the AI brains running.

### 1.1 Deploy Dual RAG System
The RAG system powers the document retrieval.

```bash
# 1. Index Existing Products (PDFs)
./venv/bin/modal run src/rag/rag_existing_products.py

# 2. Index Product Design (DOCX)
./venv/bin/modal run src/rag/rag_product_design.py

# 3. Deploy Query API
./venv/bin/modal deploy src/rag/rag_dual_query.py
```
> 📝 **Note the URL**: You'll get a URL ending in `...-fastapi-app.modal.run`. Save this!

### 1.2 Deploy Fine-Tuned Model (Optional)
For domain-specific insurance insights.

```bash
./venv/bin/modal deploy src/finetune/api_endpoint_vllm.py
```
> 📝 **Note the URL**: Save the URL ending in `...-model-ask.modal.run`.

---

## ⚙️ Step 2: Setup MCP Server (Middleware)

The MCP Server connects the AI models with JIRA and the frontend.

### 2.1 Configure Environment
Create `mcp/.env`:

```env
# JIRA (Optional)
JIRA_URL="https://your-domain.atlassian.net"
JIRA_EMAIL="your-email@example.com"
JIRA_API_TOKEN="your-api-token"
JIRA_PROJECT_KEY="PROJ"

# AI Backend URLs (From Step 1)
RAG_ENABLED="true"
RAG_API_URL="https://your-rag-url.modal.run"
FINETUNED_MODEL_API_URL="https://your-model-url.modal.run"
```

### 2.2 Run Server
```bash
cd mcp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python mcp_server.py
```
✅ **Running at**: `http://localhost:7860`

---

## 🖥️ Step 3: Run Dashboard (Frontend)

The user interface for interacting with the agent.

### 3.1 Run Dashboard
Open a new terminal:

```bash
cd dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```
✅ **Running at**: `http://localhost:8000`

---

## 🌐 Step 4: Access Application

1. Open **http://localhost:8000**
2. You're ready to go! 🚀

---

## ☁️ Deployment (Hugging Face)

To make your MCP Server public:

1. Create a Space on Hugging Face (SDK: Gradio)
2. Push your code:
   ```bash
   git remote add hf https://huggingface.co/spaces/ORG/SPACE_NAME
   git push hf main
   ```
3. Add Secrets in Space Settings:
   - `RAG_API_URL`
   - `JIRA_API_TOKEN`, etc.
