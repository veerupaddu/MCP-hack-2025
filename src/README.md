# Source Code Directory

This directory contains all application source code, organized by functionality.

## 📁 Directory Structure

```
src/
├── rag/              # RAG (Retrieval Augmented Generation) systems
├── web/              # Web application (Flask)
├── data/             # Data processing scripts
├── finetune/         # Model fine-tuning pipeline
└── tools/            # Utility tools and helpers
```

---

## 🤖 RAG Systems (`src/rag/`)

Retrieval Augmented Generation implementations for querying document collections using LLMs.

### Production Files

#### **`modal-rag-product-design.py`** ⭐ **PRIMARY**
- **Purpose**: Main RAG system for product design documents
- **Features**:
  - Supports Word (.docx), PDF (.pdf), and Excel (.xlsx/.xls) documents
  - Uses vLLM with Phi-3-mini-4k-instruct for fast inference
  - ChromaDB for vector storage
  - Modal GPU containers (A10G)
- **Usage**:
  ```bash
  # Index documents
  modal run src/rag/modal-rag-product-design.py::index_product_design
  
  # Query
  modal run src/rag/modal-rag-product-design.py::query_product_design --query "What are the product tiers?"
  ```
- **Data**: Reads from Modal volume `mcp-hack-ins-products`

#### **`rag_api.py`** ⭐ **API ENDPOINT**
- **Purpose**: FastAPI endpoint for RAG with <3s response time optimization
- **Features**:
  - Async FastAPI handlers
  - Optimized for sub-3 second responses
  - GPU memory optimization (85% utilization)
  - Warm container pool for instant responses
  - CORS enabled for web integration
- **Usage**:
  ```bash
  # Deploy API
  modal deploy src/rag/rag_api.py
  
  # Get URL
  modal app show insurance-rag-api
  ```
- **API Docs**: See `docs/api/RAG_API.md`

#### **`api_client.py`** 📡 **CLIENT LIBRARY**
- **Purpose**: Python client for interacting with the RAG API
- **Features**:
  - Simple interface: `RAGAPIClient(base_url).query(question)`
  - Response parsing and error handling
  - Type hints for better IDE support
- **Usage**:
  ```python
  from src.rag.api_client import RAGAPIClient
  
  client = RAGAPIClient(base_url="https://your-api-url.modal.run")
  result = client.query("What is the pricing structure?")
  print(result['answer'])
  ```

### Archived Files (Moved to `bkp/rag/`)

The following files have been moved to `bkp/rag/` to keep the active directory clean:

- **`modal-rag.py`** - Original RAG implementation (legacy)
- **`rag_vllm.py`** - Experimental vLLM-optimized RAG
- **`rag_service.py`** - Standalone Flask service for Nebius
- **`debug_chroma.py`** - ChromaDB inspection tool
- **`inspect_rag_docs.py`** - Document validation utility

**Note**: These files are preserved for reference but are not actively used in production. The current production system uses only `rag_api.py` and `modal-rag-product-design.py`.

---

## 🌐 Web Application (`src/web/`)

Flask-based web interface for querying the RAG system.

### Core Files

#### **`web_app.py`** 🌐 **MAIN SERVER**
- **Purpose**: Flask web server with RAG integration
- **Features**:
  - REST API endpoint: `POST /api/query`
  - Auto-detects Modal CLI or HTTP API
  - Dynamic port selection (5000-5009)
  - CORS enabled
  - Error handling and timeouts
- **Usage**:
  ```bash
  python src/web/web_app.py
  # Or use helper script:
  ./scripts/setup/start_web.sh
  ```
- **Access**: http://127.0.0.1:5000

#### **`query_product_design.py`** 💻 **CLI INTERFACE**
- **Purpose**: Command-line interface for RAG queries
- **Features**:
  - Interactive query mode
  - Index command for document ingestion
  - Auto-detects Modal installation
- **Usage**:
  ```bash
  # Index documents
  python src/web/query_product_design.py --index
  
  # Query
  python src/web/query_product_design.py --query "What are the coverage options?"
  ```

### Frontend Assets

#### **`templates/index.html`**
- **Purpose**: Web UI for RAG queries
- **Features**: Modern responsive design, query input, answer display, source citations

#### **`static/css/style.css`**
- **Purpose**: Styling for web interface
- **Features**: Modern UI, loading states, responsive design

#### **`static/js/app.js`**
- **Purpose**: Frontend JavaScript logic
- **Features**:
  - AJAX query submission
  - Loading states and progress indicators
  - Markdown to HTML conversion
  - Cancel button for long queries
  - Error handling

---

## 📊 Data Processing (`src/data/`)

Scripts for downloading, cleaning, and preparing datasets.

### Census Data

- **`download_census_modal.py`**: Download Japan census data via Modal (parallel)
- **`download_census_data.py`**: Legacy census downloader
- **`convert_census_to_csv.py`**: Convert census data to CSV format
- **`delete_census_csvs.py`**: Clean up census CSV files
- **`clear_census_volume.py`**: Clear census data from Modal volume

### Economy & Labor Data

- **`download_economy_labor_modal.py`**: Download economy/labor statistics via Modal
- **`convert_economy_labor_to_csv.py`**: Convert to CSV format
- **`prepare_economy_data.py`**: Prepare for fine-tuning

### Fine-tuning Data Preparation

- **`prepare_finetune_data.py`** ⭐ **MAIN PREP SCRIPT**
  - **Purpose**: Generate Q&A pairs for model fine-tuning
  - **Features**: CSV processing, data augmentation, train/val split
  - **Output**: `train.jsonl`, `val.jsonl`

