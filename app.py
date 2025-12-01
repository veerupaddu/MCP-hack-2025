#!/usr/bin/env python3
"""
Launcher script for Hugging Face Spaces
"""
import sys
import os

# Add mcp directory to path
mcp_dir = os.path.join(os.path.dirname(__file__), 'mcp')
sys.path.insert(0, mcp_dir)

# Set working directory to mcp folder for relative imports
os.chdir(mcp_dir)

# Import and run
from mcp_server import create_gradio_interface

if __name__ == "__main__":
    print("🚀 Starting AI Development Agent MCP Server on HuggingFace Spaces...")
    print(f"📍 Server will be available on port 7860")
    
    # Check environment variables (HuggingFace Spaces secrets)
    jira_configured = bool(os.getenv("JIRA_URL"))
    rag_configured = os.getenv("RAG_ENABLED", "false").lower() == "true"
    ft_configured = bool(os.getenv("FINETUNED_MODEL_API_URL"))
    
    print(f"🔧 JIRA Mode: {'Real' if jira_configured else 'Mock (no credentials)'}")
    print(f"🧠 RAG System: {'Enabled' if rag_configured else 'Mock'}")
    print(f"🎯 Fine-tuned Model: {'Enabled' if ft_configured else 'Mock'}")
    
    # Create and launch the app
    app = create_gradio_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        # HuggingFace Spaces compatibility
        favicon_path=None
    )

