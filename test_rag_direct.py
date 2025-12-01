#!/usr/bin/env python3
"""
Direct test of the RAG API to verify it's working correctly
"""
import requests
import json

RAG_API_URL = "https://mcp-hack--insurance-rag-api-fastapi-app.modal.run"

print("🧪 Testing RAG API Directly")
print(f"📍 Endpoint: {RAG_API_URL}")
print()

# Test 1: Health check
print("1️⃣ Testing health endpoint...")
try:
    response = requests.get(f"{RAG_API_URL}/health", timeout=10)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print("   ✅ Health check passed!")
except Exception as e:
    print(f"   ❌ Health check failed: {e}")
    exit(1)

print()

# Test 2: Query about MetLife
print("2️⃣ Testing RAG query about MetLife...")
print("   Question: 'What insurance products does MetLife offer?'")
print("   ⏱️  This may take 50-100 seconds on first query (cold start)...")
print()

try:
    response = requests.post(
        f"{RAG_API_URL}/query",
        json={
            "question": "What insurance products does MetLife offer?",
            "top_k": 5,
            "max_tokens": 512
        },
        timeout=120  # 2 minutes for cold start
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print()
        print("   ✅ Query successful!")
        print()
        print("   📊 Response:")
        print(f"      Answer: {result['answer'][:200]}...")
        print(f"      Retrieval time: {result['retrieval_time']:.2f}s")
        print(f"      Generation time: {result['generation_time']:.2f}s")
        print(f"      Total time: {result['total_time']:.2f}s")
        print(f"      Sources: {len(result['sources'])} documents")
        print()
        print("   📚 Source files:")
        for i, source in enumerate(result['sources'][:3], 1):
            src_file = source['metadata'].get('source', 'Unknown')
            print(f"      {i}. {src_file}")
        
        # Check if MetLife is mentioned
        if 'metlife' in result['answer'].lower() or any('metlife' in s['metadata'].get('source', '').lower() for s in result['sources']):
            print()
            print("   ✅ SUCCESS: MetLife information retrieved!")
        else:
            print()
            print("   ⚠️  WARNING: No MetLife information in response")
            print("      Sources retrieved:", [s['metadata'].get('source', '') for s in result['sources']])
    else:
        print(f"   ❌ Query failed: {response.text}")
        
except requests.exceptions.Timeout:
    print("   ⏱️  Timeout - Container is cold starting (this is normal)")
    print("      Try running this script again in 1-2 minutes")
except Exception as e:
    print(f"   ❌ Query failed: {e}")

print()
print("=" * 60)
print("Test complete!")
