#!/usr/bin/env python3
"""
Web interface for querying the product design document
"""

import sys
import os
from pathlib import Path

# Try to use venv Python if available
script_dir = Path(__file__).parent
venv_python = script_dir / "venv" / "bin" / "python3"
if venv_python.exists():
    # Add venv site-packages to path
    venv_site_packages = script_dir / "venv" / "lib" / "python3.13" / "site-packages"
    if not venv_site_packages.exists():
        # Try to find the actual Python version in venv
        import glob
        lib_dir = script_dir / "venv" / "lib"
        if lib_dir.exists():
            python_dirs = glob.glob(str(lib_dir / "python*"))
            if python_dirs:
                venv_site_packages = Path(python_dirs[0]) / "site-packages"
    
    if venv_site_packages.exists():
        sys.path.insert(0, str(venv_site_packages))

try:
    from flask import Flask, render_template, request, jsonify
except ImportError:
    print("❌ Flask not installed!")
    print("\n💡 Solutions:")
    print("\n1. Activate venv and install:")
    print("   source venv/bin/activate")
    print("   pip install flask flask-cors")
    print("\n2. Or install in system Python:")
    print("   pip3 install flask flask-cors")
    print("\n3. Or use the helper script:")
    print("   ./scripts/setup/start_web.sh")
    sys.exit(1)

import subprocess
import json
import re
import socket
import time

app = Flask(__name__, template_folder='templates', static_folder='static')

# Allow CORS if needed
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

def find_modal_command():
    """Find the modal command"""
    import shutil
    script_dir = Path(__file__).parent
    venv_modal = script_dir / "venv" / "bin" / "modal"
    if venv_modal.exists():
        return [str(venv_modal)]
    
    modal_path = shutil.which("modal")
    if modal_path:
        return ["modal"]
    
    return [sys.executable, "-m", "modal"]

