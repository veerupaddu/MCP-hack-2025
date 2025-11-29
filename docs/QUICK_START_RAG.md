# Quick Start: Product Design RAG

## Setup (One-Time)

### Step 1: Copy Documents to Modal Volume

```bash
# Documents should already be uploaded, but if needed:
modal volume put mcp-hack-ins-products \
  docs/tokyo_auto_insurance_product_design_filled.md \
  docs/tokyo_auto_insurance_product_design.docx
```

### Step 2: Index the Documents

```bash
# Option A: Using the CLI tool (auto-detects venv)
python3 query_product_design.py --index

# Option B: Using helper script (activates venv automatically)
./run_with_venv.sh --index

# Option C: Activate venv first, then run
source venv/bin/activate
python query_product_design.py --index

# Option D: Direct Modal command (if venv is activated)
modal run src/modal-rag-product-design.py::index_product_design
```

This will:
- Load the markdown and Word documents
- Split them into chunks
- Generate embeddings
- Store in ChromaDB collection `product_design`

**Expected time**: 2-5 minutes

## Querying

### Option 1: Interactive Mode (Recommended)

```bash
python query_product_design.py --interactive
```

Then type your questions:
```
❓ Your question: What are the three product tiers?
❓ Your question: What is the Year 3 premium volume?
❓ Your question: exit
```

### Option 2: Single Query

```bash
python query_product_design.py --query "What are the three product tiers and their premium ranges?"
```

### Option 3: Direct Modal Command

```bash
modal run src/modal-rag-product-design.py::query_product_design \
  --question "What coverage does the Standard tier include?"
```

## Example Questions

### Product Features
```bash
python query_product_design.py --query "What are the three product tiers and their premium ranges?"
python query_product_design.py --query "What coverage does the Standard tier include?"
python query_product_design.py --query "What are the unique features of TokyoDrive Insurance?"
python query_product_design.py --query "What add-on services are available?"
```

### Financial Projections
```bash
python query_product_design.py --query "What is the Year 3 premium volume projection?"
python query_product_design.py --query "What is the target loss ratio for Year 2?"
python query_product_design.py --query "What are the break-even projections?"
```

### Market & Strategy
```bash
python query_product_design.py --query "What is the target market size in Tokyo?"
python query_product_design.py --query "Who are the main competitors?"
python query_product_design.py --query "What are the key value propositions?"
```

### Technical Requirements
```bash
python query_product_design.py --query "What are the technology requirements?"
python query_product_design.py --query "What is the claims processing workflow?"
python query_product_design.py --query "What mobile app features are planned?"
```

### Compliance
```bash
python query_product_design.py --query "What are the FSA licensing requirements?"
python query_product_design.py --query "What is the minimum capital requirement?"
python query_product_design.py --query "What data privacy requirements apply?"
```

## Troubleshooting

### "No documents found"
- Make sure documents are in the Modal volume
- Check: `modal volume list mcp-hack-ins-products`

### "Collection not found"
- Run indexing first: `python query_product_design.py --index`

### Slow queries
- First query may be slow (cold start)
- Subsequent queries should be faster (warm container)

## Next Steps

1. **Test with your questions**: Try asking questions your team would actually need
2. **Create query templates**: Build common queries for different use cases
3. **Integrate with workflows**: Use RAG to extract requirements for development tickets
4. **Share with team**: Let stakeholders query the document themselves

