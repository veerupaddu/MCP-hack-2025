# RAG API Documentation

Fast API endpoint for querying the product design RAG system with <3 second response times.

## Quick Start

### Deploy the API

```bash
# Deploy to Modal
modal deploy src/rag/rag_api.py

# Get the URL
modal app list
```

### Use the API

```python
from src.rag.api_client import RAGAPIClient

client = RAGAPIClient(base_url="https://your-modal-url.modal.run")
result = client.query("What are the three product tiers?")
print(result['answer'])
```

## API Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "rag-api"
}
```

### Query

```http
POST /query
Content-Type: application/json

{
  "question": "What are the three product tiers?",
  "top_k": 5,
  "max_tokens": 1024
}
```

**Response:**
```json
{
  "answer": "The three product tiers are...",
  "retrieval_time": 0.45,
  "generation_time": 1.23,
  "total_time": 1.68,
  "sources": [
    {
      "content": "...",
      "metadata": {...}
    }
  ],
  "success": true
}
```

## Performance Optimization

### Target: <3 Second Responses

The API is optimized for fast responses:

1. **Warm Containers**: `min_containers=1` keeps a container ready
2. **Optimized LLM**: Reduced max_tokens (1024 vs 1536)
3. **Limited Context**: Top 3 documents, 800 chars each
4. **Prefix Caching**: Enabled for faster generation
5. **Concurrent Requests**: Up to 10 concurrent requests

### Response Time Breakdown

- **Retrieval**: 0.3-0.8 seconds
- **Generation**: 1.0-2.0 seconds
- **Total**: 1.5-3.0 seconds (target: <3s)

## Usage Examples

### Python Client

```python
from src.rag.api_client import RAGAPIClient

# Initialize
client = RAGAPIClient(base_url="https://your-api-url.modal.run")

# Health check
health = client.health_check()
print(health)

# Query
result = client.query("What are the premium ranges?")
print(result['answer'])

# Fast query (optimized for speed)
result = client.query_fast("What are the three tiers?")
print(result['answer'])
```

### cURL

```bash
# Health check
curl https://your-api-url.modal.run/health

# Query
curl -X POST https://your-api-url.modal.run/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the three product tiers?",
    "top_k": 5,
    "max_tokens": 1024
  }'
```

### JavaScript/TypeScript

```javascript
const response = await fetch('https://your-api-url.modal.run/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    question: 'What are the three product tiers?',
    top_k: 5,
    max_tokens: 1024
  })
});

const data = await response.json();
console.log(data.answer);
```

## Configuration

### Environment Variables

- `MODAL_APP_NAME`: App name (default: "insurance-rag-api")
- `MODAL_VOLUME_NAME`: Volume name (default: "mcp-hack-ins-products")

### API Parameters

- `question` (required): The question to ask
- `top_k` (optional, default: 5): Number of documents to retrieve
- `max_tokens` (optional, default: 1024): Maximum response length

## Performance Tips

1. **Use Fast Query**: For speed-critical applications, use `query_fast()` method
2. **Reduce top_k**: Lower `top_k` (e.g., 3) for faster retrieval
3. **Reduce max_tokens**: Lower `max_tokens` (e.g., 512) for faster generation
4. **Cache Results**: Cache common queries client-side
5. **Batch Requests**: If possible, batch multiple queries

## Error Handling

```python
result = client.query("your question")

if result.get("success"):
    print(result['answer'])
else:
    print(f"Error: {result.get('error', 'Unknown error')}")
```

## Monitoring

### Response Times

Monitor the `total_time` field in responses:
- < 2s: Excellent
- 2-3s: Good (target)
- > 3s: May need optimization

### Health Monitoring

```python
health = client.health_check()
if health.get("status") != "healthy":
    # Handle unhealthy state
    pass
```

## Deployment

### Modal Deployment

```bash
# Deploy
modal deploy src/rag/rag_api.py

# Get URL
modal app show insurance-rag-api
```

### Local Testing

```bash
# Run locally (for development)
modal serve src/rag/rag_api.py
```

## Rate Limiting

The API supports up to 10 concurrent requests. For higher throughput:
- Deploy multiple instances
- Use load balancer
- Implement client-side rate limiting

## Security

- Add authentication if needed
- Use HTTPS in production
- Implement rate limiting
- Validate input questions

## Troubleshooting

### Slow Responses (>3s)
- Check if container is warm (`min_containers=1`)
- Reduce `max_tokens`
- Reduce `top_k`
- Check network latency

### Errors
- Verify documents are indexed
- Check Modal app status
- Review error messages in response

