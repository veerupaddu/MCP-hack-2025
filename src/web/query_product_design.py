#!/usr/bin/env python3
"""
Simple CLI interface for querying the product design document via RAG
"""

import subprocess
import sys
import argparse
import os
import shutil
from pathlib import Path

def find_modal_command():
    """Find the modal command - check venv first, then PATH, then python -m modal"""
    script_dir = Path(__file__).parent
    
    # First priority: Check for venv/bin/modal (most common case)
    venv_modal = script_dir / "venv" / "bin" / "modal"
    if venv_modal.exists():
        return [str(venv_modal)]
    
    # Second priority: Check parent directory venv
    parent_venv_modal = script_dir.parent / "venv" / "bin" / "modal"
    if parent_venv_modal.exists():
        return [str(parent_venv_modal)]
    
    # Third priority: Check if modal is in PATH (might be activated venv)
    modal_path = shutil.which("modal")
    if modal_path:
        return ["modal"]
    
    # Fourth priority: Try python -m modal
    try:
        result = subprocess.run(
            [sys.executable, "-m", "modal", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return [sys.executable, "-m", "modal"]
    except:
        pass
    
    # Last resort: return "modal" and let it fail with helpful error
    return ["modal"]

def query(question: str):
    """Query the product design document"""
    print(f"\n{'='*70}")
    print(f"🤔 Question: {question}")
    print(f"{'='*70}\n")
    
    modal_cmd = find_modal_command()
    
    try:
        result = subprocess.run(
                modal_cmd + [
                    "run",
                    "src/rag/modal-rag-product-design.py::query_product_design",
                    "--question", question
                ],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
    except FileNotFoundError:
        print("❌ Error: Modal command not found!")
        print("\n💡 Solutions:")
        print("\n1. Activate your virtual environment:")
        print("   source venv/bin/activate")
        print("   python query_product_design.py --index")
        print("\n2. Or use the helper script:")
        print("   ./run_with_venv.sh --index")
        print("\n3. Or install Modal globally:")
        print("   pip3 install modal")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        sys.exit(1)

def index():
    """Index the product design documents"""
    print("\n🚀 Indexing product design documents...\n")
    
    modal_cmd = find_modal_command()
    
    try:
        result = subprocess.run(
            modal_cmd + ["run", "src/rag/modal-rag-product-design.py::index_product_design"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
    except FileNotFoundError:
        print("❌ Error: Modal command not found!")
        print("\n💡 Solutions:")
        print("\n1. Activate your virtual environment:")
        print("   source venv/bin/activate")
        print("   python query_product_design.py --index")
        print("\n2. Or use the helper script:")
        print("   ./run_with_venv.sh --index")
        print("\n3. Or install Modal globally:")
        print("   pip3 install modal")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        sys.exit(1)

def interactive():
    """Interactive query mode"""
    print("\n" + "="*70)
    print("📋 Product Design Document Query Interface")
    print("="*70)
    print("\nType your questions about the TokyoDrive Insurance product design.")
    print("Type 'exit' or 'quit' to exit.\n")
    
    while True:
        try:
            question = input("❓ Your question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            query(question)
            print("\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except EOFError:
            print("\n\n👋 Goodbye!\n")
            break

def main():
    parser = argparse.ArgumentParser(
        description="Query the TokyoDrive Insurance product design document",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index the documents first
  python query_product_design.py --index
  
  # Ask a single question
  python query_product_design.py --query "What are the three product tiers?"
  
  # Interactive mode
  python query_product_design.py --interactive
  
  # Example questions:
  - "What are the three product tiers and their premium ranges?"
  - "What is the Year 3 premium volume projection?"
  - "What coverage does the Standard tier include?"
  - "What are the FSA licensing requirements?"
        """
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Ask a single question"
    )
    
    parser.add_argument(
        "--index", "-i",
        action="store_true",
        help="Index the product design documents"
    )
    
    parser.add_argument(
        "--interactive", "-I",
        action="store_true",
        help="Start interactive query mode"
    )
    
    args = parser.parse_args()
    
    if args.index:
        index()
    elif args.query:
        query(args.query)
    elif args.interactive:
        interactive()
    else:
        parser.print_help()
        print("\n💡 Tip: Use --interactive for an interactive session")
        print("   Or use --query 'your question' for a single query")

if __name__ == "__main__":
    main()

