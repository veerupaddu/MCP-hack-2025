#!/usr/bin/env python3
"""
Test the RAG API for <3 second response times
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.api_client import RAGAPIClient

def test_api_performance(api_url: str = "http://localhost:8000"):
    """Test API performance"""
    print("="*70)
    print("🧪 RAG API Performance Test")
    print("="*70)
    
    client = RAGAPIClient(base_url=api_url)
    
    # Test 1: Health check
    print("\n1. Health Check...")
    health = client.health_check()
    print(f"   Status: {health.get('status', 'unknown')}")
    
    if health.get("status") != "healthy":
        print("❌ API is not healthy. Make sure it's deployed and running.")
        return
    
    # Test 2: Performance test
    print("\n2. Performance Test (<3s target)...")
    test_questions = [
        "What are the three product tiers?",
        "What is the Year 3 premium volume?",
        "What coverage does the Standard tier include?",
    ]
    
    results = []
    for i, question in enumerate(test_questions, 1):
        print(f"\n   Query {i}: {question[:50]}...")
        start = time.time()
        result = client.query(question)
        elapsed = time.time() - start
        
        if result.get("success"):
            total_time = result.get("total_time", elapsed)
            retrieval = result.get("retrieval_time", 0)
            generation = result.get("generation_time", 0)
            
            status = "✅" if total_time < 3.0 else "⚠️"
            print(f"   {status} Total: {total_time:.2f}s (Retrieval: {retrieval:.2f}s, Generation: {generation:.2f}s)")
            
            if total_time < 3.0:
                print(f"   ✅ Meets <3s target!")
            else:
                print(f"   ⚠️  Exceeds 3s target by {total_time - 3.0:.2f}s")
            
            results.append({
                "question": question,
                "total_time": total_time,
                "retrieval_time": retrieval,
                "generation_time": generation,
                "success": True
            })
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            results.append({"success": False})
    
    # Summary
    print("\n" + "="*70)
    print("📊 Performance Summary")
    print("="*70)
    
    successful = [r for r in results if r.get("success")]
    if successful:
        avg_time = sum(r["total_time"] for r in successful) / len(successful)
        fastest = min(r["total_time"] for r in successful)
        slowest = max(r["total_time"] for r in successful)
        
        print(f"Average response time: {avg_time:.2f}s")
        print(f"Fastest: {fastest:.2f}s")
        print(f"Slowest: {slowest:.2f}s")
        print(f"Target: <3.0s")
        
        if avg_time < 3.0:
            print("\n🎉 API meets performance target!")
        else:
            print(f"\n⚠️  API exceeds target by {avg_time - 3.0:.2f}s on average")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test RAG API performance")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API URL (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    test_api_performance(args.url)

