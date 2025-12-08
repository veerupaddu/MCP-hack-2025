"""
FastAPI endpoint for User Story Agent

Exposes the User Story Agent as a REST API endpoint.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uvicorn
import os


from user_story_agent import UserStoryAgent, UserStoryResponse, ProductSpec

# ===== Request/Response Models =====

class UserStoryRequest(BaseModel):
    """Request model for user story generation"""
    query: str = Field(
        ...,
        description="The user requirement to transform into user stories",
        min_length=10,
        example="I need a feature for customers to file auto insurance claims online"
    )
    use_rag: bool = Field(
        default=True,
        description="Whether to query RAG for product context"
    )
    use_finetuned: bool = Field(
        default=True,
        description="Whether to query fine-tuned model for domain insights"
    )


class ProductSpecRequest(BaseModel):
    """Request model for product spec generation"""
    query: str = Field(..., min_length=10)
    use_rag: bool = True
    use_finetuned: bool = True


class ProductSpecOutput(BaseModel):
    """Output model for product spec"""
    spec_id: str
    title: str
    summary: str
    status: str
    created_at: str
    target_audience: str
    key_features: List[str]
    technical_requirements: List[str]
    success_metrics: List[str]
    assumptions: List[str]
    dependencies: List[str]


class AcceptanceCriteria(BaseModel):
    """Acceptance criteria model"""
    criteria: str


class UserStoryOutput(BaseModel):
    """Output model for a single user story"""
    story_id: str
    title: str
    description: str
    actor: str
    action: str
    benefit: str
    acceptance_criteria: List[str]
    tasks: List[str]
    story_points: int
    priority: str
    technical_notes: List[str]


class UserStoryApiResponse(BaseModel):
    """Response model for user story API"""
    success: bool
    stories: List[UserStoryOutput]
    raw_query: str
    domain: str
    mcp_source: str
    confidence: float
    warnings: List[str]
    markdown: Optional[str] = None
    spec_id: Optional[str] = None


# ===== FastAPI App =====

app = FastAPI(
    title="User Story Agent API",
    description="Transform user requirements into structured user stories using AI",
    version="1.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
agent = UserStoryAgent()


# ===== Helper Functions =====

def convert_to_api_response(response: UserStoryResponse, include_markdown: bool = False) -> UserStoryApiResponse:
    """Convert UserStoryResponse to API response format"""
    stories_output = [
        UserStoryOutput(
            story_id=story.story_id,
            title=story.title,
            description=story.description,
            actor=story.actor,
            action=story.action,
            benefit=story.benefit,
            acceptance_criteria=story.acceptance_criteria,
            tasks=story.tasks,
            story_points=story.story_points,
            priority=story.priority,
            technical_notes=story.technical_notes
        )
        for story in response.stories
    ]
    
    markdown = None
    if include_markdown:
        markdown = agent.format_all_stories_markdown(response)
    
    return UserStoryApiResponse(
        success=True,
        stories=stories_output,
        raw_query=response.raw_query,
        domain=response.domain,
        mcp_source=response.mcp_source,
        confidence=response.confidence,
        warnings=response.warnings,
        markdown=markdown,
        spec_id=response.spec_id
    )


# ===== API Endpoints =====

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the HTML interface"""
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    
    if os.path.exists(html_path):
        with open(html_path, "r") as f:
            return f.read()
    else:
        return """
        <html>
            <body>
                <h1>User Story Agent API</h1>
                <p>API Version: 1.1.0</p>
                <p>Persona: Alex - Senior Product Owner & Business Analyst</p>
                <p><a href="/docs">API Documentation</a></p>
            </body>
        </html>
        """


@app.get("/api", response_class=HTMLResponse)
async def api_info():
    """Root endpoint with API information"""
    return {
        "name": "User Story Agent API",
        "version": "1.1.0",
        "persona": agent.PERSONA_NAME,
        "role": agent.PERSONA_ROLE,
        "endpoints": {
            "generate": "POST /api/user-stories",
            "specs_draft": "POST /api/specs/draft",
            "specs_list": "GET /api/specs",
            "health": "GET /health"
        },
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": agent.PERSONA_NAME,
        "mcp_server": agent.mcp_server_url
    }


@app.post("/api/user-stories", response_model=UserStoryApiResponse)
async def generate_user_stories(request: UserStoryRequest):
    """Generate user stories from a requirement (Legacy/Direct mode)"""
    try:
        response = agent.transform_to_user_stories(
            request.query,
            use_rag=request.use_rag,
            use_finetuned=request.use_finetuned
        )
        return convert_to_api_response(response, include_markdown=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/user-stories/markdown")
async def generate_user_stories_markdown(request: UserStoryRequest):
    """Generate user stories and return as markdown"""
    try:
        response = agent.transform_to_user_stories(
            request.query,
            use_rag=request.use_rag,
            use_finetuned=request.use_finetuned
        )
        return convert_to_api_response(response, include_markdown=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ===== Product Spec Endpoints =====

@app.post("/api/specs/draft", response_model=ProductSpecOutput)
async def create_draft_spec(request: ProductSpecRequest):
    """Create a new draft product specification"""
    try:
        spec = agent.create_draft_spec(
            request.query,
            use_rag=request.use_rag,
            use_finetuned=request.use_finetuned
        )
        return ProductSpecOutput(**spec.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating spec: {str(e)}")


@app.get("/api/specs", response_model=List[Dict])
async def list_specs():
    """List all product specifications"""
    try:
        return agent.list_specs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing specs: {str(e)}")


@app.get("/api/specs/{spec_id}", response_model=ProductSpecOutput)
async def get_spec(spec_id: str):
    """Get a specific product specification"""
    spec = agent.get_spec(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")
    return ProductSpecOutput(**spec.to_dict())


@app.post("/api/specs/{spec_id}/approve", response_model=ProductSpecOutput)
async def approve_spec(spec_id: str):
    """Approve a product specification"""
    spec = agent.approve_spec(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")
    return ProductSpecOutput(**spec.to_dict())


@app.post("/api/specs/{spec_id}/generate-stories", response_model=UserStoryApiResponse)
async def generate_stories_from_spec(spec_id: str):
    """Generate user stories from an approved specification"""
    try:
        response = agent.generate_stories_from_spec(spec_id)
        return convert_to_api_response(response, include_markdown=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating stories: {str(e)}")


# ===== Main =====

if __name__ == "__main__":
    print(f"\n🚀 Starting User Story Agent API")
    print(f"👤 Persona: {agent.PERSONA_NAME} - {agent.PERSONA_ROLE}")
    print(f"🔗 MCP Server: {agent.mcp_server_url}")
    print(f"📚 API Docs: http://localhost:8001/docs\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
