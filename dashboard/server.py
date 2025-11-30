from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Optional
import uvicorn
import requests
import os

# ===== FastAPI App Setup =====
app = FastAPI(title="AI Development Agent API", version="1.0.0")

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Data Models =====
class RequirementInput(BaseModel):
    requirement: str

class WorkflowStatus(BaseModel):
    current_step: int
    steps: List[Dict]
    progress_percentage: int

# ===== Global State =====
class WorkflowState:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.current_step = 0
        self.requirement = ""
        self.activity_log = []
        self.modified_files = []
        self.workflow_running = False
        
    def reset(self):
        self.current_step = 0
        self.requirement = ""
        self.activity_log = []
        self.modified_files = []
        self.workflow_running = False

state = WorkflowState()

# ===== MCP Client Configuration =====
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:7860")

def call_mcp_rag(requirement: str) -> Dict:
    """Call MCP server RAG query function"""
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/api/predict",
            json={"data": [requirement], "fn_index": 0},  # RAG tab index
            timeout=30
        )
        if response.ok:
            result = response.json()
            return result.get("data", [{}])[0]
        return {"status": "error", "message": "MCP server error"}
    except Exception as e:
        print(f"MCP RAG error: {e}")
        return {"status": "error", "message": str(e)}

def call_mcp_finetuned(requirement: str, domain: str = "general") -> Dict:
    """Call MCP server fine-tuned model query function"""
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/api/predict",
            json={"data": [requirement, domain], "fn_index": 1},  # Fine-tuning tab index
            timeout=30
        )
        if response.ok:
            result = response.json()
            return result.get("data", [{}])[0]
        return {"status": "error", "message": "MCP server error"}
    except Exception as e:
        print(f"MCP Fine-tuned error: {e}")
        return {"status": "error", "message": str(e)}

def call_mcp_search_epics(keywords: str, threshold: float = 0.6) -> Dict:
    """Call MCP server JIRA epic search function"""
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/api/predict",
            json={"data": [keywords, threshold], "fn_index": 2},  # Search tab index
            timeout=30
        )
        if response.ok:
            result = response.json()
            return result.get("data", [{}])[0]
        return {"status": "error", "message": "MCP server error"}
    except Exception as e:
        print(f"MCP Search error: {e}")
        return {"status": "error", "message": str(e)}

def call_mcp_create_epic(summary: str, description: str, project_key: str = "PROJ") -> Dict:
    """Call MCP server JIRA epic creation function"""
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/api/predict",
            json={"data": [summary, description, project_key], "fn_index": 3},  # Create epic tab index
            timeout=30
        )
        if response.ok:
            result = response.json()
            return result.get("data", [{}])[0]
        return {"status": "error", "message": "MCP server error"}
    except Exception as e:
        print(f"MCP Create Epic error: {e}")
        return {"status": "error", "message": str(e)}

# ===== WebSocket Manager =====
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            if connection in self.active_connections:
                self.active_connections.remove(connection)

manager = ConnectionManager()

# ===== Helper Functions =====
async def send_log(message: str, level: str = "info"):
    """Send log message to all clients"""
    await manager.broadcast({
        "type": "log",
        "message": message,
        "level": level,
        "timestamp": datetime.now().isoformat()
    })
    state.activity_log.append({
        "message": message,
        "level": level,
        "timestamp": datetime.now().isoformat()
    })

async def update_step(step_id: int, status: str, details: str = "", message: str = ""):
    """Update workflow step status"""
    await manager.broadcast({
        "type": "step_update",
        "stepId": step_id,
        "status": status,
        "details": details,
        "message": message or f"Step {step_id}: {status}"
    })

async def call_mcp_create_user_story(epic_key: str, summary: str, description: str, story_points: int = None) -> Dict:
    """Call MCP server JIRA user story creation function"""
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/api/predict",
            json={"data": [epic_key, summary, description, story_points], "fn_index": 4},  # Create story tab index
            timeout=30
        )
        if response.ok:
            result = response.json()
            return result.get("data", [{}])[0]
        return {"status": "error", "message": "MCP server error"}
    except Exception as e:
        print(f"MCP Create Story error: {e}")
        return {"status": "error", "message": str(e)}

async def add_modified_file(path: str, status: str, stats: str = ""):
    """Add modified file to tracker"""
    await manager.broadcast({
        "type": "file_modified",
        "path": path,
        "status": status,
        "stats": stats
    })
    state.modified_files.append({
        "path": path,
        "status": status,
        "stats": stats
    })

