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
    """Call RAG via MCP server, fallback to direct API"""
    
    # Try MCP server first
    try:
        print(f"DEBUG: Calling RAG via MCP: {config.MCP_SERVER_URL}")
        response = requests.post(
            f"{config.MCP_SERVER_URL}{config.API_ENDPOINT_RAG}",
            json={"data": [requirement]},
            timeout=60
        )
        
        if response.ok:
            event_data = response.json()
            event_id = event_data.get("event_id")
            if event_id:
                result_response = requests.get(
                    f"{config.MCP_SERVER_URL}{config.API_ENDPOINT_RAG}/{event_id}",
                    timeout=60
                )
                if result_response.ok:
                    for line in result_response.iter_lines():
                        if line:
                            line_str = line.decode('utf-8')
                            if line_str.startswith('data:'):
                                data = json.loads(line_str[5:].strip())
                                if isinstance(data, list) and len(data) > 0:
                                    result = data[0] if isinstance(data[0], dict) else {}
                                    if result.get("status") == "success":
                                        print(f"DEBUG: MCP RAG success")
                                        return result
        print(f"DEBUG: MCP RAG failed, trying direct API")
    except Exception as e:
        print(f"DEBUG: MCP RAG error: {e}")
    
    # Fallback to direct Modal RAG API
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
            for line in answer.split('\n'):
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
    """Call fine-tuned model API via MCP server"""
    
    # Try MCP server first
    try:
        print(f"DEBUG: Calling fine-tuned model via MCP: {config.MCP_SERVER_URL}")
        response = requests.post(
            f"{config.MCP_SERVER_URL}{config.API_ENDPOINT_FINETUNED}",
            json={"data": [requirement, domain]},
            timeout=60
        )
        
        if response.ok:
            event_data = response.json()
            event_id = event_data.get("event_id")
            if event_id:
                result_response = requests.get(
                    f"{config.MCP_SERVER_URL}{config.API_ENDPOINT_FINETUNED}/{event_id}",
                    timeout=60
                )
                if result_response.ok:
                    for line in result_response.iter_lines():
                        if line:
                            line_str = line.decode('utf-8')
                            if line_str.startswith('data:'):
                                data = json.loads(line_str[5:].strip())
                                if isinstance(data, list) and len(data) > 0:
                                    result = data[0] if isinstance(data[0], dict) else {}
                                    if result.get("status") == "success":
                                        print(f"DEBUG: MCP Fine-tuned success")
                                        return result
        print(f"DEBUG: MCP Fine-tuned failed, trying direct API")
    except Exception as e:
        print(f"DEBUG: MCP Fine-tuned error: {e}")

    # Fallback to direct API
    ft_api_url = os.getenv("FINETUNED_MODEL_API_URL", "https://mcp-hack--phi3-inference-vllm-model-ask.modal.run")
    
    try:
        print(f"DEBUG: Calling fine-tuned API directly: {ft_api_url}")
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
                },
                "source": "direct_finetuned_api"
            }
    except Exception as e:
        print(f"DEBUG: Fine-tuned API error: {e}")
    
    # Fallback mock
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
    """Search JIRA epics via MCP server"""
    try:
        print(f"DEBUG: Searching epics via MCP: {config.MCP_SERVER_URL}")
        # Gradio 4.x API format
        response = requests.post(
            f"{config.MCP_SERVER_URL}{config.API_ENDPOINT_SEARCH_EPICS}",
            json={"data": [keywords, threshold]},
            timeout=30
        )
        
        if response.ok:
            # Gradio returns event_id, need to fetch result
            event_data = response.json()
            event_id = event_data.get("event_id")
            if event_id:
                result_response = requests.get(
                    f"{config.MCP_SERVER_URL}{config.API_ENDPOINT_SEARCH_EPICS}/{event_id}",
                    timeout=30
                )
                if result_response.ok:
                    for line in result_response.iter_lines():
                        if line:
                            line_str = line.decode('utf-8')
                            if line_str.startswith('data:'):
                                data = json.loads(line_str[5:].strip())
                                if isinstance(data, list) and len(data) > 0:
                                    return data[0] if isinstance(data[0], dict) else {"status": "success", "epics": [], "count": 0}
        print(f"DEBUG: MCP search failed, returning empty")
    except Exception as e:
        print(f"DEBUG: MCP search error: {e}")
    
    return {"status": "success", "epics": [], "count": 0}

