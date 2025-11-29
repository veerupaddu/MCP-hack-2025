# Deployment Files

This directory contains files for deploying the RAG system to cloud platforms.

## Files

- **Dockerfile.rag** - Container for RAG service (GPU-enabled)
- **Dockerfile.web** - Container for web application
- **docker-compose.yml** - Orchestration for both services
- **requirements-web.txt** - Python dependencies for web app

## Quick Start

### Local Testing

```bash
# Build and run with docker-compose
docker-compose up --build

# Or build individually
docker build -f Dockerfile.rag -t rag-service .
docker build -f Dockerfile.web -t web-app .
```

### Nebius Deployment

See `docs/deployment/NEBIUS_DEPLOYMENT.md` for complete instructions.

## Environment Variables

### RAG Service
- `LLM_MODEL` - LLM model name (default: microsoft/Phi-3-mini-4k-instruct)
- `EMBEDDING_MODEL` - Embedding model name (default: BAAI/bge-small-en-v1.5)
- `CHROMA_PERSIST_DIR` - ChromaDB data directory (default: /data/chroma)
- `DOCUMENTS_DIR` - Documents directory (default: /data/documents)
- `PORT` - Service port (default: 8000)

### Web App
- `RAG_SERVICE_URL` - URL of RAG service (default: uses Modal CLI)
- `FLASK_APP` - Flask app file (default: src/web/web_app.py)

## Notes

- RAG service requires GPU (NVIDIA)
- Web app is lightweight and can run on CPU
- Use docker-compose for local development
- Follow platform-specific guides for production deployment

