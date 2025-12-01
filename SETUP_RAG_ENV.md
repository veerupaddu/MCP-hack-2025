# RAG Environment Setup Guide

## 🎯 Problem Identified

Your MCP app is not using the updated RAG API because the environment variables are not set!

**Current Status:**
- ❌ `RAG_ENABLED` is not set
- ❌ `RAG_API_URL` is not set
- ❌ App is using MOCK data instead of real RAG

---

## ✅ Solution: Set Environment Variables

### Option 1: Local Testing (Terminal)

```bash
# Set environment variables
export RAG_ENABLED=true
export RAG_API_URL=https://mcp-hack--insurance-rag-api-fastapi-app.modal.run

# Run your app
python3 app.py
```

### Option 2: Create .env File

Create a `.env` file in the project root:

```bash
# .env
RAG_ENABLED=true
RAG_API_URL=https://mcp-hack--insurance-rag-api-fastapi-app.modal.run
```

Then load it before running:

```bash
# Load .env and run
export $(cat .env | xargs) && python3 app.py
```

### Option 3: HuggingFace Spaces (Production)

1. Go to your HuggingFace Space settings
2. Navigate to "Settings" → "Repository secrets"
3. Add these secrets:
   - `RAG_ENABLED` = `true`
   - `RAG_API_URL` = `https://mcp-hack--insurance-rag-api-fastapi-app.modal.run`

---

## 🧪 Quick Test

```bash
# Set env vars and test
export RAG_ENABLED=true
export RAG_API_URL=https://mcp-hack--insurance-rag-api-fastapi-app.modal.run

# Run app
python3 app.py
```

Then ask: **"What insurance products does MetLife offer?"**

---

## 🔍 Verify It's Working

When RAG is properly configured, you should see in the logs:

```
🧠 RAG System: Enabled
[RAG] Calling remote endpoint: https://mcp-hack--insurance-rag-api-fastapi-app.modal.run
```

And the response should contain **actual MetLife information** from the PDFs, not generic knowledge.

---

## ⚠️ Common Issues

### Issue 1: Still Getting Mock Data

**Cause**: Environment variables not set  
**Fix**: Run `export RAG_ENABLED=true` before starting app

### Issue 2: "Connection refused" or timeout

**Cause**: Modal container is cold starting  
**Fix**: Wait 50-100 seconds for first query (normal)

### Issue 3: Still seeing TokyoDrive

**Cause**: Using old/cached endpoint  
**Fix**: Ensure `RAG_API_URL` points to the correct Modal endpoint

---

## 📊 Current Deployment

**API Endpoint:**
```
https://mcp-hack--insurance-rag-api-fastapi-app.modal.run
```

**Status:** ✅ Deployed and ready

**Data Available:**
- MetLife: 2,944 chunks (8 PDFs)
- Japan Post: 569 chunks (1 PDF)
- Sonpo: 155 chunks (6 PDFs)
- AIG: 98 chunks (4 PDFs)

**Total:** 3,766 chunks from 19 PDFs

---

## ✅ Complete Setup Command

```bash
# One-liner to set everything up and run
export RAG_ENABLED=true && \
export RAG_API_URL=https://mcp-hack--insurance-rag-api-fastapi-app.modal.run && \
python3 app.py
```

---

**After setting these variables, your app will use the REAL RAG system with actual MetLife data!**
