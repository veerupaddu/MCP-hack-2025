#!/usr/bin/env python3
"""
Test script for the RAG system
Tests indexing and querying functionality
"""

import subprocess
import sys
import time
from pathlib import Path

def find_modal_command():
    """Find the modal command"""
    script_dir = Path(__file__).parent.parent
    venv_modal = script_dir / "venv" / "bin" / "modal"
    
    if venv_modal.exists():
        return [str(venv_modal)]
    
    import shutil
    modal_path = shutil.which("modal")
    if modal_path:
        return ["modal"]
    
    return [sys.executable, "-m", "modal"]

def test_modal_connection():
    """Test if Modal is accessible"""
    print("🔍 Testing Modal connection...")
    modal_cmd = find_modal_command()
    
    try:
        result = subprocess.run(
            modal_cmd + ["--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ Modal found: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Modal version check failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Modal command not found!")
        print("   Install with: pip install modal")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_indexing():
    """Test document indexing"""
    print("\n📚 Testing document indexing...")
    modal_cmd = find_modal_command()
    
    try:
        print("   Running indexing (this may take 2-5 minutes)...")
        result = subprocess.run(
            modal_cmd + [
                "run",
                "src/rag/modal-rag-product-design.py::index_product_design"
            ],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        if result.returncode == 0:
            output = result.stdout
            if "✅" in output or "success" in output.lower():
                print("✅ Indexing completed successfully!")
                return True
            else:
                print("⚠️ Indexing completed but output unclear:")
                print(output[:500])
                return False
        else:
            print(f"❌ Indexing failed:")
            print(result.stderr[:500])
            return False
    except subprocess.TimeoutExpired:
        print("❌ Indexing timed out (took more than 10 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error during indexing: {e}")
        return False

def test_query(question="What are the three product tiers?"):
    """Test a query"""
    print(f"\n❓ Testing query: '{question}'")
    modal_cmd = find_modal_command()
    
    try:
        print("   Sending query (this may take 10-30 seconds)...")
        start_time = time.time()
        result = subprocess.run(
            modal_cmd + [
                "run",
                "src/rag/modal-rag-product-design.py::query_product_design",
                "--question", question
            ],
            capture_output=True,
            text=True,
            timeout=180  # 3 minutes
        )
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            output = result.stdout
            if "Answer:" in output or "📝 Answer:" in output:
                print(f"✅ Query successful! (took {elapsed:.1f}s)")
                # Show a preview of the answer
                answer_start = output.find("Answer:") or output.find("📝 Answer:")
                if answer_start != -1:
                    answer_preview = output[answer_start:answer_start+200]
                    print(f"   Preview: {answer_preview[:150]}...")
                return True
            else:
                print("⚠️ Query completed but no answer found in output")
                print(output[:300])
                return False
        else:
            print(f"❌ Query failed:")
            print(result.stderr[:500])
            return False
    except subprocess.TimeoutExpired:
        print("❌ Query timed out (took more than 3 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error during query: {e}")
        return False

def test_web_app():
    """Test if web app can start"""
    print("\n🌐 Testing web app...")
    
    try:
        # Try importing Flask
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "web"))
        from web_app import app
        print("✅ Web app imports successfully")
        print("   Start with: python src/web/web_app.py")
        return True
    except ImportError as e:
        print(f"❌ Web app import failed: {e}")
        print("   Install dependencies: pip install flask flask-cors")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("="*70)
    print("🧪 RAG System Test Suite")
    print("="*70)
    
    results = {}
    
    # Test 1: Modal connection
    results['modal_connection'] = test_modal_connection()
    
    if not results['modal_connection']:
        print("\n⚠️  Modal not available. Skipping RAG tests.")
        print("   Install Modal: pip install modal")
        print("   Or activate venv: source venv/bin/activate")
        return
    
    # Test 2: Web app
    results['web_app'] = test_web_app()
    
    # Test 3: Indexing (optional - can skip if already indexed)
    print("\n" + "="*70)
    print("Indexing test (optional - skip if already indexed)")
    print("="*70)
    response = input("Run indexing test? (y/n, default=n): ").strip().lower()
    if response == 'y':
        results['indexing'] = test_indexing()
    else:
        print("⏭️  Skipping indexing test")
        results['indexing'] = None
    
    # Test 4: Query (requires indexing)
    if results.get('indexing') is not False:
        print("\n" + "="*70)
        print("Query test")
        print("="*70)
        results['query'] = test_query()
    else:
        print("\n⏭️  Skipping query test (indexing failed)")
        results['query'] = None
    
    # Summary
    print("\n" + "="*70)
    print("📊 Test Results Summary")
    print("="*70)
    
    for test_name, result in results.items():
        if result is True:
            print(f"✅ {test_name.replace('_', ' ').title()}: PASSED")
        elif result is False:
            print(f"❌ {test_name.replace('_', ' ').title()}: FAILED")
        else:
            print(f"⏭️  {test_name.replace('_', ' ').title()}: SKIPPED")
    
    print("\n" + "="*70)
    
    # Overall status
    passed = sum(1 for r in results.values() if r is True)
    total = sum(1 for r in results.values() if r is not None)
    
    if passed == total and total > 0:
        print("🎉 All tests passed!")
    elif passed > 0:
        print(f"⚠️  {passed}/{total} tests passed")
    else:
        print("❌ No tests passed")

if __name__ == "__main__":
    main()

