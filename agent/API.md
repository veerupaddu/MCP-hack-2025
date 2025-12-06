# User Story Agent API

## Overview
REST API endpoint for the User Story Agent that transforms user requirements into structured user stories.

## Starting the API Server

```bash
cd /Users/veeru/agents/mcp-hack
python agent/api.py
```

The API will start on **http://localhost:8001**

## API Documentation

Once the server is running, visit:
- **Interactive Docs (Swagger)**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## Endpoints

### 1. Root Information
```http
GET /
```

Returns API information and available endpoints.

**Response:**
```json
{
  "name": "User Story Agent API",
  "version": "1.0.0",
  "persona": "Alex",
  "role": "Senior Product Owner & Business Analyst",
  "endpoints": {
    "generate": "POST /api/user-stories",
    "generate_markdown": "POST /api/user-stories/markdown",
    "health": "GET /health"
  }
}
```

### 2. Health Check
```http
GET /health
```

Returns API health status.

### 3. Generate User Stories
```http
POST /api/user-stories
```

Generates structured user stories from a requirement.

**Request Body:**
```json
{
  "query": "I need a feature for customers to file auto insurance claims online",
  "use_rag": true,
  "use_finetuned": true
}
```

**Response:**
```json
{
  "success": true,
  "stories": [
    {
      "story_id": "US-001",
      "title": "Online Claims Filing",
      "actor": "customer",
      "action": "file auto insurance claims online",
      "benefit": "I can accomplish my task efficiently",
      "acceptance_criteria": [
        "GIVEN the customer is authenticated WHEN...",
        "GIVEN valid input is provided WHEN..."
      ],
      "story_points": 5,
      "priority": "High",
      "technical_notes": [
        "Implement input validation",
        "Add error handling"
      ]
    }
  ],
  "raw_query": "I need a feature...",
  "domain": "general",
  "mcp_source": "RAG + Fine-tuned",
  "confidence": 0.85,
  "warnings": []
}
```

### 4. Generate User Stories with Markdown
```http
POST /api/user-stories/markdown
```

Same as above, but includes a `markdown` field with formatted documentation.

## Usage Examples

### Using cURL

```bash
curl -X POST http://localhost:8001/api/user-stories \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I need a feature for customers to file auto insurance claims online",
    "use_rag": true,
    "use_finetuned": true
  }'
```

### Using Python requests

```python
import requests

response = requests.post(
    "http://localhost:8001/api/user-stories",
    json={
        "query": "I need a feature for customers to file auto insurance claims online",
        "use_rag": True,
        "use_finetuned": True
    }
)

data = response.json()
for story in data["stories"]:
    print(f"\n{story['story_id']}: {story['title']}")
    print(f"As a {story['actor']}, I want {story['action']}")
    print(f"Story Points: {story['story_points']}")
```

### Using JavaScript fetch

```javascript
fetch('http://localhost:8001/api/user-stories', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'I need a feature for customers to file auto insurance claims online',
    use_rag: true,
    use_finetuned: true
  })
})
.then(response => response.json())
.then(data => {
  console.log('User Stories:', data.stories);
});
```

## Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | The user requirement (min 10 characters) |
| `use_rag` | boolean | No | true | Query RAG for product context |
| `use_finetuned` | boolean | No | true | Query fine-tuned model for domain insights |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the request was successful |
| `stories` | array | List of generated user stories |
| `raw_query` | string | Original user query |
| `domain` | string | Detected domain |
| `mcp_source` | string | MCP sources used (e.g., "RAG + Fine-tuned") |
| `confidence` | float | Confidence score (0.0 to 1.0) |
| `warnings` | array | Any warnings or limitations |
| `markdown` | string | Formatted markdown (only in /markdown endpoint) |

## CORS

CORS is enabled for all origins, so you can call this API from any frontend application.

## Port Configuration

Default port: **8001**

To change the port, edit the `uvicorn.run()` call in `agent/api.py`:

```python
uvicorn.run(app, host="0.0.0.0", port=YOUR_PORT)
```

## Production Deployment

For production deployment, use a production ASGI server:

```bash
pip install uvicorn[standard]
uvicorn agent.api:app --host 0.0.0.0 --port 8001 --workers 4
```

Or with Gunicorn:

```bash
gunicorn agent.api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

## Error Handling

All errors return a standard HTTP error response:

```json
{
  "detail": "Error message here"
}
```

Common status codes:
- `200`: Success
- `422`: Validation error (invalid request)
- `500`: Internal server error