### Utility Scripts

- **`cleanup_data.py`**: General data cleaning utilities
- **`remove_duplicate_csvs.py`**: Remove duplicate files
- **`fix_csv_filenames.py`**: Standardize filenames
- **`create_custom_qa.py`**: Generate custom Q&A pairs
- **`debug_parser.py`**: Debug data parsing issues

### Product Design Tools

- **`convert_to_word.py`**: Convert markdown to Word documents
- **`fill_product_design.py`**: Populate product design templates with data

---

## 🔥 Fine-tuning Pipeline (`src/finetune/`)

Scripts for training custom insurance models.

### Training & Evaluation

#### **`finetune_modal.py`** ⭐ **MAIN TRAINING**
- **Purpose**: Fine-tune Phi-3-mini on insurance data
- **Features**:
  - LoRA training (r=16, alpha=32)
  - QLoRA (4-bit quantization)
  - H200 GPU support
  - Automatic checkpoint saving
- **Usage**:
  ```bash
  modal run src/finetune/finetune_modal.py
  ```
- **Data**: Reads `train.jsonl`, `val.jsonl` from Modal volume
- **Output**: LoRA adapters saved to volume

#### **`merge_model.py`** 🔀 **MODEL MERGING**
- **Purpose**: Merge LoRA adapters with base model
- **Features**: Creates unified model for deployment
- **Usage**:
  ```bash
  modal run src/finetune/merge_model.py
  ```
- **Output**: `merged_model/` in Modal volume

#### **`eval_finetuned.py`** 📊 **EVALUATION**
- **Purpose**: Evaluate fine-tuned model on validation set
- **Features**: Perplexity, accuracy metrics, sample predictions
- **Usage**:
  ```bash
  modal run src/finetune/eval_finetuned.py
  ```

### Inference Endpoints

#### **`api_endpoint_vllm.py`** ⚡ **VLLM ENDPOINT**
- **Purpose**: Fast inference with fine-tuned model using vLLM
- **Features**:
  - Sub-second inference
  - Batch processing
  - GPU optimization
- **Usage**:
  ```bash
  modal deploy src/finetune/api_endpoint_vllm.py
  ```

#### **`api_endpoint.py`**
- **Purpose**: Standard inference endpoint (slower, more flexible)
- **Use Case**: When vLLM compatibility issues arise

### Data Preparation

#### **`prepare_finetune_data.py`**
- **Purpose**: Prepare training data for fine-tuning
- **Features**: Data validation, formatting, augmentation
- **Note**: Duplicate of `src/data/prepare_finetune_data.py`

---

## 🛠️ Tools & Utilities (`src/tools/`)

Miscellaneous tools and helper scripts.

### Model Testing

- **`ask_model.py`**: Interactive CLI for testing models
- **`eval_finetuned.py`**: Model evaluation utilities

### API Endpoints (Legacy)

- **`api_endpoint.py`**: Standard API endpoint
- **`api_endpoint_cpu.py`**: CPU-only inference endpoint

### Data Tools

- **`debug_list_csv.py`**: List and inspect CSV files
- **`fill_product_design.py`**: Product design template filler

### Fine-tuning Tools

- **`finetune_modal.py`**: Training script (duplicate)
- **`finetune_modal_simple.py`**: Simplified training script

---

## 🚀 Quick Start

### 1. RAG System (Product Design Queries)

```bash
# Index documents
modal run src/rag/modal-rag-product-design.py::index_product_design

# Query via CLI
python src/web/query_product_design.py --query "What are the product tiers?"

# Start web interface
python src/web/web_app.py
```

### 2. Deploy Fast API

```bash
# Deploy optimized API (<3s responses)
modal deploy src/rag/rag_api.py

# Get API URL
modal app show insurance-rag-api

# Test with client
python -c "
from src.rag.api_client import RAGAPIClient
client = RAGAPIClient('https://your-url.modal.run')
print(client.query('What is the pricing?'))
"
```

### 3. Fine-tune Model

```bash
# 1. Prepare data
modal run src/data/prepare_finetune_data.py

# 2. Train model
modal run src/finetune/finetune_modal.py

# 3. Merge adapters
modal run src/finetune/merge_model.py

# 4. Deploy inference
modal deploy src/finetune/api_endpoint_vllm.py
```

---

## 📚 Documentation

- **RAG System**: `docs/guides/QUICK_START_RAG.md`
- **API Reference**: `docs/api/RAG_API.md`
- **Fine-tuning**: `finetune/README.md`
- **Deployment**: `docs/deployment/NEBIUS_DEPLOYMENT.md`
- **Architecture**: `diagrams/rag-finetune-system.svg`

---

## 🔑 Key Technologies

- **Modal**: Serverless GPU infrastructure
- **vLLM**: Fast LLM inference engine
- **LangChain**: RAG framework
- **ChromaDB**: Vector database
- **Flask**: Web framework
- **HuggingFace**: Models and embeddings
- **LoRA/QLoRA**: Efficient fine-tuning

---

## 🎯 File Selection Guide

**Need to query documents?**
→ Use `src/rag/modal-rag-product-design.py`

**Need a fast API?**
→ Deploy `src/rag/rag_api.py`

**Need a web interface?**
→ Run `src/web/web_app.py`

**Need to fine-tune a model?**
→ Run `src/finetune/finetune_modal.py`

**Need to prepare data?**
→ Run `src/data/prepare_finetune_data.py`

**Need to deploy outside Modal?**
→ Use `src/rag/rag_service.py`