def query_rag(question: str):
    """Query the RAG system via Modal"""
    modal_cmd = find_modal_command()
    
    try:
        # Increased timeout for Modal cold starts
        result = subprocess.run(
            modal_cmd + [
                "run",
                "src/rag/modal-rag-product-design.py::query_product_design",
                "--question", question
            ],
            capture_output=True,
            text=True,
            timeout=180,  # 3 minutes for cold start
            check=True
        )
        
        # Parse the output
        output = result.stdout
        
        # Extract answer - improved logic
        answer = ""
        
        # Try multiple patterns to find the answer
        answer_start = output.find("📝 Answer:")
        if answer_start == -1:
            answer_start = output.find("Answer:")
        if answer_start == -1:
            # Look for "To decide" or other common answer starters
            answer_start = output.find("To decide")
        if answer_start == -1:
            answer_start = output.find("Based on")
        
        if answer_start != -1:
            answer_section = output[answer_start:]
            # Find the end of answer (before Sources, timing, or separators)
            # Try multiple patterns to find the end
            answer_end = answer_section.find("📚 Sources")
            if answer_end == -1:
                answer_end = answer_section.find("============================================================")
            if answer_end == -1:
                answer_end = answer_section.find("⏱️  Retrieval:")
            if answer_end == -1:
                answer_end = answer_section.find("⏱️ Retrieval:")
            if answer_end == -1:
                # Look for double newline followed by timing or sources
                answer_end = answer_section.find("\n\n⏱️")
            if answer_end == -1:
                answer_end = answer_section.find("\n\n📚")
            if answer_end == -1:
                # Look for triple newline (likely end of answer)
                answer_end = answer_section.find("\n\n\n")
            
            if answer_end != -1:
                answer = answer_section[:answer_end]
            else:
                # If no clear end found, take everything up to a reasonable point
                # Look for common patterns that indicate end of answer
                lines = answer_section.split('\n')
                answer_lines = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    # Stop if we hit sources, timing, or separators
                    if line.startswith('📚') or line.startswith('⏱️') or '===' in line:
                        break
                    # Stop if we hit "Stopping app" or Modal messages
                    if 'Stopping app' in line or 'View run at' in line or 'modal.com' in line:
                        break
                    answer_lines.append(line)
                answer = '\n'.join(answer_lines)
            
            # Remove answer markers
            answer = answer.replace("📝 Answer:", "").replace("Answer:", "").strip()
        else:
            # Fallback: extract meaningful content before sources
            sources_pos = output.find("📚 Sources")
            if sources_pos != -1:
                answer = output[:sources_pos].strip()
            else:
                answer = output
        
        # Clean up the answer - remove markdown table syntax, extra whitespace
        # Remove markdown table separators and structure
        answer = re.sub(r'\|[\s\-:]+\|', '', answer)
        # Remove table row separators (lines that are mostly pipes)
        answer = re.sub(r'^\|[\s\|\-:]+\|?\s*$', '', answer, flags=re.MULTILINE)
        # Remove standalone pipe characters
        answer = re.sub(r'^\s*\|\s*$', '', answer, flags=re.MULTILINE)
        # Remove pipe characters from start/end of lines (but keep content)
        answer = re.sub(r'^\|\s*', '', answer, flags=re.MULTILINE)
        answer = re.sub(r'\s*\|$', '', answer, flags=re.MULTILINE)
        # Remove lines that are just separators
        answer = re.sub(r'^=+\s*$', '', answer, flags=re.MULTILINE)
        # Remove timing info if it got mixed in
        answer = re.sub(r'⏱️\s*Retrieval:.*', '', answer)
        answer = re.sub(r'⏱️\s*Generation:.*', '', answer)
        # Remove Modal app messages
        answer = re.sub(r'Stopping app.*', '', answer)
        answer = re.sub(r'View run at.*', '', answer)
        answer = re.sub(r'modal\.com.*', '', answer)
        # Clean up multiple spaces
        answer = re.sub(r' {3,}', ' ', answer)
        # Clean up multiple newlines (keep max 2)
        answer = re.sub(r'\n{3,}', '\n\n', answer)
        # Remove empty lines at start/end
        answer = answer.strip()
        
        # Extract timing info
        retrieval_time = None
        generation_time = None
        if "⏱️  Retrieval:" in output:
            try:
                retrieval_line = [l for l in output.split("\n") if "⏱️  Retrieval:" in l][0]
                retrieval_time = float(retrieval_line.split(":")[1].strip().replace("s", ""))
            except:
                pass
        
        if "⏱️  Generation:" in output:
            try:
                gen_line = [l for l in output.split("\n") if "⏱️  Generation:" in l][0]
                generation_time = float(gen_line.split(":")[1].strip().replace("s", ""))
            except:
                pass
        
        # Extract sources - improved parsing
        sources = []
        if "📚 Sources" in output:
            sources_section = output[output.find("📚 Sources"):]
            source_lines = sources_section.split("\n")[1:]  # Skip header
            
            current_source = {}
            for line in source_lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if this is a new source (starts with number)
                if line and line[0].isdigit() and ('.' in line[:3] or ')' in line[:3]):
                    if current_source and (current_source.get("path") or current_source.get("content")):
                        sources.append(current_source)
                    current_source = {"number": line.split('.')[0] if '.' in line else line.split(')')[0], "content": ""}
                elif "/insurance-data" in line or "tokyo_auto_insurance" in line.lower():
                    # This is likely a file path
                    path = line.replace("/insurance-data/", "").replace("docs/", "")
                    current_source["path"] = path
                elif line and current_source:
                    # This is content
                    # Skip if it's just separators or timing info
                    if "===" in line or "Retrieval:" in line or "Generation:" in line:
                        continue
                    # Clean up the content
                    clean_line = line.replace("|", "").strip()
                    if clean_line and len(clean_line) > 10:  # Only add substantial content
                        current_source["content"] += clean_line + " "
            
            # Add the last source
            if current_source and (current_source.get("path") or current_source.get("content")):
                sources.append(current_source)
            
            # Clean up source content
            for source in sources:
                if source.get("content"):
                    # Remove markdown table syntax
                    source["content"] = re.sub(r'\|[\s\-:]+\|', '', source["content"])
                    source["content"] = re.sub(r'\s+\|\s+', ' ', source["content"])
                    source["content"] = source["content"].strip()
                    # Limit length
                    if len(source["content"]) > 400:
                        source["content"] = source["content"][:400] + "..."
        
        return {
            "success": True,
            "answer": answer,
            "retrieval_time": retrieval_time,
            "generation_time": generation_time,
            "sources": sources[:5],  # Limit to 5 sources
            "raw_output": output
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Query timed out after 3 minutes. This might be due to Modal cold start (first query takes 10-15 seconds). Please try again - subsequent queries should be faster. If the problem persists, try a simpler question."
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": f"Error executing query: {e.stderr or str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

@app.route('/')
def index():
    """Main page"""
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error rendering template: {str(e)}", 500

@app.route('/api/query', methods=['POST'])
def api_query():
    """API endpoint for queries"""
    data = request.json
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({
            "success": False,
            "error": "Please provide a question"
        }), 400
    
    result = query_rag(question)
    return jsonify(result)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    # Check if Modal is available
    modal_cmd = find_modal_command()
    try:
        test_result = subprocess.run(
            modal_cmd + ["--version"],
            capture_output=True,
            timeout=5
        )
        if test_result.returncode != 0:
            print("⚠️  Warning: Modal command may not be working correctly")
    except:
        print("⚠️  Warning: Could not verify Modal installation")
    
    # Try to find an available port
    import socket
    port = 5000
    for p in range(5000, 5010):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', p))
        sock.close()
        if result != 0:
            port = p
            break
    
    print("\n" + "="*70)
    print("🚀 Starting Product Design RAG Web Interface")
    print("="*70)
    print(f"\n📋 Access the interface at:")
    print(f"   → http://127.0.0.1:{port}  ⭐ RECOMMENDED")
    print(f"   → http://localhost:{port}")
    print(f"\n💡 If you see 403 error, use 127.0.0.1 instead of localhost")
    print("💡 Press Ctrl+C to stop\n")
    
    # Run with explicit host and port, allow all origins
    # Using 127.0.0.1 is more reliable than localhost on some systems
    app.run(debug=True, host='127.0.0.1', port=port, threaded=True, use_reloader=False)

