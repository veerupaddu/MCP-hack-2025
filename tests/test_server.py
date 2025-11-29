#!/usr/bin/env python3
"""Test if the web server is accessible"""
import requests
import sys

port = 5001
if len(sys.argv) > 1:
    port = int(sys.argv[1])

urls = [
    f"http://127.0.0.1:{port}/",
    f"http://localhost:{port}/",
    f"http://127.0.0.1:{port}/health",
]

print(f"🧪 Testing web server on port {port}...\n")

for url in urls:
    try:
        response = requests.get(url, timeout=5)
        print(f"✅ {url}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Content length: {len(response.text)} bytes")
        print()
    except requests.exceptions.ConnectionError:
        print(f"❌ {url}")
        print(f"   Error: Connection refused (server not running)")
        print()
    except Exception as e:
        print(f"❌ {url}")
        print(f"   Error: {e}")
        print()

