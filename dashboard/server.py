"""
AI Development Agent Dashboard Server
FastAPI + WebSocket server for workflow visualization
"""
import os
import sys
import json
import asyncio
import requests
import uvicorn
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ===== Configuration =====
class Config:
    """Centralized configuration for dashboard"""
    # MCP Server
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "https://veeru-c-sdlc-mcp.hf.space")
    
    # API Endpoints (Gradio 4.x format)
    API_ENDPOINT_RAG = os.getenv("API_ENDPOINT_RAG", "/call/query_rag")
    API_ENDPOINT_FINETUNED = os.getenv("API_ENDPOINT_FINETUNED", "/call/query_finetuned")
    API_ENDPOINT_SEARCH_EPICS = os.getenv("API_ENDPOINT_SEARCH_EPICS", "/call/search_jira_epics")
    API_ENDPOINT_CREATE_EPIC = os.getenv("API_ENDPOINT_CREATE_EPIC", "/call/create_jira_epic")
    API_ENDPOINT_CREATE_STORY = os.getenv("API_ENDPOINT_CREATE_STORY", "/call/create_jira_user_story")
    
    # Dashboard Server
    DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8000"))
    
    # Timeouts
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))

config = Config()

class WorkflowState:
    def __init__(self):
        self.workflow_running = False
        self.requirement = ""
        self.activity_log = []
        self.modified_files = []
        self.steps = []
        self.active_connections: List[WebSocket] = []