def call_mcp_create_epic(summary: str, description: str, project_key: str = "SCRUM") -> Dict:
    """Create JIRA epic via MCP server"""
    try:
        print(f"DEBUG: Creating epic via MCP: {config.MCP_SERVER_URL}")
        response = requests.post(
            f"{config.MCP_SERVER_URL}{config.API_ENDPOINT_CREATE_EPIC}",
            json={"data": [summary, description, project_key]},
            timeout=30
        )
        
        if response.ok:
            event_data = response.json()
            event_id = event_data.get("event_id")
            if event_id:
                result_response = requests.get(
                    f"{config.MCP_SERVER_URL}{config.API_ENDPOINT_CREATE_EPIC}/{event_id}",
                    timeout=30
                )
                if result_response.ok:
                    for line in result_response.iter_lines():
                        if line:
                            line_str = line.decode('utf-8')
                            if line_str.startswith('data:'):
                                data = json.loads(line_str[5:].strip())
                                if isinstance(data, list) and len(data) > 0:
                                    result = data[0] if isinstance(data[0], dict) else {}
                                    if result.get("status") == "success":
                                        print(f"DEBUG: Epic created: {result.get('epic', {}).get('key')}")
                                        return result
        print(f"DEBUG: MCP create epic failed")
    except Exception as e:
        print(f"DEBUG: MCP create epic error: {e}")
    
    # Fallback to mock
    import random
    epic_id = random.randint(100, 999)
    epic_key = f"{project_key}-{epic_id}"
    return {
        "status": "success",
        "epic": {"key": epic_key, "summary": summary, "url": f"https://mock-jira.atlassian.net/browse/{epic_key}"},
        "source": "mock_fallback"
    }

def call_mcp_create_user_story(epic_key: str, summary: str, description: str, story_points: int = None) -> Dict:
    """Create JIRA user story via MCP server"""
    try:
        print(f"DEBUG: Creating story via MCP: {config.MCP_SERVER_URL}")
        response = requests.post(
            f"{config.MCP_SERVER_URL}{config.API_ENDPOINT_CREATE_STORY}",
            json={"data": [epic_key, summary, description, story_points or 3]},
            timeout=30
        )
        
        if response.ok:
            event_data = response.json()
            event_id = event_data.get("event_id")
            if event_id:
                result_response = requests.get(
                    f"{config.MCP_SERVER_URL}{config.API_ENDPOINT_CREATE_STORY}/{event_id}",
                    timeout=30
                )
                if result_response.ok:
                    for line in result_response.iter_lines():
                        if line:
                            line_str = line.decode('utf-8')
                            if line_str.startswith('data:'):
                                data = json.loads(line_str[5:].strip())
                                if isinstance(data, list) and len(data) > 0:
                                    result = data[0] if isinstance(data[0], dict) else {}
                                    if result.get("status") == "success":
                                        print(f"DEBUG: Story created: {result.get('story', {}).get('key')}")
                                        return result
        print(f"DEBUG: MCP create story failed")
    except Exception as e:
        print(f"DEBUG: MCP create story error: {e}")
    
    # Fallback to mock
    import random
    project_key = epic_key.split('-')[0] if '-' in epic_key else "SCRUM"
    story_id = random.randint(200, 999)
    story_key = f"{project_key}-{story_id}"
    return {
        "status": "success",
        "story": {"key": story_key, "summary": summary, "epic_key": epic_key, "story_points": story_points or 3},
        "source": "mock_fallback"
    }

