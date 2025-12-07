---
title: MCP SDLC Agent
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
license: mit
---

# 🤖 AI Development Agent MCP Server

AI-powered Software Development Lifecycle agent with JIRA integration, dual RAG system, and fine-tuned model support for insurance product design.

## 📁 Project Structure

```
mcp-hack/
├── app.py                    # HuggingFace Spaces entry point
├── mcp/                      # MCP Server (Gradio)
│   └── mcp_server.py
├── agent/                    # User Story Agent
│   ├── api.py, user_story_agent.py
│   └── index.html
├── dashboard/                # Dashboard UI
│   ├── server.py
│   └── index.html, app.js, style.css
├── src/
│   ├── rag/                  # Dual RAG System
│   │   ├── rag_dual_query.py        # Query API ⭐
│   │   ├── rag_existing_products.py # PDF indexer
│   │   └── rag_product_design.py    # DOCX indexer
│   └── finetune/             # Fine-tuning
│       ├── api_endpoint_vllm.py     # Inference API ⭐
│       └── finetune_modal.py
├── docs/                     # Documentation
└── diagrams/                 # Architecture diagrams
```

## ✨ Features

- **🎯 JIRA Integration**: Create and search epics, create user stories
- **🧠 Dual RAG System**: Query both existing products (PDFs) and new product design (DOCX)
- **🔥 Fine-tuned Models**: Specialized AI for insurance product design
- **📊 Mock Mode**: Works without credentials for demonstration

## 🔧 Configuration

Configure in **Settings → Repository secrets**:

### JIRA (Optional)
- `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY`

### Dual RAG System
- `RAG_ENABLED=true`
- `RAG_API_URL=https://mcp-hack--insurance-rag-dual-query-fastapi-app.modal.run`

### Fine-tuned Model
- `FINETUNED_MODEL_API_URL`: vLLM endpoint URL
- `FINETUNED_MODEL_TYPE=insurance`

## 🚀 Quick Start

```bash
# Deploy RAG (dual source)
./venv/bin/modal run src/rag/rag_existing_products.py
./venv/bin/modal run src/rag/rag_product_design.py
./venv/bin/modal deploy src/rag/rag_dual_query.py

# Deploy Fine-tuned Model
./venv/bin/modal deploy src/finetune/api_endpoint_vllm.py
```

## 📖 Tabs

- **RAG Query**: Query product specs from dual sources
- **Fine-tuned Model**: Insurance domain insights
- **JIRA**: Search/create epics and user stories
- **Configuration**: View current settings

## 🔗 Links

- [GitHub Repository](https://github.com/veerupaddu/MCP-hack-2025)
- [Documentation](docs/)

## 📝 License

MIT License
