# 📁 Project Structure

Clean, simplified structure for the MCP SDLC Agent.

```
mcp-hack/
│
├── app.py                          # HuggingFace Spaces entry point
├── README.md                       # Main documentation
├── README_HF.md                    # HuggingFace specific readme
├── requirements.txt                # Root dependencies
│
├── mcp/                            # 🎯 MCP Server (Gradio/HuggingFace)
│   ├── mcp_server.py               # Main Gradio server with all tools
│   ├── requirements.txt            # MCP dependencies
│   └── .env.example                # Environment template
│
├── agent/                          # 🤖 User Story Agent
│   ├── api.py                      # FastAPI server (port 8001)
│   ├── user_story_agent.py         # Agent logic with RAG + LLM
│   ├── index.html                  # Web UI
│   └── API.md                      # API documentation
│
├── dashboard/                      # 📊 Dashboard UI
│   ├── server.py                   # Backend server (port 8000)
│   ├── index.html                  # Main dashboard
│   ├── app.js                      # Frontend logic
│   ├── style.css                   # Styling
│   └── requirements.txt            # Dashboard dependencies
│
├── src/
│   ├── rag/                        # 🧠 Dual RAG System
│   │   ├── rag_dual_query.py       # Query API (Modal deployment) ⭐
│   │   ├── rag_existing_products.py # Index insurance PDFs
│   │   ├── rag_product_design.py   # Index design DOCX/XLSX
│   │   └── README.md               # RAG documentation
│   │
│   └── finetune/                   # 🔥 Fine-tuning
│       ├── api_endpoint_vllm.py    # vLLM inference API ⭐
│       ├── finetune_modal.py       # Training script
│       ├── prepare_finetune_data.py # Dataset preparation
│       ├── eval_finetuned.py       # Model evaluation
│       └── merge_model.py          # LoRA merge utility
│
├── docs/                           # 📖 Documentation
│   ├── HOW_TO_RUN.md               # Complete setup guide
│   ├── QUICK_START.md              # Quick start guide
│   ├── STRUCTURE.md                # This file
│   └── product-design/             # Product design docs
│
└── diagrams/                       # 📐 Architecture diagrams
    ├── rag-finetune-system.svg     # System overview
    ├── 1-indexing-flow.svg         # RAG indexing flow
    ├── 2-query-flow.svg            # Query flow
    └── finetuning.svg              # Fine-tuning flow
```

## 🔧 Key Components

| Component | Port | Purpose |
|-----------|------|---------|
| `mcp/mcp_server.py` | 7860 | HuggingFace Gradio server |
| `agent/api.py` | 8001 | User Story Agent API |
| `dashboard/server.py` | 8000 | Dashboard backend |
| `src/rag/rag_dual_query.py` | Modal | Dual RAG query API |
| `src/finetune/api_endpoint_vllm.py` | Modal | Fine-tuned model API |

## 🚀 Deployment

### Modal (Cloud)
```bash
# RAG System
./venv/bin/modal deploy src/rag/rag_dual_query.py

# Fine-tuned Model
./venv/bin/modal deploy src/finetune/api_endpoint_vllm.py
```

### HuggingFace Spaces
Push to HuggingFace - `app.py` auto-starts on port 7860.

### Local Development
```bash
# Dashboard
python dashboard/server.py

# Agent API
python agent/api.py

# MCP Server
python mcp/mcp_server.py
```
