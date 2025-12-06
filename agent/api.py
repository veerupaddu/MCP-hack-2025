"""
FastAPI endpoint for User Story Agent

Exposes the User Story Agent as a REST API endpoint.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
import os

from user_story_agent import UserStoryAgent, UserStoryResponse


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


class AcceptanceCriteria(BaseModel):
    """Acceptance criteria model"""
    criteria: str


class UserStoryOutput(BaseModel):
    """Output model for a single user story"""
    story_id: str
    title: str
    actor: str
    action: str
    benefit: str
    acceptance_criteria: List[str]
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


# ===== FastAPI App =====

app = FastAPI(
    title="User Story Agent API",
    description="Transform user requirements into structured user stories using AI",
    version="1.0.0",
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
            actor=story.actor,
            action=story.action,
            benefit=story.benefit,
            acceptance_criteria=story.acceptance_criteria,
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
        markdown=markdown
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
                <p>API Version: 1.0.0</p>
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
        "version": "1.0.0",
        "persona": agent.PERSONA_NAME,
        "role": agent.PERSONA_ROLE,
        "endpoints": {
            "generate": "POST /api/user-stories",
            "generate_markdown": "POST /api/user-stories/markdown",
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
    """
    Generate user stories from a requirement
    
    This endpoint transforms a user requirement into structured user stories
    by querying the MCP server (RAG + Fine-tuned models) and applying
    INVEST principles.
    
    **Returns:**
    - Structured user stories with acceptance criteria
    - Story points and priority
    - Confidence score
    - Technical notes
    """
    try:
        # Generate user stories
        response = agent.transform_to_user_stories(
            request.query,
            use_rag=request.use_rag,
            use_finetuned=request.use_finetuned
        )
        
        # Convert to API response
        return convert_to_api_response(response, include_markdown=False)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating user stories: {str(e)}"
        )


@app.post("/api/user-stories/markdown")
async def generate_user_stories_markdown(request: UserStoryRequest):
    """
    Generate user stories and return as markdown
    
    Same as /api/user-stories but includes a formatted markdown document
    of all the generated stories.
    """
    try:
        # Generate user stories
        response = agent.transform_to_user_stories(
            request.query,
            use_rag=request.use_rag,
            use_finetuned=request.use_finetuned
        )
        
        # Convert to API response with markdown
        return convert_to_api_response(response, include_markdown=True)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating user stories: {str(e)}"
        )


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
