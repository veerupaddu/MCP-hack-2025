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

AI-powered Software Development Lifecycle agent with JIRA integration, RAG capabilities, and fine-tuned model support.

## ✨ Features

- **🎯 JIRA Integration**: Create and search epics, create user stories
- **🧠 RAG System**: Query product design documents using retrieval-augmented generation  
- **🔥 Fine-tuned Models**: Specialized AI models for domain-specific queries
- **📊 Mock Mode**: Works without credentials for demonstration

## 🔧 Configuration

This Space uses environment variables (configure in **Settings → Repository secrets**):

### JIRA Configuration (Optional - uses mock if not provided)
- `JIRA_URL`: Your JIRA instance URL (e.g., `https://your-domain.atlassian.net`)
- `JIRA_EMAIL`: Your JIRA email
- `JIRA_API_TOKEN`: Your JIRA API token ([How to get](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/))
- `JIRA_PROJECT_KEY`: Default project key (e.g., `SCRUM`)

### RAG System Configuration (Optional)
- `RAG_ENABLED`: Set to `true` to enable RAG system
- `RAG_API_URL`: RAG API endpoint URL (e.g., Modal deployment URL)

### Fine-tuned Model Configuration (Optional)
- `FINETUNED_MODEL_API_URL`: Fine-tuned model API endpoint
- `FINETUNED_MODEL_TYPE`: Model type (`general`, `insurance`, `finance`, etc.)

## 🚀 Usage

### Without Configuration (Mock Mode)
The app works out of the box in mock mode - perfect for testing and demos!

### With JIRA Integration
1. Go to **Settings** tab in your HuggingFace Space
2. Add the environment variables listed above
3. Restart the Space
4. You'll now have real JIRA integration!

### With RAG System
1. Deploy your RAG system (e.g., using Modal)
2. Get the API endpoint URL
3. Set `RAG_ENABLED=true` and `RAG_API_URL=<your-url>`
4. Restart the Space

## 📖 Tabs

- **RAG Query**: Query product specifications from documents
- **Fine-tuned Model**: Get domain-specific insights
- **JIRA - Search Epics**: Find existing epics by keywords
- **JIRA - Create Epic**: Create new epics
- **JIRA - Create User Story**: Create user stories under epics
- **Configuration**: View current configuration

## 🔗 Links

- [GitHub Repository](https://github.com/veerupaddu/MCP-hack-2025)
- [Documentation](https://github.com/veerupaddu/MCP-hack-2025/tree/main/docs)

## 📝 License

MIT License
