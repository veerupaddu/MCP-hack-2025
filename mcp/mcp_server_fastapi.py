from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import os
from difflib import SequenceMatcher
from datetime import datetime

# ===== FastAPI App =====
app = FastAPI(title="AI Development Agent MCP Server", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Configuration =====
class Config:
    JIRA_URL = os.getenv("JIRA_URL", "")
    JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
    JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "PROJ")
    RAG_ENABLED = os.getenv("RAG_ENABLED", "false").lower() == "true"
    FINETUNED_MODEL_PATH = os.getenv("FINETUNED_MODEL_PATH", "")

config = Config()

# ===== Mock Data =====
mock_epics = [
    {
        "key": "PROJ-100",
        "summary": "User Authentication System",
        "description": "Implement comprehensive user authentication with OAuth2, JWT tokens, and MFA",
        "status": "In Progress",
        "created": "2024-01-15"
    },
    {
        "key": "PROJ-101",
        "summary": "Payment Gateway Integration",
        "description": "Integrate Stripe and PayPal payment gateways with webhook support",
        "status": "Done",
        "created": "2024-02-01"
    },
    {
        "key": "PROJ-102",
        "summary": "Real-time Notification System",
        "description": "Build WebSocket-based notification system with push notifications",
        "status": "To Do",
        "created": "2024-03-10"
    }
]

# ===== Request/Response Models =====
class RAGRequest(BaseModel):
    requirement: str

class FinetunedRequest(BaseModel):
    requirement: str
    domain: str = "general"

class SearchEpicsRequest(BaseModel):
    keywords: str
    threshold: float = 0.6

class CreateEpicRequest(BaseModel):
    summary: str
    description: str
    project_key: str = "PROJ"

class CreateStoryRequest(BaseModel):
    epic_key: str
    summary: str
    description: str
    story_points: Optional[int] = None

# ===== Helper Functions =====
def calculate_similarity(text1: str, text2: str) -> float:
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def use_real_jira() -> bool:
    return bool(config.JIRA_URL and config.JIRA_EMAIL and config.JIRA_API_TOKEN)

# ===== API Endpoints =====
@app.get("/")
async def root():
    return {
        "name": "AI Development Agent MCP Server",
        "version": "1.0.0",
        "status": "running",
        "mode": "real_jira" if use_real_jira() else "mock",
        "endpoints": {
            "rag": "/api/rag",
            "finetuned": "/api/finetuned",
            "search_epics": "/api/search-epics",
            "create_epic": "/api/create-epic",
            "create_story": "/api/create-story"
        }
    }

