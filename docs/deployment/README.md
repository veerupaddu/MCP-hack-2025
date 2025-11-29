# Deployment Guides

This directory contains deployment guides for different cloud platforms.

## Available Guides

- **[Nebius Deployment](./NEBIUS_DEPLOYMENT.md)** - Complete guide for deploying to Nebius cloud platform

## Quick Reference

### Current Setup (Modal)
- RAG inference: Modal GPU containers
- Vector DB: Remote ChromaDB on Modal
- Web app: Local Flask server

### Nebius Deployment
- RAG inference: Nebius GPU VM/Container
- Vector DB: Local ChromaDB or managed service
- Web app: Nebius VM or container

## Migration Path

1. **Read the deployment guide** for your target platform
2. **Create standalone RAG service** (remove Modal dependencies)
3. **Update web app** to use HTTP API instead of Modal CLI
4. **Deploy infrastructure** (VM/containers)
5. **Index documents** in new environment
6. **Test end-to-end**
7. **Switch traffic** from Modal to new platform

## Support

For deployment issues, see:
- Platform-specific deployment guide
- `docs/guides/TROUBLESHOOTING.md`
- Project README.md

