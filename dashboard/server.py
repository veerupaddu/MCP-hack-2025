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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
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

# LLM API Configuration
LLM_API_URL = os.getenv("LLM_API_URL", "https://your-modal-app--llm-inference-api-fastapi-app.modal.run")

class WorkflowState:
    def __init__(self):
        self.workflow_running = False
        self.paused = False
        self.confirmation_event = asyncio.Event()
        self.requirement = ""
        self.activity_log = []
        self.modified_files = []
        self.steps = []
        self.current_step = 0
        self.active_connections: List[WebSocket] = []
        self.step_data = {}  # Store data for each step to allow restarts
        self.workflow_task = None

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

# ===== Helper Functions =====
def normalize_list(value):
    """
    Normalize a value that might be a list or an object with numeric keys.
    Gradio sometimes serializes lists as {"0": "item1", "1": "item2", ...}
    """
    if isinstance(value, list):
        return value
    elif isinstance(value, dict):
        # Check if it's an object with numeric string keys
        try:
            # Sort by numeric key and extract values
            sorted_items = sorted(value.items(), key=lambda x: int(x[0]))
            return [item[1] for item in sorted_items]
        except (ValueError, TypeError):
            # Not numeric keys, return as-is
            return value
    return value

def call_mcp_rag(requirement: str) -> Dict:
    """Call RAG API directly (bypasses HF Space issues)"""
    # Direct Modal RAG API URL
    rag_api_url = os.getenv("RAG_API_URL", "https://mcp-hack--insurance-rag-api-fastapi-app.modal.run")
    
    try:
        print(f"DEBUG: Calling RAG API directly: {rag_api_url}")
        response = requests.post(
            f"{rag_api_url}/query",
            json={"question": requirement, "top_k": 3, "max_tokens": 256},
            timeout=30
        )
        
        if response.ok:
            result = response.json()
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            
            # Parse features from answer
            features = []
            for line in answer.split('\\n'):
                line = line.strip()
                if line.startswith(('-', '•', '*', '1.', '2.', '3.')) and len(line) > 3:
                    features.append(line.lstrip('-•*0123456789. '))
            
            if not features:
                features = ["Core functionality", "User interface", "Data management"]
            
            return {
                "status": "success",
                "specification": {
                    "title": "Product Specification (RAG Generated)",
                    "summary": answer[:200] + "..." if len(answer) > 200 else answer,
                    "features": features[:5],
                    "technical_requirements": ["Secure implementation", "Scalable architecture", "Error handling"],
                    "acceptance_criteria": ["Meets functional requirements", "Passes testing", "User-friendly"],
                    "estimated_effort": "2-3 weeks",
                    "full_answer": answer,
                    "context_retrieved": len(sources)
                },
                "source": "direct_rag_api"
            }
        else:
            print(f"DEBUG: RAG API error: {response.status_code}")
    except Exception as e:
        print(f"DEBUG: RAG API exception: {e}")
    
    # Fallback mock response
    return {
        "status": "success",
        "specification": {
            "title": "Feature Implementation Specification",
            "summary": f"Implementation for: {requirement[:100]}...",
            "features": ["Core functionality", "User interface", "Data management", "Error handling"],
            "technical_requirements": ["Secure implementation", "Scalable architecture"],
            "acceptance_criteria": ["Meets requirements", "Passes testing"],
            "estimated_effort": "2-4 weeks",
            "full_answer": requirement,
            "context_retrieved": 0
        },
        "source": "mock_fallback"
    }

