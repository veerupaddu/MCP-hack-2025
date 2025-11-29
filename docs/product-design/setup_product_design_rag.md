# Setting Up RAG for Product Design Document

## Quick Start

### Step 1: Copy Product Design Document to Modal Volume

```bash
# Copy the filled product design document to your Modal volume
modal volume put mcp-hack-ins-products \
  docs/tokyo_auto_insurance_product_design_filled.md \
  docs/tokyo_auto_insurance_product_design.docx
```

### Step 2: Index the Document

```bash
# Index the product design document
modal run src/modal-rag-product-design.py::index_product_design
```

### Step 3: Query the Document

```bash
# Example queries
modal run src/modal-rag-product-design.py::query_product_design --question "What are the three product tiers and their premium ranges?"

modal run src/modal-rag-product-design.py::query_product_design --question "What is the Year 3 premium volume projection?"

modal run src/modal-rag-product-design.py::query_product_design --question "What coverage does the Standard tier include?"

modal run src/modal-rag-product-design.py::query_product_design --question "What are the key value propositions of TokyoDrive Insurance?"
```

## Example Questions You Can Ask

### Product Features
- "What are the three product tiers and their premium ranges?"
- "What coverage does the Standard tier include?"
- "What are the unique features of TokyoDrive Insurance?"
- "What add-on services are available?"

### Pricing & Financials
- "What is the Year 3 premium volume projection?"
- "What are the premium ranges for each tier?"
- "What discounts are available?"
- "What is the target loss ratio?"

### Market & Strategy
- "What is the target market size?"
- "Who are the main competitors?"
- "What are the key value propositions?"
- "What is the customer acquisition strategy?"

### Technical & Operations
- "What are the technology requirements?"
- "What is the claims processing workflow?"
- "What mobile app features are planned?"
- "How many repair shop partners are needed?"

### Compliance
- "What are the FSA licensing requirements?"
- "What is the minimum capital requirement?"
- "What data privacy requirements apply?"

## Integration with Existing RAG

The product design RAG uses a **separate collection** (`product_design`) in ChromaDB, so it won't interfere with your existing insurance products RAG.

You can:
1. Query product design separately
2. Query insurance products separately  
3. Combine both in a future unified query system

## Next Steps After RAG Setup

1. **Test with Real Questions**: Try asking questions your team would actually need
2. **Create Query Templates**: Build common queries for different use cases
3. **Integrate with Development**: Use RAG to extract requirements for development tickets
4. **Stakeholder Q&A**: Use for answering questions from investors, partners, etc.

