#!/usr/bin/env python3
"""
Launcher script for Hugging Face Spaces
This script changes to the mcp directory and runs the MCP server
"""
import sys
import os

# Add mcp directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp'))

# Change to mcp directory for relative imports
os.chdir(os.path.join(os.path.dirname(__file__), 'mcp'))

# Import and run the server
from mcp_server import create_gradio_interface, config

if __name__ == "__main__":
    print("🚀 Starting AI Development Agent MCP Server...")
    print(f"📍 Server URL: http://localhost:{config.MCP_PORT}")
    
    app = create_gradio_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