def call_mcp_finetuned(requirement: str, domain: str = "general") -> Dict:
    """Call fine-tuned model API directly"""
    ft_api_url = os.getenv("FINETUNED_MODEL_API_URL", "https://mcp-hack--phi3-inference-vllm-model-ask.modal.run")
    
    try:
        print(f"DEBUG: Calling fine-tuned API: {ft_api_url}")
        response = requests.post(
            f"{ft_api_url}/ask",
            json={"question": requirement, "context": f"Domain: {domain}"},
            timeout=10
        )
        
        if response.ok:
            result = response.json()
            return {
                "status": "success",
                "insights": {
                    "domain": domain,
                    "recommendations": ["Follow best practices", "Ensure security", "Add testing"],
                    "full_response": result.get("answer", "")
                }
            }
    except Exception as e:
        print(f"DEBUG: Fine-tuned API error: {e}")
    
    # Fallback
    return {
        "status": "success",
        "insights": {
            "domain": domain,
            "recommendations": ["Follow security best practices", "Implement proper validation", "Add comprehensive testing"],
            "compliance_notes": ["Regular security audits recommended"]
        },
        "source": "mock_fallback"
    }

def call_mcp_search_epics(keywords: str, threshold: float = 0.6) -> Dict:
    """Search JIRA epics - returns empty to trigger new epic creation"""
    # Return empty to always create new epic (simpler flow)
    return {"status": "success", "epics": [], "count": 0}

def call_mcp_create_epic(summary: str, description: str, project_key: str = "SCRUM") -> Dict:
    """Create JIRA epic using mock data (HF Space unavailable)"""
    import random
    epic_id = random.randint(100, 999)
    epic_key = f"{project_key}-{epic_id}"
    
    return {
        "status": "success",
        "epic": {
            "key": epic_key,
            "summary": summary,
            "description": description[:200],
            "url": f"https://mock-jira.atlassian.net/browse/{epic_key}"
        },
        "source": "mock_jira"
    }

def call_mcp_create_user_story(epic_key: str, summary: str, description: str, story_points: int = None) -> Dict:
    """Create JIRA user story using mock data"""
    import random
    
    # Extract project key from epic key
    project_key = epic_key.split('-')[0] if '-' in epic_key else "SCRUM"
    story_id = random.randint(200, 999)
    story_key = f"{project_key}-{story_id}"
    
    return {
        "status": "success",
        "story": {
            "key": story_key,
            "summary": summary,
            "epic_key": epic_key,
            "story_points": story_points or 3,
            "url": f"https://mock-jira.atlassian.net/browse/{story_key}"
        },
        "source": "mock_jira"
    }

def call_llm_api(prompt: str, system_prompt: str = None, max_tokens: int = 256, temperature: float = 0.7) -> Dict:
    """Call the open-source LLM inference API on Modal"""
    try:
        print(f"DEBUG: Calling LLM API: {LLM_API_URL}")
        
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        if system_prompt:
            payload["system_prompt"] = system_prompt
        
        response = requests.post(
            f"{LLM_API_URL}/generate",
            json=payload,
            timeout=90  # Increased for cold starts
        )
        
        if response.ok:
            result = response.json()
            return {
                "status": "success",
                "text": result.get("text", ""),
                "model": result.get("model", "unknown"),
                "latency_ms": result.get("latency_ms", 0),
                "source": "llm_api"
            }
        else:
            print(f"DEBUG: LLM API error: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "message": f"API returned {response.status_code}",
                "source": "llm_api"
            }
    except requests.exceptions.Timeout:
        print("DEBUG: LLM API timeout")
        return {"status": "error", "message": "Request timeout", "source": "llm_api"}
    except Exception as e:
        print(f"DEBUG: LLM API exception: {e}")
        return {"status": "error", "message": str(e), "source": "llm_api"}

