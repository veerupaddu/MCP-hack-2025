# Web Interface for Product Design Q&A

## Quick Start

### Start the Web Server

```bash
python3 web_app.py
```

Then open your browser to: **http://localhost:5000**

## Features

- 🎨 **Modern UI**: Clean, responsive design
- ⚡ **Fast Queries**: Direct integration with Modal RAG
- 📚 **Source Citations**: See which parts of the document were used
- 💡 **Suggested Questions**: Quick access to common queries
- ⏱️ **Performance Metrics**: See retrieval and generation times

## Usage

1. **Start the server**: `python3 web_app.py`
2. **Open browser**: Navigate to `http://localhost:5000`
3. **Ask questions**: Type your question and click "Ask Question"
4. **View results**: See answers with sources and timing info

## Example Questions

- "What are the three product tiers and their premium ranges?"
- "What is the Year 3 premium volume projection?"
- "What coverage does the Standard tier include?"
- "What are the FSA licensing requirements?"
- "What are the key value propositions?"

## Architecture

```
Browser (Frontend)
    ↓ HTTP POST
Flask Web App (web_app.py)
    ↓ Subprocess
Modal RAG System
    ↓ Query
ChromaDB + LLM
    ↓ Response
Flask Web App
    ↓ JSON
Browser (Display Results)
```

## Files

- `web_app.py` - Flask web server
- `templates/index.html` - Frontend HTML
- `static/css/style.css` - Styling
- `static/js/app.js` - Frontend JavaScript

## Troubleshooting

### Port Already in Use
```bash
# Use a different port
FLASK_RUN_PORT=5001 python3 web_app.py
```

### Modal Not Found
- Make sure venv is activated or Modal is in PATH
- The web app auto-detects Modal in venv

### Slow Queries
- First query: 10-15 seconds (cold start)
- Subsequent queries: 3-5 seconds

## Customization

### Change Port
Edit `web_app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change 5000 to 5001
```

### Change Styling
Edit `static/css/style.css`

### Add More Suggestions
Edit `templates/index.html` - add more chips in the suggestions section

