# Quick Start: RAG API

Fast API endpoint for querying product design documents with <3 second response times.

## Deploy the API

```bash
# Deploy to Modal
modal deploy src/rag/rag_api.py

# Get the API URL
modal app show insurance-rag-api
```

## Use the API

### Python Client

```python
from src.rag.api_client import RAGAPIClient

# Initialize client
client = RAGAPIClient(base_url="https://your-api-url.modal.run")

# Query
result = client.query("What are the three product tiers?")
print(result['answer'])
print(f"Response time: {result['total_time']:.2f}s")
```

### cURL

```bash
curl -X POST https://your-api-url.modal.run/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the three product tiers?"}'
```

### JavaScript

```javascript
const response = await fetch('https://your-api-url.modal.run/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question: 'What are the three product tiers?' })
});

const data = await response.json();
console.log(data.answer);
```

## Test Performance

```bash
# Test with default URL
python tests/test_api.py

# Test with custom URL
python tests/test_api.py --url https://your-api-url.modal.run
```

## Performance Target

- **Target**: <3 seconds per query
- **Typical**: 1.5-2.5 seconds
- **Optimizations**: Warm containers, reduced tokens, limited context

## API Endpoints

- `GET /health` - Health check
- `POST /query` - Query the RAG system
- `GET /` - API information

See `docs/api/RAG_API.md` for full documentation.