# ===== Simulated Workflow =====
async def run_workflow(requirement: str):
    """Simulate the complete workflow"""
    state.workflow_running = True
    state.requirement = requirement
    
    try:
        # Step 1: Requirement Analysis
        await send_log("Starting requirement analysis...", "info")
        await update_step(1, "in-progress", "", "Analyzing requirement...")
        await asyncio.sleep(2)
        await update_step(1, "complete", "Analysis complete", "Requirement analyzed successfully")
        await send_log("Requirement analysis complete", "success")
        
        # Step 2: RAG & Fine-tuning Query
        await asyncio.sleep(1)
        await send_log("Querying RAG system via Gradio MCP...", "info")
        await update_step(2, "in-progress", "", "Querying RAG & fine-tuned models...")
        
        # Call MCP RAG
        rag_result = call_mcp_rag(requirement)
        if rag_result.get("status") == "success":
            spec = rag_result.get("specification", {})
            await send_log(f"RAG query successful - {spec.get('context_retrieved', 0)} contexts retrieved", "success")
        else:
            await send_log(f"RAG query failed: {rag_result.get('message', 'Unknown error')}", "warning")
            spec = {}
        
        # Call MCP Fine-tuned model (optional)
        ft_result = call_mcp_finetuned(requirement, domain="general")
        if ft_result.get("status") == "success":
            await send_log(f"Fine-tuned model query successful", "success")
        else:
            await send_log(f"Fine-tuned model query failed: {ft_result.get('message', 'Unknown error')}", "warning")
        
        # Generate epic summary from RAG results
        epic_summary = spec.get("title", "New Feature Implementation")
        epic_description = f"""
## Requirement
{requirement}

## Product Specification
{spec.get('summary', 'Generated from user requirement')}

## Features
{chr(10).join('- ' + f for f in spec.get('features', []))}

## Technical Requirements
{chr(10).join('- ' + t for t in spec.get('technical_requirements', []))}

## Acceptance Criteria
{chr(10).join('- ' + a for a in spec.get('acceptance_criteria', []))}

## Estimated Effort
{spec.get('estimated_effort', 'TBD')}
"""
        
        # Search for existing similar epics
        await send_log("Searching for existing JIRA epics...", "info")
        search_result = call_mcp_search_epics(epic_summary, threshold=0.7)
        
        existing_epics = search_result.get("epics", [])
        spec_id = "SPEC-2024-001"
        
        if existing_epics and len(existing_epics) > 0:
            # Found similar epic
            best_match = existing_epics[0]
            spec_id = best_match["key"]
            similarity = best_match.get("similarity_score", 0)
            await send_log(f"Found similar epic: {spec_id} (similarity: {similarity})", "info")
            await update_step(2, "in-progress", spec_id, f"Using existing epic: {spec_id}. Adding stories...")
        else:
            # Create new epic
            await send_log("No similar epics found. Creating new epic...", "info")
            create_result = call_mcp_create_epic(epic_summary, epic_description)
            
            if create_result.get("status") == "success":
                epic = create_result.get("epic", {})
                spec_id = epic.get("key", "SPEC-2024-001")
                await send_log(f"JIRA epic created: {spec_id}", "success")
            else:
                await send_log(f"Epic creation failed: {create_result.get('message', 'Unknown error')}", "error")
                spec_id = "SPEC-2024-001"  # Fallback
        
        # Add User Stories to Epic (Existing or New)
        features = spec.get("features", ["Core Implementation", "Testing"])
        await send_log(f"Adding {len(features)} user stories to epic {spec_id}...", "info")
        
        for i, feature in enumerate(features):
            story_summary = f"{feature}"
            story_desc = f"Implement {feature} as part of {epic_summary}"
            story_result = call_mcp_create_user_story(spec_id, story_summary, story_desc, story_points=3)
            
            if story_result.get("status") == "success":
                story_key = story_result.get("story", {}).get("key", "STORY-XXX")
                await send_log(f"Created story: {story_key} - {story_summary}", "success")
            else:
                await send_log(f"Failed to create story for {feature}", "warning")
            
            await asyncio.sleep(0.5) # Avoid rate limits
            
        await update_step(2, "complete", spec_id, f"Epic {spec_id} ready with {len(features)} stories")
        
        # Step 3: Git Branch Created
        await asyncio.sleep(1)
        await send_log("Creating Git branch...", "info")
        await update_step(3, "in-progress", "", "Creating feature branch...")
        await asyncio.sleep(1.5)
        branch_name = f"feature/{spec_id}-new-feature"
        await update_step(3, "complete", branch_name, f"Branch created: {branch_name}")
        await send_log(f"Git branch created: {branch_name}", "success")
        
        # Step 4: Code Generation
        await asyncio.sleep(1)
        await send_log("Generating code...", "info")
        await update_step(4, "in-progress", "", "Generating implementation files...")
        await asyncio.sleep(3)
        
        # Simulate file creation
        files = [
            ("src/agent/feature/main.py", "added", "+150 lines"),
            ("src/agent/feature/utils.py", "added", "+75 lines"),
            ("src/agent/feature/__init__.py", "added", "+10 lines"),
            ("tests/test_feature.py", "added", "+120 lines"),
        ]
        
        for file_path, status, stats in files:
            await add_modified_file(file_path, status, stats)
            await asyncio.sleep(0.5)
        
        await update_step(4, "complete", "4 files created", "Code generation complete")
        await send_log("Code generation complete - 4 files created", "success")
        
        # Step 5: Code Review
        await asyncio.sleep(1)
        await send_log("Running code review...", "info")
        await update_step(5, "in-progress", "", "Analyzing code quality...")
        await asyncio.sleep(2.5)
        await update_step(5, "complete", "No issues found", "Code review passed")
        await send_log("Code review passed - no issues found", "success")
        
        # Step 6: Git Commit
        await asyncio.sleep(1)
        await send_log("Committing changes...", "info")
        await update_step(6, "in-progress", "", "Staging and committing files...")
        await asyncio.sleep(1.5)
        commit_sha = "a1b2c3d"
        await update_step(6, "complete", commit_sha, f"Committed: {commit_sha}")
        await send_log(f"Changes committed: {commit_sha}", "success")
        
        # Step 7: Unit Testing
        await asyncio.sleep(1)
        await send_log("Running unit tests...", "info")
        await update_step(7, "in-progress", "", "Executing test suite...")
        await asyncio.sleep(3)
        await update_step(7, "complete", "15/15 passed (100%)", "All tests passed")
        await send_log("Unit tests passed: 15/15 (100% coverage)", "success")
        
        # Step 8: Manual Approval (waiting state)
        await asyncio.sleep(1)
        await send_log("Waiting for manual approval...", "info")
        await update_step(8, "in-progress", "", "Awaiting user approval...")
        await asyncio.sleep(2)
        await update_step(8, "complete", "Approved", "Changes approved")
        await send_log("Changes approved by user", "success")
        
        # Step 9: PR Submission
        await asyncio.sleep(1)
        await send_log("Creating pull request...", "info")
        await update_step(9, "in-progress", "", "Submitting PR...")
        await asyncio.sleep(2)
        pr_number = "#42"
        await update_step(9, "complete", pr_number, f"PR created: {pr_number}")
        await send_log(f"Pull request created: {pr_number}", "success")
        
        # Step 10: PR Merge & Notification
        await asyncio.sleep(1)
        await send_log("Merging pull request...", "info")
        await update_step(10, "in-progress", "", "Merging to main branch...")
        await asyncio.sleep(2)
        await update_step(10, "complete", "Merged", "PR merged successfully")
        await send_log("Pull request merged successfully!", "success")
        
        # Workflow complete
        await asyncio.sleep(1)
        await manager.broadcast({
            "type": "workflow_complete",
            "message": "Workflow completed successfully!",
            "summary": {
                "spec_id": spec_id,
                "branch": branch_name,
                "commit": commit_sha,
                "pr": pr_number,
                "files_modified": len(files)
            }
        })
        await send_log("🎉 Workflow completed successfully!", "success")
        
    except Exception as e:
        await send_log(f"Workflow error: {str(e)}", "error")
        await manager.broadcast({
            "type": "error",
            "message": str(e)
        })
    finally:
        state.workflow_running = False