def generate_summary(requirement: str, llm_response: str = "") -> str:
    """Generate a 200-500 word summary based on requirement"""
    req_len = len(requirement)
    req_lower = requirement.lower()
    
    # Use LLM response if good
    if llm_response and len(llm_response) > 100:
        words = llm_response.strip().split()
        if len(words) > 500:
            return ' '.join(words[:500]) + '...'
        return llm_response.strip()
    
    # Build summary
    parts = ["This requirement describes a software feature that needs development."]
    
    # Feature type
    if 'login' in req_lower or 'auth' in req_lower:
        parts.append("The feature involves user authentication and access control. This includes secure login flows, session management, and potentially role-based permissions.")
    elif 'dashboard' in req_lower or 'report' in req_lower:
        parts.append("The feature focuses on data visualization and reporting. This requires aggregating data, creating visual components, and ensuring responsive design.")
    elif 'api' in req_lower or 'integration' in req_lower:
        parts.append("The feature requires API development and integration. This involves endpoint design, request validation, error handling, and documentation.")
    elif 'search' in req_lower or 'filter' in req_lower:
        parts.append("The feature involves search and filtering functionality. This requires efficient query design, indexing strategy, and user-friendly interface.")
    else:
        parts.append("The feature requires careful analysis of user needs and technical constraints to deliver a robust solution.")
    
    # Scope
    if req_len > 300:
        parts.append("Given the detailed requirements, this is a comprehensive feature with multiple components requiring careful planning and phased implementation.")
    elif req_len > 150:
        parts.append("The requirements outline a moderately scoped feature with clear objectives that can be delivered incrementally.")
    else:
        parts.append("The requirements describe a focused feature with specific goals suitable for rapid development.")
    
    parts.append("Implementation will require proper architecture design, database schema planning, and API endpoint definition. Testing should cover unit tests, integration tests, and user acceptance criteria.")
    
    return ' '.join(parts)

def estimate_complexity(requirement: str) -> Dict:
    """Estimate development complexity"""
    req_lower = requirement.lower()
    factors = []
    score = 0
    
    # Complexity indicators
    if any(w in req_lower for w in ['integration', 'api', 'third-party', 'external']):
        factors.append("External Integration")
        score += 2
    if any(w in req_lower for w in ['auth', 'login', 'security', 'permission', 'role']):
        factors.append("Security/Auth")
        score += 2
    if any(w in req_lower for w in ['real-time', 'websocket', 'notification', 'live']):
        factors.append("Real-time Features")
        score += 3
    if any(w in req_lower for w in ['report', 'analytics', 'dashboard', 'chart']):
        factors.append("Data Analytics")
        score += 2
    if any(w in req_lower for w in ['payment', 'transaction', 'billing']):
        factors.append("Payment Processing")
        score += 3
    if any(w in req_lower for w in ['search', 'filter', 'sort']):
        factors.append("Search/Filter")
        score += 1
    
    # Length-based
    if len(requirement) > 500:
        score += 2
    elif len(requirement) > 200:
        score += 1
    
    # Determine level
    if score >= 6:
        level, estimate = "High", "3-4 weeks"
    elif score >= 3:
        level, estimate = "Medium", "1-2 weeks"
    else:
        level, estimate = "Low", "3-5 days"
    
    if not factors:
        factors = ["Standard CRUD", "Basic UI"]
    
    return {"level": level, "estimate": estimate, "factors": factors[:5]}

def call_llm_chat(message: str, system_prompt: str = "You are a helpful AI assistant.", max_tokens: int = 256) -> Dict:
    """Call the LLM API chat endpoint"""
    try:
        response = requests.post(
            f"{LLM_API_URL}/chat",
            json={
                "message": message,
                "system_prompt": system_prompt,
                "max_tokens": max_tokens
            },
            timeout=90  # Increased for cold starts
        )
        
        if response.ok:
            result = response.json()
            return {
                "status": "success",
                "text": result.get("text", ""),
                "model": result.get("model", "unknown"),
                "latency_ms": result.get("latency_ms", 0),
                "source": "llm_chat"
            }
        else:
            return {"status": "error", "message": f"API returned {response.status_code}", "source": "llm_chat"}
    except Exception as e:
        print(f"DEBUG: LLM Chat exception: {e}")
        return {"status": "error", "message": str(e), "source": "llm_chat"}

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
    # Store data in state for restarts
    if data:
        state.step_data[step_id] = data
        
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

