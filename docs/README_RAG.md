# Product Design RAG System

## Quick Start

```bash
# 1. Index documents (one-time, takes 2-5 minutes)
python query_product_design.py --index

# 2. Query the document
python query_product_design.py --query "What are the three product tiers?"

# 3. Or use interactive mode
python query_product_design.py --interactive
```

## What You Can Ask

- Product features and tiers
- Pricing and financial projections
- Market analysis and strategy
- Technical requirements
- Compliance and regulatory info

See `docs/QUICK_START_RAG.md` for more examples.

## Files

- `src/modal-rag-product-design.py` - RAG system
- `query_product_design.py` - CLI interface
- `docs/QUICK_START_RAG.md` - Quick start guide
