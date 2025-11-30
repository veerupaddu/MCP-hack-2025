# RAG Indexing Configuration

## Overview

The RAG system indexes **only Word, PDF, and Excel files** containing product design information. **All markdown files are excluded** from indexing to keep the RAG focused on structured product documents.

## Currently Indexed Files

The system automatically indexes files that match these patterns:

1. **Word Documents (.docx):**
   - Files with `tokyo_auto_insurance` or `product_design` in the filename
   - Example: `tokyo_auto_insurance_product_design.docx`

2. **PDF Documents (.pdf):**
   - Files with `tokyo_auto_insurance` or `product_design` in the filename
   - Example: `tokyo_auto_insurance_product_design.pdf`

3. **Excel Spreadsheets (.xlsx, .xls):**
   - Files with `tokyo_auto_insurance` or `product_design` in the filename
   - Example: `tokyo_auto_insurance_product_design.xlsx`

## Excluded Files

The following files are **NOT indexed**:

- ❌ **All markdown files** (`.md`, `.markdown`) - completely excluded
- ❌ Guide files (e.g., `QUICK_START_RAG.md`, `PRODUCT_DECISION_GUIDE.md`)
- ❌ Setup guides (e.g., `setup_product_design_rag.md`)
- ❌ Troubleshooting guides
- ❌ Web interface guides
- ❌ Any other file types (`.txt`, `.csv`, `.json`, etc.)

## Files That Will Be Indexed

Based on the current repository structure:

✅ **Will be indexed (if uploaded to Modal volume):**
- `tokyo_auto_insurance_product_design.docx` (Word document)
- `tokyo_auto_insurance_product_design.pdf` (PDF document)
- `tokyo_auto_insurance_product_design.xlsx` (Excel spreadsheet)
- `tokyo_auto_insurance_product_design.xls` (Excel 97-2003)

❌ **Will NOT be indexed (all excluded):**
- `tokyo_auto_insurance_product_design.md` (markdown - excluded)
- `tokyo_auto_insurance_product_design_filled.md` (markdown - excluded)
- `QUICK_START_RAG.md` (markdown - excluded)
- `PRODUCT_DECISION_GUIDE.md` (markdown - excluded)
- `setup_product_design_rag.md` (markdown - excluded)
- `TROUBLESHOOTING.md` (markdown - excluded)
- `WEB_INTERFACE.md` (markdown - excluded)
- All other markdown and non-supported file types

## How to Add More Product Design Files

### Option 1: Use Supported File Formats
Convert your files to one of the supported formats:
- **Word**: `.docx` format
- **PDF**: `.pdf` format
- **Excel**: `.xlsx` or `.xls` format

**Important:** 
- The file must contain `tokyo_auto_insurance` **OR** `product_design` in the filename
- Markdown files (`.md`) are **not supported** and will be ignored

### Option 2: Update the Loader
Edit `src/rag/modal-rag-product-design.py` and modify the pattern matching:

```python
# Current pattern for PDF files (line ~81):
if 'tokyo_auto_insurance' in file_lower or 'product_design' in file_lower:
    pdf_files.append(full_path)

# To add more patterns, modify to:
if ('tokyo_auto_insurance' in file_lower or 
    'product_design' in file_lower or
    'your_custom_pattern' in file_lower):
    pdf_files.append(full_path)
```

**Note:** All markdown files are intentionally excluded. Only Word, PDF, and Excel files are processed.

## Uploading to Modal Volume

To index product design documents, upload **only Word, PDF, or Excel files** to the Modal volume:

```bash
# Upload Word document
modal volume put mcp-hack-ins-products \
  docs/product-design/tokyo_auto_insurance_product_design.docx \
  docs/product-design/tokyo_auto_insurance_product_design.docx

# Upload PDF document (if you have one)
modal volume put mcp-hack-ins-products \
  docs/product-design/tokyo_auto_insurance_product_design.pdf \
  docs/product-design/tokyo_auto_insurance_product_design.pdf

# Upload Excel spreadsheet (if you have one)
modal volume put mcp-hack-ins-products \
  docs/product-design/tokyo_auto_insurance_product_design.xlsx \
  docs/product-design/tokyo_auto_insurance_product_design.xlsx
```

**Important Notes:**
- ❌ **Do NOT upload markdown files** (`.md`) - they will be ignored
- ✅ Only `.docx`, `.pdf`, `.xlsx`, and `.xls` files are processed
- ✅ Files must contain `tokyo_auto_insurance` or `product_design` in the filename

## Re-indexing

After uploading new files, re-index:

```bash
# Using CLI
python src/web/query_product_design.py --index

# Or direct Modal command
modal run src/rag/modal-rag-product-design.py::index_product_design
```

## Benefits of Current Approach

By focusing only on Word, PDF, and Excel files:
- ✅ RAG answers are focused on structured product documents
- ✅ No confusion from markdown guide/instruction content
- ✅ Faster retrieval (smaller, more focused document set)
- ✅ More accurate product-related answers from official documents
- ✅ Better handling of tables and structured data (Excel, Word tables)
- ✅ Cleaner source citations
- ✅ Support for professional document formats

## Example Queries

With product design documents indexed, you can ask:

```
"What are the three product tiers and their premium ranges?"
"What is the Year 3 premium volume projection?"
"What are the FSA licensing requirements?"
"What coverage does the Standard tier include?"
"What is the target market size in Tokyo?"
"Who are the main competitors?"
```

The RAG system will retrieve relevant sections from the product design documents only, ensuring answers are focused on product information.