async def wait_for_confirmation(step_id: int, data: dict):
    """Wait for user confirmation before proceeding"""
    # Map step ID to message type for frontend
    msg_types = {
        1: "requirement_analyzed",
        2: "rag_completed",
        3: "git_branch_created",
        4: "code_generated",
        5: "code_reviewed",
        6: "git_committed",
        7: "unit_tested",
        8: "manual_approval_requested",
        9: "pr_submitted",
        10: "pr_merged"
    }
    
    msg_type = msg_types.get(step_id, "step_complete")
    
    # Send confirmation request
    await manager.broadcast({
        "type": msg_type,
        "stepId": step_id,
        "data": data
    })
    
    print(f"Waiting for confirmation for step {step_id}...")
    
    # Wait for event
    state.confirmation_event.clear()
    await state.confirmation_event.wait()
    
    # Check if we should continue
    if not state.workflow_running:
        raise asyncio.CancelledError("Workflow stopped")
    
    if state.paused:
        # If paused, we might want to wait again or exit
        # For now, let's treat pause as stop for the loop, but keep state
        raise asyncio.CancelledError("Workflow paused")

# ===== Simulated Workflow =====
async def execute_step(step_id: int):
    """Execute a single step of the workflow"""
    requirement = state.requirement
    
    if step_id == 1:
        # Step 1: Requirement Analysis using FM Inference
        await send_log("Starting requirement analysis using FM inference...", "info")
        await update_step(1, "in-progress", "", "Analyzing requirement with AI model...")
        
        # Call FM inference API for requirement analysis
        fm_api_url = os.getenv("FINETUNED_MODEL_API_URL", "https://mcp-hack--phi3-inference-vllm-model-ask.modal.run")
        
        analysis_prompt = f"""Analyze this software requirement and extract:
1. Key Actors (who will use this)
2. Main Requirements (what needs to be built)
3. Possible Actions (what users can do)
4. Technical Considerations

Requirement: {requirement}

Provide a structured analysis."""

        analysis_data = {
            "user_query": requirement,
            "summary": "",
            "complexity": {},
            "source": ""
        }
        
        try:
            response = requests.post(
                f"{fm_api_url}/ask",
                json={"question": analysis_prompt, "context": "Software requirement analysis"},
                timeout=15
            )
            
            if response.ok:
                result = response.json()
                answer = result.get("answer", "")
                
                # Generate summary and complexity
                analysis_data["summary"] = generate_summary(requirement, answer)
                analysis_data["complexity"] = estimate_complexity(requirement)
                analysis_data["source"] = "fm_inference"
                await send_log("FM inference analysis complete", "success")
            else:
                raise Exception(f"FM API returned {response.status_code}")
                
        except Exception as e:
            print(f"FM inference error: {e}")
            # Try LLM API as fallback
            await send_log("Trying LLM API fallback...", "info")
            llm_result = call_llm_api(
                prompt=analysis_prompt,
                system_prompt="You are a software requirements analyst. Provide structured analysis.",
                max_tokens=512,
                temperature=0.3
            )
            
            if llm_result.get("status") == "success":
                answer = llm_result.get("text", "")
                analysis_data["summary"] = generate_summary(requirement, answer)
                analysis_data["complexity"] = estimate_complexity(requirement)
                analysis_data["source"] = "llm_api"
                await send_log(f"LLM analysis complete ({llm_result.get('latency_ms', 0)}ms)", "success")
            else:
                # Final fallback - static analysis
                analysis_data["summary"] = generate_summary(requirement, "")
                analysis_data["complexity"] = estimate_complexity(requirement)
                analysis_data["source"] = "static"
                await send_log("Using static analysis", "warning")
        
        await update_step(1, "complete", "Analysis complete", "Requirement analyzed successfully", data=analysis_data)
        await send_log("Requirement analysis complete", "success")
        return analysis_data

    elif step_id == 2:
        # Step 2: RAG & Fine-tuning Query
        await send_log("Querying RAG system via Gradio MCP...", "info")
        await update_step(2, "in-progress", "", "Querying RAG & fine-tuned models...")
        
        # Call MCP RAG
        rag_result = call_mcp_rag(requirement)
        spec = {}
        if rag_result.get("status") == "success":
            spec = rag_result.get("specification") or rag_result.get("data", {})
            if isinstance(spec, list): spec = spec[0] if spec else {}
            if isinstance(spec, dict):
                spec["features"] = normalize_list(spec.get("features", []))
                spec["technical_requirements"] = normalize_list(spec.get("technical_requirements", []))
                spec["acceptance_criteria"] = normalize_list(spec.get("acceptance_criteria", []))
            await send_log(f"RAG query successful", "success")
        else:
            await send_log(f"RAG query failed: {rag_result.get('message', 'Unknown error')}", "warning")
        
        # Call MCP Fine-tuned model
        ft_result = call_mcp_finetuned(requirement, domain="general")
        
        # Generate epic details
        epic_summary = spec.get("title", "New Feature Implementation") if isinstance(spec, dict) else "New Feature Implementation"
        epic_description = f"Implementation of: {requirement}"
        
        # Search/Create Epic
        await send_log("Searching for existing JIRA epics...", "info")
        search_result = call_mcp_search_epics(epic_summary)
        existing_epics = search_result.get("epics", [])
        
        if existing_epics:
            spec_id = existing_epics[0]["key"]
            await send_log(f"Found similar epic: {spec_id}", "info")
        else:
            await send_log("Creating new epic...", "info")
            create_result = call_mcp_create_epic(epic_summary, epic_description)
            spec_id = create_result.get("epic", {}).get("key", "SPEC-2024-001")
            await send_log(f"JIRA epic created: {spec_id}", "success")
            
        # Create Stories
        features = spec.get("features", ["Core Implementation", "Testing"]) if isinstance(spec, dict) else ["Core Implementation"]
        created_stories = []
        for feature in features:
            story_result = call_mcp_create_user_story(spec_id, str(feature), f"Implement {feature}")
            if story_result.get("status") == "success":
                created_stories.append(story_result.get("story", {}).get("key"))
        
        rag_data = {
            "rag_spec": spec,
            "jira_epic": spec_id,
            "created_stories": created_stories,
            "rag_status": rag_result.get("status"),
            "finetune_status": ft_result.get("status")
        }
        await update_step(2, "complete", spec_id, f"Epic {spec_id} ready", data=rag_data)
        return rag_data

    elif step_id == 3:
        # Step 3: Git Branch
        await send_log("Creating Git branch...", "info")
        await update_step(3, "in-progress", "", "Creating feature branch...")
        await asyncio.sleep(1)
        
        # Retrieve spec_id from previous step data if available, else use default
        step2_data = state.step_data.get(2, {})
        spec_id = step2_data.get("jira_epic", "SPEC-2024-001")
        branch_name = f"feature/{spec_id}-implementation"
        
        git_data = {
            "branch": branch_name,
            "base_branch": "main",
            "repository": "mcp-hack-2025",
            "command": f"git checkout -b {branch_name}"
        }
        await update_step(3, "complete", branch_name, f"Branch created: {branch_name}", data=git_data)
        await send_log(f"Git branch created: {branch_name}", "success")
        return git_data

    elif step_id == 4:
        # Step 4: Code Generation
        await send_log("Generating code...", "info")
        await update_step(4, "in-progress", "", "Generating implementation files...")
        await asyncio.sleep(2)
        
        files = [
            ("src/feature/main.py", "added", "+150 lines"),
            ("src/feature/utils.py", "added", "+75 lines"),
            ("tests/test_feature.py", "added", "+120 lines"),
        ]
        for f in files:
            await add_modified_file(*f)
            await asyncio.sleep(0.2)
            
        codegen_data = {
            "files_generated": [f[0] for f in files],
            "total_lines": 345,
            "model_used": "Claude 3.5 Sonnet"
        }
        await update_step(4, "complete", "3 files created", "Code generation complete", data=codegen_data)
        await send_log("Code generation complete", "success")
        return codegen_data

    elif step_id == 5:
        # Step 5: Code Review
        await send_log("Running code review...", "info")
        await update_step(5, "in-progress", "", "Analyzing code quality...")
        await asyncio.sleep(1.5)
        
        review_data = {
            "status": "Passed",
            "issues_found": 0,
            "linter_score": "10/10"
        }
        await update_step(5, "complete", "No issues found", "Code review passed", data=review_data)
        await send_log("Code review passed", "success")
        return review_data

    elif step_id == 6:
        # Step 6: Git Commit
        await send_log("Committing changes...", "info")
        await update_step(6, "in-progress", "", "Staging and committing files...")
        await asyncio.sleep(1)
        
        commit_data = {
            "hash": "a1b2c3d",
            "message": "feat: Implement new features",
            "author": "AI Agent",
            "files_changed": 3
        }
        await update_step(6, "complete", "a1b2c3d", "Committed changes", data=commit_data)
        await send_log("Changes committed", "success")
        return commit_data

    elif step_id == 7:
        # Step 7: Unit Testing
        await send_log("Running unit tests...", "info")
        await update_step(7, "in-progress", "", "Executing test suite...")
        await asyncio.sleep(2)
        
        test_data = {
            "total_tests": 12,
            "passed": 12,
            "failed": 0,
            "coverage": "100%"
        }
        await update_step(7, "complete", "12/12 passed", "All tests passed", data=test_data)
        await send_log("Unit tests passed", "success")
        return test_data

    elif step_id == 8:
        # Step 8: Manual Approval
        await send_log("Waiting for manual approval...", "info")
        await update_step(8, "in-progress", "", "Awaiting user approval...")
        await asyncio.sleep(1)
        
        approval_data = {
            "approver": "User",
            "timestamp": datetime.now().isoformat(),
            "status": "Approved"
        }
        await update_step(8, "complete", "Approved", "Changes approved", data=approval_data)
        await send_log("Changes approved by user", "success")
        return approval_data

    elif step_id == 9:
        # Step 9: PR Submission
        await send_log("Creating pull request...", "info")
        await update_step(9, "in-progress", "", "Submitting PR...")
        await asyncio.sleep(1.5)
        
        pr_data = {
            "pr_number": "#42",
            "title": "feat: New Feature Implementation",
            "url": "https://github.com/org/repo/pull/42"
        }
        await update_step(9, "complete", "#42", "PR created: #42", data=pr_data)
        await send_log("Pull request created", "success")
        return pr_data

    elif step_id == 10:
        # Step 10: PR Merge
        await send_log("Merging pull request...", "info")
        await update_step(10, "in-progress", "", "Merging to main branch...")
        await asyncio.sleep(1.5)
        
        merge_data = {
            "status": "Merged",
            "merged_by": "CI/CD Bot",
            "timestamp": datetime.now().isoformat()
        }
        await update_step(10, "complete", "Merged", "PR merged successfully", data=merge_data)
        await send_log("Pull request merged", "success")
        return merge_data

