# AI Development Agent Dashboard

A modern, real-time web dashboard for the AI-powered automated software development workflow system.

## 🎯 Features

- **Requirement Input**: Submit 3-5 sentence requirements to start the workflow
- **Real-time Progress Tracking**: Visual progress bar and step-by-step status updates
- **Activity Log**: Live streaming of workflow activities and events
- **File Modification Tracker**: Monitor all files created, modified, or deleted
- **WebSocket Integration**: Real-time updates without page refresh
- **Modern UI**: Beautiful dark theme with glassmorphism and smooth animations

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Navigate to the dashboard directory**:
   ```bash
   cd dashboard
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running Locally

1. **Start the FastAPI server**:
   ```bash
   python server.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:8000
   ```

3. **Start using the dashboard**:
   - Enter your requirement (minimum 50 characters)
   - Click "Start Workflow"
   - Watch the real-time progress!

## 📁 Project Structure

```
dashboard/
├── index.html          # Main HTML structure
├── style.css           # Modern CSS with glassmorphism
├── app.js              # Frontend JavaScript with WebSocket
├── server.py           # FastAPI backend server
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🔧 API Endpoints

### REST API

- `GET /` - Serve the dashboard
- `POST /api/submit-requirement` - Submit a new requirement
- `GET /api/workflow-status` - Get current workflow status
- `GET /api/activity-log` - Get activity log
- `GET /api/modified-files` - Get modified files list

### WebSocket

- `ws://localhost:8000/ws` - Real-time updates endpoint

## 🎨 Technology Stack

### Frontend
- **HTML5**: Semantic structure
- **CSS3**: Modern styling with:
  - Dark mode theme
  - Glassmorphism effects
  - Gradient backgrounds
  - Smooth animations
  - Responsive design
- **JavaScript**: Vanilla JS with:
  - WebSocket client
  - State management
  - Dynamic UI updates

### Backend
- **FastAPI**: Modern Python web framework
- **WebSockets**: Real-time bidirectional communication
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

## 🌐 Future Deployment (Nebius)

This dashboard is designed to be easily deployable to cloud platforms like Nebius. For production deployment:

1. **Update configuration**:
   - Set production WebSocket URL in `app.js`
   - Configure CORS settings in `server.py`
   - Set up environment variables

2. **Containerization** (optional):
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["python", "server.py"]
   ```

3. **Deploy to Nebius**:
   - Follow Nebius deployment documentation
   - Configure domain and SSL certificates
   - Set up monitoring and logging

## 🔄 Workflow Steps

The dashboard tracks these 10 workflow steps:

1. 📝 Requirement Analysis
2. 📋 JIRA Epic Created
3. 🌿 Git Branch Created
4. ⚡ Code Generation
5. 🔍 Code Review
6. 💾 Git Commit
7. 🧪 Unit Testing
8. ✋ Manual Approval
9. 🚀 PR Submission
10. 🎉 PR Merge & Notification

## 🐛 Troubleshooting

### WebSocket Connection Issues

If you see "Disconnected" status:
- Ensure the server is running on port 8000
- Check browser console for errors
- Verify firewall settings

### Port Already in Use

If port 8000 is busy:
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn server:app --port 8001
```

## 📝 Development

### Running in Development Mode

```bash
# Auto-reload on file changes
uvicorn server:app --reload --port 8000
```

### Testing WebSocket Connection

```javascript
// Open browser console and run:
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```

## 🤝 Contributing

This dashboard is part of the AI Development Agent project. To contribute:

1. Make your changes
2. Test locally
3. Submit a pull request

## 📄 License

Part of the MCP-hack-2025 project.

## 🎉 Acknowledgments

Built with ❤️ for automated software development workflows.

---

**Need help?** Check the main project documentation or open an issue.
