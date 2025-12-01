#!/usr/bin/env python3
"""
Launcher script for Hugging Face Spaces
"""
import sys
import os

# Add mcp directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp'))

# Change to mcp directory
os.chdir(os.path.join(os.path.dirname(__file__), 'mcp'))

# Import and run
from mcp_server import create_gradio_interface

if __name__ == "__main__":
    app = create_gradio_interface()
    # Launch with explicit server settings for HuggingFace Spaces
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