async def run_workflow(requirement: str):
    """Execute the workflow with human-in-the-loop steps"""
    state.workflow_running = True
    state.paused = False
    state.requirement = requirement
    
    # If starting fresh, reset current step
    if state.current_step == 0:
        state.current_step = 1
        
    try:
        while state.workflow_running and state.current_step <= 10:
            step_id = state.current_step
            
            # Execute the step
            try:
                step_data = await execute_step(step_id)
            except Exception as e:
                print(f"Error executing step {step_id}: {e}")
                await update_step(step_id, "error", "Failed", str(e))
                await manager.broadcast({"type": "workflow_error", "message": str(e)})
                state.workflow_running = False
                break
            
            # Wait for user confirmation
            try:
                await wait_for_confirmation(step_id, step_data)
            except asyncio.CancelledError:
                print("Workflow cancelled or paused")
                break
                
            # Move to next step only if we haven't been redirected (e.g. restart)
            if state.current_step == step_id:
                state.current_step += 1
        
        if state.current_step > 10:
            await manager.broadcast({
                "type": "workflow_complete",
                "message": "Workflow completed successfully!"
            })
            await send_log("🎉 Workflow completed successfully!", "success")
            state.workflow_running = False
            state.current_step = 0
            
    except Exception as e:
        print(f"Workflow fatal error: {e}")
        state.workflow_running = False
    finally:
        # If we exited loop but paused is true, we stay in running state logically
        if not state.paused:
            state.workflow_running = False