# ===== FastAPI App Setup =====
app = FastAPI(title="AI Development Agent Dashboard", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

state = WorkflowState()

# ===== Data Models =====
class RequirementInput(BaseModel):
    requirement: str

def call_mcp_rag(requirement: str) -> Dict:
    """Call MCP server RAG query function via Gradio 4.x API"""
    try:
        print(f"DEBUG: Calling RAG endpoint: {config.MCP_SERVER_URL}/call/query_rag")
        # Use fn_index=0 for RAG query (based on app.py order)
        response = requests.post(
            f"{config.MCP_SERVER_URL}/api/predict",
            json={"data": [requirement], "fn_index": 0},
            headers={"Content-Type": "application/json"},
            timeout=config.API_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        print(f"DEBUG: RAG initial response: {result}")
        
        data = result.get("data", [])
        if data:
            result_data = data[0]
            if isinstance(result_data, list):
                result_data = result_data[0] if result_data else {}
            if isinstance(result_data, dict):
                return result_data
            return {"status": "success", "data": result_data}
            
        return {"status": "error", "message": "No data returned"}
    except Exception as e:
        print(f"MCP RAG error: {e}")
        return {"status": "error", "message": str(e)}

def call_mcp_finetuned(requirement: str, domain: str = "general") -> Dict:
    """Call MCP server fine-tuned model query function via Gradio 4.x API"""
    try:
        # Use fn_index=1 for Fine-tuned query
        response = requests.post(
            f"{config.MCP_SERVER_URL}/api/predict",
            json={"data": [requirement, domain], "fn_index": 1},
            headers={"Content-Type": "application/json"},
            timeout=config.API_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        data = result.get("data", [])
        if data:
            result_data = data[0]
            if isinstance(result_data, list):
                result_data = result_data[0] if result_data else {}
            if isinstance(result_data, dict):
                return result_data
            return {"status": "success", "data": result_data}
            
        return {"status": "error", "message": "No data returned"}
    except Exception as e:
        print(f"MCP Fine-tuned error: {e}")
        return {"status": "error", "message": str(e)}

def call_mcp_search_epics(keywords: str, threshold: float = 0.6) -> Dict:
    """Call MCP server JIRA epic search function via Gradio 4.x API"""
    try:
        # Use fn_index=2 for Search Epics
        response = requests.post(
            f"{config.MCP_SERVER_URL}/api/predict",
            json={"data": [keywords, threshold], "fn_index": 2},
            headers={"Content-Type": "application/json"},
            timeout=config.API_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        data = result.get("data", [])
        if data:
            result_data = data[0]
            if isinstance(result_data, list):
                return {"status": "success", "epics": result_data}
            return result_data if isinstance(result_data, dict) else {"status": "error", "message": "Invalid response format"}
            
        return {"status": "error", "message": "No data returned"}
    except Exception as e:
        print(f"MCP Search error: {e}")
        return {"status": "error", "message": str(e)}

def call_mcp_create_epic(summary: str, description: str, project_key: str = "PROJ") -> Dict:
    """Call MCP server JIRA epic creation function via Gradio 4.x API"""
    try:
        # Use fn_index=3 for Create Epic
        response = requests.post(
            f"{config.MCP_SERVER_URL}/api/predict",
            json={"data": [summary, description, project_key], "fn_index": 3},
            headers={"Content-Type": "application/json"},
            timeout=config.API_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        data = result.get("data", [])
        if data:
            result_data = data[0]
            if isinstance(result_data, list):
                result_data = result_data[0] if result_data else {}
            if isinstance(result_data, dict):
                return result_data
            return {"status": "success", "data": result_data}
            
        return {"status": "error", "message": "No data returned"}
    except Exception as e:
        print(f"MCP Create Epic error: {e}")
        return {"status": "error", "message": str(e)}

def call_mcp_create_user_story(epic_key: str, summary: str, description: str, story_points: int = None) -> Dict:
    """Call MCP server JIRA user story creation function via Gradio 4.x API"""
    try:
        # Use fn_index=4 for Create Story
        response = requests.post(
            f"{config.MCP_SERVER_URL}/api/predict",
            json={"data": [epic_key, summary, description, story_points], "fn_index": 4},
            headers={"Content-Type": "application/json"},
            timeout=config.API_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        data = result.get("data", [])
        if data:
            result_data = data[0]
            if isinstance(result_data, list):
                result_data = result_data[0] if result_data else {}
            if isinstance(result_data, dict):
                return result_data
            return {"status": "success", "data": result_data}
            
        return {"status": "error", "message": "No data returned"}
    except Exception as e:
        print(f"MCP Create Story error: {e}")
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

async def update_step(step_id: int, status: str, details: str = "", message: str = "", data: dict = None):
    """Update workflow step status"""
    await manager.broadcast({
        "type": "step_update",
        "stepId": step_id,
        "status": status,
        "details": details,
        "message": message or f"Step {step_id}: {status}",
        "data": data
    })

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
        
        analysis_data = {
            "summary": "Requirement Analysis",
            "input_length": len(requirement),
            "complexity_score": "Medium",
            "key_entities": ["User", "System", "Database"],
            "detected_intent": "Feature Implementation"
        }
        await update_step(1, "complete", "Analysis complete", "Requirement analyzed successfully", data=analysis_data)
        await send_log("Requirement analysis complete", "success")
        
        # Step 2: RAG & Fine-tuning Query
        await asyncio.sleep(1)
        await send_log("Querying RAG system via Gradio MCP...", "info")
        await update_step(2, "in-progress", "", "Querying RAG & fine-tuned models...")
        
        # Call MCP RAG
        rag_result = call_mcp_rag(requirement)
        if rag_result.get("status") == "success":
            # Handle wrapped list response
            spec = rag_result.get("specification") or rag_result.get("data", {})
            if isinstance(spec, list):
                spec = spec[0] if spec else {}
            await send_log(f"RAG query successful - {spec.get('context_retrieved', 0) if isinstance(spec, dict) else 0} contexts retrieved", "success")
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
        epic_summary = spec.get("title", "New Feature Implementation") if isinstance(spec, dict) else "New Feature Implementation"
        epic_description = f"""
## Requirement
{requirement}

## Product Specification
{spec.get('summary', 'Generated from user requirement') if isinstance(spec, dict) else 'Generated from user requirement'}

## Features
{chr(10).join('- ' + f for f in spec.get('features', [])) if isinstance(spec, dict) else '- Core Implementation\n- Testing'}

## Technical Requirements
{chr(10).join('- ' + t for t in spec.get('technical_requirements', [])) if isinstance(spec, dict) else '- TBD'}

## Acceptance Criteria
{chr(10).join('- ' + a for a in spec.get('acceptance_criteria', [])) if isinstance(spec, dict) else '- TBD'}

## Estimated Effort
{spec.get('estimated_effort', 'TBD') if isinstance(spec, dict) else 'TBD'}
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
                # Stop workflow and show error
                error_msg = create_result.get('message', 'Unknown error')
                await send_log(f"Epic creation failed: {error_msg}", "error")
                await update_step(2, "error", "Failed", f"Epic creation failed")
                await manager.broadcast({
                    "type": "workflow_error",
                    "title": "JIRA Epic Creation Failed",
                    "message": error_msg,
                    "details": f"The workflow was stopped because the JIRA epic could not be created.\n\nError: {error_msg}\n\nPlease check your JIRA configuration (project key, permissions, etc.) and try again."
                })
                state.workflow_running = False
                return  # Stop workflow immediately
        
        # Add User Stories to Epic (Existing or New)
        features = spec.get("features", ["Core Implementation", "Testing"])
        await send_log(f"Adding {len(features)} user stories to epic {spec_id}...", "info")
        
        created_stories = []
        for i, feature in enumerate(features):
            story_summary = f"{feature}"
            story_desc = f"Implement {feature} as part of {epic_summary}"
            story_result = call_mcp_create_user_story(spec_id, story_summary, story_desc, story_points=3)
            
            if story_result.get("status") == "success":
                story_key = story_result.get("story", {}).get("key", "STORY-XXX")
                created_stories.append(story_key)
                await send_log(f"Created story: {story_key} - {story_summary}", "success")
            else:
                await send_log(f"Failed to create story for {feature}", "warning")
            
            await asyncio.sleep(0.5) # Avoid rate limits
            
        rag_step_data = {
            "rag_spec": spec,
            "jira_epic": spec_id,
            "created_stories": created_stories,
            "rag_status": rag_result.get("status"),
            "finetune_status": ft_result.get("status")
        }
        await update_step(2, "complete", spec_id, f"Epic {spec_id} ready with {len(features)} stories", data=rag_step_data)
        
        # Step 3: Git Branch Created
        await asyncio.sleep(1)
        await send_log("Creating Git branch...", "info")
        await update_step(3, "in-progress", "", "Creating feature branch...")
        await asyncio.sleep(1.5)
        branch_name = f"feature/{spec_id}-new-feature"
        
        git_data = {
            "branch": branch_name,
            "base_branch": "main",
            "repository": "mcp-hack-2025",
            "command": f"git checkout -b {branch_name}"
        }
        await update_step(3, "complete", branch_name, f"Branch created: {branch_name}", data=git_data)
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
        
        codegen_data = {
            "files_generated": [f[0] for f in files],
            "total_lines": 355,
            "model_used": "Claude 3.5 Sonnet",
            "generation_time": "3.2s"
        }
        await update_step(4, "complete", "4 files created", "Code generation complete", data=codegen_data)
        await send_log("Code generation complete - 4 files created", "success")
        
        # Step 5: Code Review
        await asyncio.sleep(1)
        await send_log("Running code review...", "info")
        await update_step(5, "in-progress", "", "Analyzing code quality...")
        await asyncio.sleep(2.5)
        
        review_data = {
            "status": "Passed",
            "issues_found": 0,
            "suggestions": 2,
            "linter_score": "10/10",
            "security_scan": "Clean"
        }
        await update_step(5, "complete", "No issues found", "Code review passed", data=review_data)
        await send_log("Code review passed - no issues found", "success")
        
        # Step 6: Git Commit
        await asyncio.sleep(1)
        await send_log("Committing changes...", "info")
        await update_step(6, "in-progress", "", "Staging and committing files...")
        await asyncio.sleep(1.5)
        commit_sha = "a1b2c3d"
        
        commit_data = {
            "hash": commit_sha,
            "message": f"feat({spec_id}): Implement new features based on requirements",
            "author": "AI Agent",
            "files_changed": 4
        }
        await update_step(6, "complete", commit_sha, f"Committed: {commit_sha}", data=commit_data)
        await send_log(f"Changes committed: {commit_sha}", "success")
        
        # Step 7: Unit Testing
        await asyncio.sleep(1)
        await send_log("Running unit tests...", "info")
        await update_step(7, "in-progress", "", "Executing test suite...")
        await asyncio.sleep(3)
        
        test_data = {
            "total_tests": 15,
            "passed": 15,
            "failed": 0,
            "coverage": "100%",
            "duration": "0.45s"
        }
        await update_step(7, "complete", "15/15 passed (100%)", "All tests passed", data=test_data)
        await send_log("Unit tests passed: 15/15 (100% coverage)", "success")
        
        # Step 8: Manual Approval (waiting state)
        await asyncio.sleep(1)
        await send_log("Waiting for manual approval...", "info")
        await update_step(8, "in-progress", "", "Awaiting user approval...")
        await asyncio.sleep(2)
        
        approval_data = {
            "approver": "User (Auto-approved for demo)",
            "timestamp": datetime.now().isoformat(),
            "comments": "Looks good!"
        }
        await update_step(8, "complete", "Approved", "Changes approved", data=approval_data)
        await send_log("Changes approved by user", "success")
        
        # Step 9: PR Submission
        await asyncio.sleep(1)
        await send_log("Creating pull request...", "info")
        await update_step(9, "in-progress", "", "Submitting PR...")
        await asyncio.sleep(2)
        pr_number = "#42"
        
        pr_data = {
            "pr_number": pr_number,
            "title": f"feat({spec_id}): New Feature Implementation",
            "description": epic_description,
            "reviewers": ["Senior Dev", "QA Lead"],
            "url": f"https://github.com/org/repo/pull/{pr_number.replace('#', '')}"
        }
        await update_step(9, "complete", pr_number, f"PR created: {pr_number}", data=pr_data)
        await send_log(f"Pull request created: {pr_number}", "success")
        
        # Step 10: PR Merge & Notification
        await asyncio.sleep(1)
        await send_log("Merging pull request...", "info")
        await update_step(10, "in-progress", "", "Merging to main branch...")
        await asyncio.sleep(2)
        
        merge_data = {
            "status": "Merged",
            "merged_by": "CI/CD Bot",
            "timestamp": datetime.now().isoformat()
        }
        await update_step(10, "complete", "Merged", "PR merged successfully", data=merge_data)
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
