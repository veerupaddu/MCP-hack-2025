#!/usr/bin/env python3
"""Quick test to verify web app works"""
import requests
import time
import subprocess
import sys

print("🧪 Testing web app...")

# Start web app in background
print("Starting web app...")
proc = subprocess.Popen(
    [sys.executable, "web_app.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for server to start
time.sleep(3)

# Test health endpoint
try:
    response = requests.get("http://127.0.0.1:5001/health", timeout=5)
    if response.status_code == 200:
        print("✅ Health check passed!")
    else:
        print(f"❌ Health check failed: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# Clean up
proc.terminate()
proc.wait()