# ===== API Endpoints =====
@app.get("/")
async def root():
    """Serve the main dashboard page"""
    dashboard_dir = os.path.dirname(__file__)
    return FileResponse(os.path.join(dashboard_dir, "index.html"))

@app.post("/api/submit-requirement")
async def submit_requirement(req: RequirementInput):
    """Submit a new requirement and start the workflow"""
    if state.workflow_running:
        raise HTTPException(status_code=400, detail="Workflow already running")
    
    if len(req.requirement) < 50:
        raise HTTPException(status_code=400, detail="Requirement too short (minimum 50 characters)")
    
    # Start workflow in background
    state.workflow_task = asyncio.create_task(run_workflow(req.requirement))
    
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

# ===== LLM API Endpoints =====
class LLMGenerateRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: int = 256
    temperature: float = 0.7

class LLMChatRequest(BaseModel):
    message: str
    system_prompt: str = "You are a helpful AI assistant."
    max_tokens: int = 256

@app.post("/api/llm/generate")
async def llm_generate(req: LLMGenerateRequest):
    """Generate text using the LLM API"""
    result = call_llm_api(
        prompt=req.prompt,
        system_prompt=req.system_prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=503, detail=result.get("message", "LLM API unavailable"))
    
    return result

@app.post("/api/llm/chat")
async def llm_chat(req: LLMChatRequest):
    """Chat with the LLM"""
    result = call_llm_chat(
        message=req.message,
        system_prompt=req.system_prompt,
        max_tokens=req.max_tokens
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=503, detail=result.get("message", "LLM API unavailable"))
    
    return result