# Store JIRA items for status management
jira_items = {}

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
        3: "finetuned_completed",
        4: "stories_crafted",
        5: "jira_created",
        6: "tasks_generated",
        7: "git_branch_created",
        8: "code_generated",
        9: "review_testing_done",
        10: "deployed"
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
        # Step 2: RAG Product Research via MCP
        await send_log("Step 2: RAG Product Research...", "info")
        await update_step(2, "in-progress", "", "Querying RAG for product specs & best practices...")
        
        rag_result = call_mcp_rag(requirement)
        rag_context = ""
        spec = {}
        
        if rag_result.get("status") == "success":
            spec = rag_result.get("specification") or {}
            rag_context = spec.get("full_answer", "") or spec.get("summary", "")
            await send_log(f"RAG: Retrieved {len(rag_context)} chars of context", "success")
        else:
            await send_log("RAG query failed, will continue with LLM", "warning")
        
        rag_data = {
            "rag_context": rag_context,
            "spec": spec,
            "features": spec.get("features", []),
            "technical_requirements": spec.get("technical_requirements", []),
            "source": rag_result.get("source", "unknown"),
            "status": rag_result.get("status")
        }
        await update_step(2, "complete", f"{len(rag_context)} chars", "RAG research complete", data=rag_data)
        await send_log("RAG product research complete", "success")
        return rag_data

    elif step_id == 3:
        # Step 3: Fine-tuned Model Analysis via MCP
        await send_log("Step 3: Fine-tuned Model Analysis...", "info")
        await update_step(3, "in-progress", "", "Getting domain-specific insights...")
        
        ft_result = call_mcp_finetuned(requirement, domain="insurance")
        ft_insights = ""
        recommendations = []
        
        if ft_result.get("status") == "success":
            insights = ft_result.get("insights", {})
            ft_insights = insights.get("full_response", "")
            recommendations = insights.get("recommendations", [])
            await send_log(f"Fine-tuned: Got {len(recommendations)} recommendations", "success")
        else:
            await send_log("Fine-tuned query failed, will use defaults", "warning")
            recommendations = ["Follow industry best practices", "Ensure security compliance", "Add comprehensive testing"]
        
        ft_data = {
            "ft_insights": ft_insights,
            "recommendations": recommendations,
            "domain": ft_result.get("insights", {}).get("domain", "general"),
            "source": ft_result.get("source", "unknown"),
            "status": ft_result.get("status")
        }
        await update_step(3, "complete", f"{len(recommendations)} insights", "Domain analysis complete", data=ft_data)
        await send_log("Fine-tuned model analysis complete", "success")
        return ft_data

    elif step_id == 4:
        # Step 4: Craft User Stories with LLM
        await send_log("Step 4: Crafting User Stories with LLM...", "info")
        await update_step(4, "in-progress", "", "LLM generating user stories from analysis...")
        
        # Get context from previous steps
        step2_data = state.step_data.get(2, {})
        step3_data = state.step_data.get(3, {})
        rag_context = step2_data.get("rag_context", "")
        ft_insights = step3_data.get("ft_insights", "")
        recommendations = step3_data.get("recommendations", [])
        
        story_prompt = f"""Based on this requirement and analysis, generate 3-5 user stories.

REQUIREMENT: {requirement}

PRODUCT RESEARCH (RAG): {rag_context[:600] if rag_context else 'No additional context'}

DOMAIN INSIGHTS: {ft_insights[:400] if ft_insights else chr(10).join(recommendations[:3])}

Generate user stories in this EXACT format (one per line):
STORY: [Title] | [As a... I want... so that...] | [Acceptance Criteria] | [Story Points 1-8]
"""
        
        llm_result = call_llm_api(story_prompt, "You are a senior product manager. Generate clear, actionable user stories.", 1000, 0.4)
        
        user_stories = []
        if llm_result.get("status") == "success":
            for line in llm_result.get("text", "").split('\n'):
                if 'STORY:' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        user_stories.append({
                            "title": parts[0].replace('STORY:', '').strip(),
                            "description": parts[1].strip() if len(parts) > 1 else "",
                            "acceptance": parts[2].strip() if len(parts) > 2 else "",
                            "points": int(parts[3].strip()) if len(parts) > 3 and parts[3].strip().isdigit() else 3
                        })
        
        if not user_stories:
            user_stories = [
                {"title": "Core Feature", "description": f"Implement: {requirement[:80]}", "acceptance": "Works as specified", "points": 5},
                {"title": "Testing", "description": "Write unit tests", "acceptance": "80% coverage", "points": 3},
                {"title": "Documentation", "description": "Create docs", "acceptance": "README complete", "points": 2}
            ]
        
        stories_data = {
            "user_stories": user_stories,
            "count": len(user_stories),
            "total_points": sum(s.get("points", 3) for s in user_stories),
            "source": "llm" if llm_result.get("status") == "success" else "fallback"
        }
        await update_step(4, "complete", f"{len(user_stories)} stories", "User stories crafted", data=stories_data)
        await send_log(f"Crafted {len(user_stories)} user stories", "success")
        return stories_data

    elif step_id == 5:
        # Step 5: Create JIRA Epic & Stories via MCP
        await send_log("Step 5: Creating JIRA Epic & Stories...", "info")
        await update_step(5, "in-progress", "", "Creating epic and stories in JIRA...")
        
        step4_data = state.step_data.get(4, {})
        user_stories = step4_data.get("user_stories", [])
        
        # Create Epic
        epic_title = f"Feature: {requirement[:80]}..."
        epic_desc = f"Implementation of: {requirement}"
        create_result = call_mcp_create_epic(epic_title, epic_desc)
        epic_data = create_result.get("epic", {})
        epic_key = epic_data.get("key", "PROJ-100")
        jira_items[epic_key] = epic_data
        await send_log(f"Epic created: {epic_key}", "success")
        
        # Create Stories
        created_stories = []
        for story in user_stories:
            story_desc = f"{story['description']}\n\nAcceptance: {story.get('acceptance', '')}"
            result = call_mcp_create_user_story(epic_key, story["title"], story_desc, story.get("points", 3))
            if result.get("status") == "success":
                story_data = result.get("story", {})
                story_data.update(story)
                created_stories.append(story_data)
                jira_items[story_data.get("key", "")] = story_data
        
        await send_log(f"Created {len(created_stories)} stories in JIRA", "success")
        
        jira_data = {
            "epic": epic_data,
            "jira_epic": epic_key,
            "stories": created_stories,
            "total_story_points": sum(s.get("points", 3) for s in created_stories),
            "jira_source": create_result.get("source", "unknown")
        }
        await update_step(5, "complete", epic_key, f"Epic {epic_key} + {len(created_stories)} stories", data=jira_data)
        return jira_data

    elif step_id == 6:
        # Step 6: Generate Tasks for each Story
        await send_log("Step 6: Generating Development Tasks...", "info")
        await update_step(6, "in-progress", "", "Breaking down stories into tasks...")
        
        step5_data = state.step_data.get(5, {})
        stories = step5_data.get("stories", [])
        
        task_prompt = f"""Generate 2-3 development tasks for each user story.

User Stories:
{chr(10).join([f"- {s.get('title', s.get('summary', 'Story'))}: {s.get('description', '')}" for s in stories])}

Format: TASK: [Story] | [Task Name] | [Hours]"""
        
        tasks = []
        llm_result = call_llm_api(task_prompt, "You are a tech lead.", 600, 0.3)
        if llm_result.get("status") == "success":
            for line in llm_result.get("text", "").split('\n'):
                if 'TASK:' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        tasks.append({"story": parts[0].replace('TASK:', '').strip(), "name": parts[1].strip(), "hours": parts[2].strip() if len(parts) > 2 else "4"})
        
        if not tasks:
            tasks = [{"story": "Implementation", "name": "Setup project", "hours": "2"},
                     {"story": "Implementation", "name": "Core logic", "hours": "8"},
                     {"story": "Testing", "name": "Unit tests", "hours": "4"}]
        
        task_data = {"tasks": tasks, "total_tasks": len(tasks), "total_hours": sum(int(t.get("hours", "4")) for t in tasks)}
        await update_step(6, "complete", f"{len(tasks)} tasks", f"Generated {len(tasks)} tasks", data=task_data)
        await send_log(f"Generated {len(tasks)} development tasks", "success")
        return task_data

    elif step_id == 7:
        # Step 7: Create Git Branch
        await send_log("Step 7: Creating Git Branch...", "info")
        await update_step(7, "in-progress", "", "Creating feature branch...")
        await asyncio.sleep(1)
        
        step5_data = state.step_data.get(5, {})
        epic_key = step5_data.get("jira_epic", "FEAT-001")
        branch_name = f"feature/{epic_key}-implementation"
        
        git_data = {"branch": branch_name, "base_branch": "main", "command": f"git checkout -b {branch_name}"}
        await update_step(7, "complete", branch_name, f"Branch: {branch_name}", data=git_data)
        await send_log(f"Git branch created: {branch_name}", "success")
        return git_data

    elif step_id == 8:
        # Step 8: Code Generation
        await send_log("Step 8: AI Code Generation...", "info")
        await update_step(8, "in-progress", "", "AI generating implementation...")
        await asyncio.sleep(2)
        
        files = [("src/feature/main.py", "added", "+150 lines"), ("src/feature/utils.py", "added", "+75 lines"), ("tests/test_feature.py", "added", "+120 lines")]
        for f in files:
            await add_modified_file(*f)
        
        codegen_data = {"files_generated": [f[0] for f in files], "total_lines": 345, "model": "LLM"}
        await update_step(8, "complete", "3 files", "Code generated", data=codegen_data)
        await send_log("Code generation complete", "success")
        return codegen_data

    elif step_id == 9:
        # Step 9: Code Review & Testing
        await send_log("Step 9: Code Review & Testing...", "info")
        await update_step(9, "in-progress", "", "Running review and tests...")
        await asyncio.sleep(2)
        
        review_test_data = {
            "review_status": "Passed",
            "issues_found": 0,
            "tests_total": 12,
            "tests_passed": 12,
            "coverage": "95%"
        }
        await update_step(9, "complete", "12/12 tests", "Review & tests passed", data=review_test_data)
        await send_log("Code review and testing complete", "success")
        return review_test_data

    elif step_id == 10:
        # Step 10: PR, Merge & Deploy
        await send_log("Step 10: PR, Merge & Deploy...", "info")
        await update_step(10, "in-progress", "", "Creating PR, merging & deploying...")
        await asyncio.sleep(2)
        
        step5_data = state.step_data.get(5, {})
        epic_key = step5_data.get("jira_epic", "FEAT-001")
        
        deploy_data = {
            "pr_number": "#42",
            "pr_title": f"feat({epic_key}): Feature Implementation",
            "pr_url": "https://github.com/org/repo/pull/42",
            "status": "Merged & Deployed",
            "branch": f"feature/{epic_key}-implementation",
            "merged_to": "main",
            "timestamp": datetime.now().isoformat(),
            "jira_updated": True
        }
        await update_step(10, "complete", "Deployed ✓", "PR merged & deployed", data=deploy_data)
        await send_log(f"PR #{42} merged and deployed to main", "success")
        return deploy_data

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

