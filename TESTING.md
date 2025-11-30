# Testing Guide

## Quick Test

Run the automated test suite:
```bash
python tests/test_rag_system.py
```

Or with venv:
```bash
source venv/bin/activate
python tests/test_rag_system.py
```

## Manual Testing

### 1. Test Modal Connection
```bash
source venv/bin/activate
modal --version
```

Expected: Shows Modal version number

### 2. Test Indexing
```bash
source venv/bin/activate
python src/web/query_product_design.py --index
```

Expected:
- ✅ Loads Word/PDF/Excel files
- ✅ Creates embeddings
- ✅ Stores in ChromaDB
- ✅ Shows success message

**Time**: 2-5 minutes

### 3. Test Query (CLI)
```bash
source venv/bin/activate
python src/web/query_product_design.py --query "What are the three product tiers?"
```

Expected:
- ✅ Returns answer with product tier information
- ✅ Shows retrieval and generation times
- ✅ Lists sources

**Time**: 3-10 seconds (first query may be slower due to cold start)

### 4. Test Query (Interactive Mode)
```bash
source venv/bin/activate
python src/web/query_product_design.py --interactive
```

Then type questions like:
- "What are the three product tiers?"
- "What is the Year 3 premium volume?"
- "What coverage does the Standard tier include?"

### 5. Test Web Interface
```bash
source venv/bin/activate
python src/web/web_app.py
```

Then:
1. Open browser: `http://127.0.0.1:5000`
2. Enter a question
3. Click "Ask Question"
4. Verify answer appears

## Test Cases

### Product Information Queries
- ✅ "What are the three product tiers?"
- ✅ "What are the premium ranges for each tier?"
- ✅ "What coverage does the Standard tier include?"
- ✅ "What are the unique features of TokyoDrive Insurance?"

### Financial Queries
- ✅ "What is the Year 3 premium volume projection?"
- ✅ "What is the target loss ratio?"
- ✅ "What are the break-even projections?"

### Market & Strategy Queries
- ✅ "What is the target market size in Tokyo?"
- ✅ "Who are the main competitors?"
- ✅ "What are the key value propositions?"

### Compliance Queries
- ✅ "What are the FSA licensing requirements?"
- ✅ "What is the minimum capital requirement?"
- ✅ "What data privacy requirements apply?"

## Expected Behavior

### Successful Query
- Answer appears within 10-30 seconds
- Answer is relevant and accurate
- Sources are listed
- Timing information is shown

### Failed Query
- Clear error message
- Suggestion for fixing the issue
- No crash or hang

## Troubleshooting Tests

### "Modal command not found"
```bash
source venv/bin/activate
pip install modal
```

### "No documents found"
```bash
# Upload documents first
modal volume put mcp-hack-ins-products \
  docs/product-design/tokyo_auto_insurance_product_design.docx \
  docs/product-design/tokyo_auto_insurance_product_design.docx

# Then index
python src/web/query_product_design.py --index
```

### "Collection not found"
```bash
# Run indexing first
python src/web/query_product_design.py --index
```

### Slow queries
- First query: 10-30 seconds (cold start)
- Subsequent queries: 3-10 seconds (warm container)

## Performance Benchmarks

| Operation | Expected Time |
|-----------|--------------|
| Indexing (first time) | 2-5 minutes |
| Query (cold start) | 10-30 seconds |
| Query (warm) | 3-10 seconds |
| Web app startup | < 5 seconds |

## File Format Tests

### Should Work
- ✅ `.docx` files (Word)
- ✅ `.pdf` files (PDF)
- ✅ `.xlsx` files (Excel 2007+)
- ✅ `.xls` files (Excel 97-2003)

### Should Be Ignored
- ❌ `.md` files (markdown)
- ❌ `.txt` files
- ❌ `.csv` files
- ❌ Other formats

## Integration Tests

### End-to-End Test
1. Upload Word/PDF/Excel document
2. Index documents
3. Query via CLI
4. Query via web interface
5. Verify answers are consistent

### Error Handling Test
1. Query without indexing → Should show helpful error
2. Query with invalid question → Should handle gracefully
3. Network issues → Should show timeout/connection error

## Continuous Testing

For development, run tests after:
- Code changes
- Dependency updates
- Configuration changes
- Document updates