@app.post("/api/rag")
async def query_rag(request: RAGRequest) -> Dict:
    """Query RAG system for product specification"""
    print(f"[RAG] Query: {request.requirement[:100]}...")
    
    specification = {
        "title": "Generated Product Specification",
        "summary": f"Product specification for: {request.requirement[:100]}",
        "features": [
            "Core functionality implementation",
            "User interface components",
            "API endpoints and integration",
            "Database schema design",
            "Security and authentication"
        ],
        "technical_requirements": [
            "Backend: Python/FastAPI or Node.js/Express",
            "Frontend: React or Vue.js",
            "Database: PostgreSQL or MongoDB",
            "Authentication: JWT tokens",
            "Deployment: Docker containers"
        ],
        "acceptance_criteria": [
            "All core features implemented and tested",
            "API documentation complete",
            "Unit test coverage > 80%",
            "Security audit passed",
            "Performance benchmarks met"
        ],
        "dependencies": [
            "User authentication system",
            "Database migration tools",
            "CI/CD pipeline setup"
        ],
        "estimated_effort": "2-3 sprints",
        "context_retrieved": 5,
        "confidence_score": 0.85
    }
    
    return {
        "status": "success",
        "specification": specification,
        "source": "mock_rag" if not config.RAG_ENABLED else "real_rag",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/finetuned")
async def query_finetuned(request: FinetunedRequest) -> Dict:
    """Query fine-tuned model for domain insights"""
    print(f"[Fine-tuned] Query: {request.requirement[:100]}... (domain: {request.domain})")
    
    domain_insights = {
        "insurance": {
            "regulatory_requirements": ["GDPR compliance", "Insurance regulations"],
            "risk_factors": ["Data privacy", "Claims processing accuracy"],
            "best_practices": ["Actuarial validation", "Fraud detection"]
        },
        "finance": {
            "regulatory_requirements": ["PCI-DSS", "SOX compliance"],
            "risk_factors": ["Transaction security", "Audit trails"],
            "best_practices": ["Double-entry bookkeeping", "Reconciliation"]
        },
        "general": {
            "regulatory_requirements": ["Data protection", "Accessibility"],
            "risk_factors": ["Security vulnerabilities", "Scalability"],
            "best_practices": ["Code review", "Automated testing"]
        }
    }
    
    insights = domain_insights.get(request.domain, domain_insights["general"])
    
    return {
        "status": "success",
        "domain": request.domain,
        "insights": insights,
        "recommendations": [
            f"Consider {request.domain}-specific compliance requirements",
            "Implement domain-specific validation rules",
            "Add specialized error handling",
            "Include domain expert review in workflow"
        ],
        "confidence_score": 0.78,
        "source": "mock_finetuned" if not config.FINETUNED_MODEL_PATH else "real_finetuned",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/search-epics")
async def search_epics(request: SearchEpicsRequest) -> Dict:
    """Search for existing JIRA epics"""
    print(f"[JIRA] Search: {request.keywords}")
    
    matching_epics = []
    for epic in mock_epics:
        summary_sim = calculate_similarity(request.keywords, epic["summary"])
        desc_sim = calculate_similarity(request.keywords, epic["description"])
        max_sim = max(summary_sim, desc_sim)
        
        if max_sim >= request.threshold:
            matching_epics.append({
                **epic,
                "similarity_score": round(max_sim, 2)
            })
    
    matching_epics.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    return {
        "status": "success",
        "count": len(matching_epics),
        "epics": matching_epics,
        "source": "mock_jira" if not use_real_jira() else "real_jira",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/create-epic")
async def create_epic(request: CreateEpicRequest) -> Dict:
    """Create new JIRA epic"""
    print(f"[JIRA] Create epic: {request.summary}")
    
    epic_key = f"{request.project_key}-{len(mock_epics) + 100}"
    new_epic = {
        "key": epic_key,
        "summary": request.summary,
        "description": request.description,
        "status": "To Do",
        "created": datetime.now().strftime("%Y-%m-%d"),
        "url": f"{config.JIRA_URL or 'https://mock-jira.atlassian.net'}/browse/{epic_key}"
    }
    
    mock_epics.append(new_epic)
    
    return {
        "status": "success",
        "epic": new_epic,
        "source": "mock_jira" if not use_real_jira() else "real_jira",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/create-story")
async def create_story(request: CreateStoryRequest) -> Dict:
    """Create new JIRA user story"""
    print(f"[JIRA] Create story: {request.summary}")
    
    story_key = f"{request.epic_key.split('-')[0]}-{200}"
    new_story = {
        "key": story_key,
        "epic_key": request.epic_key,
        "summary": request.summary,
        "description": request.description,
        "story_points": request.story_points,
        "status": "To Do",
        "created": datetime.now().strftime("%Y-%m-%d"),
        "url": f"{config.JIRA_URL or 'https://mock-jira.atlassian.net'}/browse/{story_key}"
    }
    
    return {
        "status": "success",
        "story": new_story,
        "source": "mock_jira" if not use_real_jira() else "real_jira",
        "timestamp": datetime.now().isoformat()
    }

# ===== Main =====
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MCP_PORT", "7860"))
    print(f"🚀 Starting AI Development Agent MCP Server...")
    print(f"📍 Server URL: http://localhost:{port}")
    print(f"🔧 Mode: {'Real JIRA' if use_real_jira() else 'Mock Mode'}")
    print(f"📚 API Docs: http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
