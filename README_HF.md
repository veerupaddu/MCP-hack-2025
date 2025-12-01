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

# MCP SDLC Agent

AI-powered Software Development Lifecycle agent with JIRA integration, RAG capabilities, and fine-tuned model support.

## Features

- 🎯 **JIRA Integration**: Create epics, stories, tasks, and subtasks
- 🧠 **RAG System**: Query product design documents using retrieval-augmented generation
- 🔥 **Fine-tuned Models**: Specialized AI models for domain-specific queries
- 📊 **Mock Mode**: Works without JIRA credentials for demo purposes

## Configuration

This Space uses the following environment variables (configure in Settings → Repository secrets):

- `JIRA_URL`: Your JIRA instance URL (e.g., https://your-domain.atlassian.net)
- `JIRA_EMAIL`: Your JIRA email
- `JIRA_API_TOKEN`: Your JIRA API token
- `JIRA_PROJECT_KEY`: Default project key (e.g., SCRUM)
- `RAG_ENABLED`: Enable RAG system (true/false)
- `RAG_API_URL`: RAG API endpoint URL
- `FINETUNED_MODEL_API_URL`: Fine-tuned model API endpoint

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

## Links

- [GitHub Repository](https://github.com/your-username/mcp-hack)
- [Documentation](https://github.com/your-username/mcp-hack/docs)