# ===== JIRA API Endpoints =====
# ===== JIRA Data Models =====
class StoryCreate(BaseModel):
    summary: str
    description: str = ""
    story_points: int = 3
    epic_key: str

class StoryUpdate(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    story_points: Optional[int] = None
    status: Optional[str] = None

class TaskCreate(BaseModel):
    summary: str
    description: str = ""
    story_key: str

class TaskUpdate(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

# ===== JIRA API Endpoints =====
@app.get("/api/jira/items")
async def get_jira_items():
    """Get all JIRA items"""
    return {"items": list(jira_items.values())}

@app.get("/api/jira/epic/{epic_key}")
async def get_epic_with_stories(epic_key: str):
    """Get epic with all its stories and tasks"""
    if epic_key not in jira_items:
        raise HTTPException(status_code=404, detail="Epic not found")
    
    epic = jira_items[epic_key]
    stories = [item for item in jira_items.values() if item.get("epic_key") == epic_key and item.get("type") == "Story"]
    
    # Get tasks for each story
    for story in stories:
        story["tasks"] = [item for item in jira_items.values() if item.get("story_key") == story.get("key") and item.get("type") == "Task"]
    
    return {"epic": epic, "stories": stories}

@app.get("/api/jira/item/{key}")
async def get_jira_item(key: str):
    """Get a specific JIRA item"""
    if key not in jira_items:
        raise HTTPException(status_code=404, detail="Item not found")
    return jira_items[key]

@app.post("/api/jira/story")
async def create_story(story: StoryCreate):
    """Create a new user story"""
    import random
    project_key = story.epic_key.split('-')[0] if '-' in story.epic_key else "SCRUM"
    story_id = random.randint(200, 999)
    story_key = f"{project_key}-{story_id}"
    
    story_data = {
        "key": story_key,
        "type": "Story",
        "summary": story.summary,
        "description": story.description,
        "story_points": story.story_points,
        "epic_key": story.epic_key,
        "status": "To Do",
        "created": datetime.now().isoformat(),
        "tasks": []
    }
    jira_items[story_key] = story_data
    
    await manager.broadcast({"type": "jira_item_created", "item": story_data})
    return {"status": "success", "story": story_data}

@app.put("/api/jira/story/{key}")
async def update_story(key: str, update: StoryUpdate):
    """Update a user story"""
    if key not in jira_items:
        raise HTTPException(status_code=404, detail="Story not found")
    
    story = jira_items[key]
    if update.summary: story["summary"] = update.summary
    if update.description: story["description"] = update.description
    if update.story_points: story["story_points"] = update.story_points
    if update.status: story["status"] = update.status
    story["updated"] = datetime.now().isoformat()
    
    await manager.broadcast({"type": "jira_item_updated", "item": story})
    return {"status": "success", "story": story}

@app.delete("/api/jira/story/{key}")
async def delete_story(key: str):
    """Delete a user story and its tasks"""
    if key not in jira_items:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Delete associated tasks
    tasks_to_delete = [k for k, v in jira_items.items() if v.get("story_key") == key]
    for task_key in tasks_to_delete:
        del jira_items[task_key]
    
    del jira_items[key]
    await manager.broadcast({"type": "jira_item_deleted", "key": key})
    return {"status": "success", "deleted": key}

@app.post("/api/jira/task")
async def create_task(task: TaskCreate):
    """Create a new task under a story"""
    import random
    if task.story_key not in jira_items:
        raise HTTPException(status_code=404, detail="Story not found")
    
    project_key = task.story_key.split('-')[0] if '-' in task.story_key else "SCRUM"
    task_id = random.randint(300, 999)
    task_key = f"{project_key}-{task_id}"
    
    task_data = {
        "key": task_key,
        "type": "Task",
        "summary": task.summary,
        "description": task.description,
        "story_key": task.story_key,
        "status": "To Do",
        "created": datetime.now().isoformat()
    }
    jira_items[task_key] = task_data
    
    await manager.broadcast({"type": "jira_item_created", "item": task_data})
    return {"status": "success", "task": task_data}

@app.put("/api/jira/task/{key}")
async def update_task(key: str, update: TaskUpdate):
    """Update a task"""
    if key not in jira_items:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = jira_items[key]
    if update.summary: task["summary"] = update.summary
    if update.description: task["description"] = update.description
    if update.status: task["status"] = update.status
    task["updated"] = datetime.now().isoformat()
    
    await manager.broadcast({"type": "jira_item_updated", "item": task})
    return {"status": "success", "task": task}

@app.delete("/api/jira/task/{key}")
async def delete_task(key: str):
    """Delete a task"""
    if key not in jira_items:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del jira_items[key]
    await manager.broadcast({"type": "jira_item_deleted", "key": key})
    return {"status": "success", "deleted": key}

@app.put("/api/jira/item/{key}/status")
async def update_jira_status(key: str, update: StoryUpdate):
    """Update JIRA item status"""
    if key not in jira_items:
        raise HTTPException(status_code=404, detail="Item not found")
    
    valid_statuses = ["To Do", "In Progress", "In Review", "Done"]
    if update.status and update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    if update.status:
        jira_items[key]["status"] = update.status
    jira_items[key]["updated"] = datetime.now().isoformat()
    
    await manager.broadcast({"type": "jira_status_updated", "key": key, "status": update.status})
    return {"status": "success", "item": jira_items[key]}

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
