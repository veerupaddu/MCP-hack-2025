#!/bin/bash

# Startup script for MCP server with RAG enabled

echo "🚀 Starting MCP Server with RAG enabled..."
echo ""

# Set environment variables
export RAG_ENABLED=true
export RAG_API_URL=https://mcp-hack--insurance-rag-api-fastapi-app.modal.run

# Display configuration
echo "🔧 Configuration:"
echo "   RAG_ENABLED: $RAG_ENABLED"
echo "   RAG_API_URL: $RAG_API_URL"
echo ""

# Navigate to mcp directory and run
cd "$(dirname "$0")/mcp"
echo "📂 Working directory: $(pwd)"
echo ""

echo "🎯 Starting Gradio interface..."
echo "   Access at: http://localhost:7860"
echo ""

python mcp_server.py