@app.get("/api/llm/health")
async def llm_health():
    """Check LLM API health"""
    try:
        response = requests.get(f"{LLM_API_URL}/health", timeout=10)
        if response.ok:
            return {"status": "healthy", "llm_api": response.json()}
        return {"status": "unhealthy", "error": f"Status {response.status_code}"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                
                if msg_type == "confirm_step":
                    print(f"User confirmed step {state.current_step}")
                    state.confirmation_event.set()
                    
                elif msg_type == "stop_workflow":
                    print("User stopped workflow")
                    state.workflow_running = False
                    state.paused = True
                    state.confirmation_event.set() # Unblock if waiting
                    await send_log("Workflow stopped by user", "warning")
                    
                elif msg_type == "restart_step":
                    step_id = message.get("stepId")
                    print(f"User requested restart from step {step_id}")
                    state.current_step = step_id
                    state.workflow_running = True
                    state.paused = False
                    state.confirmation_event.set() # Unblock to allow loop to continue/reset
                    await send_log(f"Restarting workflow from step {step_id}...", "info")
                    
                elif msg_type == "modify_step":
                    print("User requested modification")
                    state.workflow_running = False
                    state.paused = False
                    state.confirmation_event.set()
                    
            except json.JSONDecodeError:
                print(f"Received invalid JSON: {data}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# ===== Static Files =====
# Mount static files (CSS, JS) after API routes
dashboard_dir = os.path.dirname(__file__)
app.mount("/", StaticFiles(directory=dashboard_dir, html=True), name="static")

# ===== Main =====
if __name__ == "__main__":
    print("🚀 Starting AI Development Agent Dashboard Server...")
    print("📍 Dashboard: http://localhost:8000")
    print("🔌 WebSocket: ws://localhost:8000/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