# ===== API Endpoints =====
@app.get("/")
async def root():
    """Serve the main dashboard page"""
    return FileResponse("index.html")

@app.post("/api/submit-requirement")
async def submit_requirement(req: RequirementInput):
    """Submit a new requirement and start the workflow"""
    if state.workflow_running:
        raise HTTPException(status_code=400, detail="Workflow already running")
    
    if len(req.requirement) < 50:
        raise HTTPException(status_code=400, detail="Requirement too short (minimum 50 characters)")
    
    # Start workflow in background
    asyncio.create_task(run_workflow(req.requirement))
    
    return {
        "status": "success",
        "message": "Workflow started",
        "requirement": req.requirement
    }

@app.get("/api/workflow-status")
async def get_workflow_status():
    """Get current workflow status"""
    return {
        "workflow_running": state.workflow_running,
        "current_step": state.current_step,
        "requirement": state.requirement
    }

@app.get("/api/activity-log")
async def get_activity_log():
    """Get activity log"""
    return {
        "logs": state.activity_log[-50:]  # Last 50 entries
    }

@app.get("/api/modified-files")
async def get_modified_files():
    """Get list of modified files"""
    return {
        "files": state.modified_files
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            print(f"Received from client: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# ===== Static Files =====
# Mount static files (CSS, JS) after API routes
app.mount("/", StaticFiles(directory=".", html=True), name="static")

# ===== Main =====
if __name__ == "__main__":
    print("🚀 Starting AI Development Agent Dashboard Server...")
    print("📍 Dashboard: http://localhost:8000")
    print("🔌 WebSocket: ws://localhost:8000/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
