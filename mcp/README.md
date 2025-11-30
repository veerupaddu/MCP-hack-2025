# AI Development Agent MCP Server

Gradio-based MCP server providing unified access to RAG, Fine-tuning, and JIRA systems.

## Features

- **RAG Query**: Query vector database for relevant context and product specifications
- **Fine-tuned Model Query**: Get domain-specific insights (insurance, finance, healthcare, etc.)
- **JIRA Integration**:
  - Search existing epics with similarity matching
  - Create new epics
  - Create user stories linked to epics
  - Automatic deduplication

## Quick Start

### Installation

```bash
cd mcp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Server

```bash
python mcp_server.py
```

Server will start on: **http://localhost:7860**

## Configuration

The server works in **mock mode** by default (no credentials needed). To enable real integrations:

### Environment Variables

```bash
# JIRA (optional - uses mock if not provided)
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
export JIRA_PROJECT_KEY="PROJ"

# RAG (optional)
export RAG_ENABLED="true"
export VECTOR_DB_PATH="./data/vectordb"

# Fine-tuned Model (optional)
export FINETUNED_MODEL_PATH="/path/to/your/model"
export FINETUNED_MODEL_TYPE="insurance"  # or finance, healthcare, etc.

# MCP Server
export MCP_PORT="7860"
```

### Using .env File

Create a `.env` file in the `mcp/` directory:

```bash
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJ
```

## API Functions

### RAG Query

```python
query_rag(requirement: str) -> Dict
```

Returns product specification with features, technical requirements, and acceptance criteria.

### Fine-tuned Model Query

```python
query_finetuned_model(requirement: str, domain: str = "general") -> Dict
```

Returns domain-specific insights and recommendations.

### Search JIRA Epics

```python
search_jira_epics(keywords: str, similarity_threshold: float = 0.6) -> Dict
```

Searches existing epics and returns matches with similarity scores.

### Create JIRA Epic

```python
create_jira_epic(summary: str, description: str, project_key: str = None) -> Dict
```

Creates a new JIRA epic and returns the epic key and URL.

### Create JIRA User Story

```python
create_jira_user_story(epic_key: str, summary: str, description: str, story_points: int = None) -> Dict
```

Creates a user story linked to an epic.

## Mock Mode

By default, the server runs in mock mode with:
- 3 pre-populated sample epics
- Simulated RAG responses
- Simulated fine-tuned model responses
- In-memory JIRA epic/story creation

This allows you to test the workflow without any external dependencies.

## Integration with Dashboard

The dashboard (`dashboard/server.py`) calls these MCP functions via HTTP requests to orchestrate the workflow.

## Troubleshooting

### Port Already in Use

```bash
# Change the port
export MCP_PORT="7861"
python mcp_server.py
```

### JIRA Authentication Errors

- Verify your JIRA URL (should include `https://`)
- Check API token is valid
- Ensure email matches your JIRA account

## Next Steps

1. **Test Mock Mode**: Run the server and test all functions via the Gradio UI
2. **Add Real JIRA**: Set environment variables for your JIRA instance
3. **Integrate RAG**: Connect your vector database
4. **Load Fine-tuned Model**: Point to your trained model

## License

Part of the MCP-hack-2025 project.
