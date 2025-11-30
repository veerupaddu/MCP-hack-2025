import gradio as gr
from typing import Dict, List, Optional
import json
from datetime import datetime
import os
from difflib import SequenceMatcher
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ===== Configuration =====
class Config:
    # JIRA Configuration (optional - uses mock if not provided)
    JIRA_URL = os.getenv("JIRA_URL", "")
    JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
    JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "PROJ")
    
    # RAG Configuration
    RAG_ENABLED = os.getenv("RAG_ENABLED", "false").lower() == "true"
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vectordb")
    
    # Fine-tuning Configuration
    FINETUNED_MODEL_PATH = os.getenv("FINETUNED_MODEL_PATH", "")
    FINETUNED_MODEL_TYPE = os.getenv("FINETUNED_MODEL_TYPE", "general")
    
    # MCP Server
    MCP_PORT = int(os.getenv("MCP_PORT", "7860"))

config = Config()

# ===== Mock Data Storage =====
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

mock_user_stories = []

# ===== Helper Functions =====
def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two strings (0.0 to 1.0)"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def use_real_jira() -> bool:
    """Check if real JIRA credentials are configured"""
    return bool(config.JIRA_URL and config.JIRA_EMAIL and config.JIRA_API_TOKEN)

# ===== RAG Functions =====
def query_rag(requirement: str) -> Dict:
    """
    Query RAG system for relevant context and generate product specification.
    
    Args:
        requirement: User's requirement text
        
    Returns:
        Dict with specification, context, and recommendations
    """
    print(f"[RAG] Querying with requirement: {requirement[:100]}...")
    
    if config.RAG_ENABLED:
        # TODO: Implement real RAG query with ChromaDB/Pinecone
        # from langchain.vectorstores import Chroma
        # vectordb = Chroma(persist_directory=config.VECTOR_DB_PATH)
        # results = vectordb.similarity_search(requirement, k=5)
        pass
    
    # Mock RAG response
    specification = {
        "title": "Generated Product Specification",
        "summary": f"Product specification for: {requirement[:100]}",
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

# ===== Fine-tuning Functions =====
def query_finetuned_model(requirement: str, domain: str = "general") -> Dict:
    """
    Query fine-tuned model for domain-specific insights.
    
    Args:
        requirement: User's requirement text
        domain: Domain type (insurance, finance, healthcare, etc.)
        
    Returns:
        Dict with domain-specific recommendations and insights
    """
    print(f"[Fine-tuning] Querying {domain} model with requirement: {requirement[:100]}...")
    
    if config.FINETUNED_MODEL_PATH:
        # TODO: Load and query real fine-tuned model
        # from transformers import AutoModelForCausalLM, AutoTokenizer
        # model = AutoModelForCausalLM.from_pretrained(config.FINETUNED_MODEL_PATH)
        pass
    
    # Mock fine-tuned model response
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
    
    insights = domain_insights.get(domain, domain_insights["general"])
    
    return {
        "status": "success",
        "domain": domain,
        "insights": insights,
        "recommendations": [
            f"Consider {domain}-specific compliance requirements",
            "Implement domain-specific validation rules",
            "Add specialized error handling",
            "Include domain expert review in workflow"
        ],
        "confidence_score": 0.78,
        "source": "mock_finetuned" if not config.FINETUNED_MODEL_PATH else "real_finetuned",
        "timestamp": datetime.now().isoformat()
    }

from jira import JIRA

# ... (imports remain the same)

# ===== JIRA Functions =====
def get_jira_client():
    """Get authenticated JIRA client"""
    if not use_real_jira():
        return None
    return JIRA(
        server=config.JIRA_URL,
        basic_auth=(config.JIRA_EMAIL, config.JIRA_API_TOKEN),
        options={"rest_api_version": "3"}
    )

def search_jira_epics(keywords: str, similarity_threshold: float = 0.6) -> Dict:
    """
    Search for existing JIRA epics matching the keywords.
    """
    print(f"[JIRA] Searching epics with keywords: {keywords}")
    
    if use_real_jira():
        try:
            # Use direct REST API call to avoid deprecated GET endpoint
            import requests
            from requests.auth import HTTPBasicAuth
            
            jql = f'project = "{config.JIRA_PROJECT_KEY}" AND issuetype = Epic AND (summary ~ "{keywords}" OR description ~ "{keywords}")'
            print(f"[JIRA] JQL: {jql}")
            
            # Ensure no trailing slash in base URL
            base_url = config.JIRA_URL.rstrip('/')
            
            # Try standard POST search endpoint first
            api_url = f"{base_url}/rest/api/3/search"
            
            auth = HTTPBasicAuth(config.JIRA_EMAIL, config.JIRA_API_TOKEN)
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            payload = {
                "jql": jql,
                "maxResults": 5,
                "fields": ["summary", "description", "status", "created"]
            }
            
            print(f"[JIRA] POST to {api_url}")
            response = requests.post(api_url, json=payload, headers=headers, auth=auth)
            
            # If standard search fails with 410, try the specific endpoint mentioned in error
            if response.status_code == 410:
                print("[JIRA] 410 Error, trying /rest/api/3/search/jql endpoint...")
                api_url = f"{base_url}/rest/api/3/search/jql"
                # The /search/jql endpoint uses a slightly different payload structure
                # It expects 'jql' as a query parameter or in body? 
                # Actually, strictly following the error message recommendation.
                # Documentation says POST /rest/api/3/search/jql takes { "jql": "...", ... } just like search
                print(f"[JIRA] POST to {api_url}")
                response = requests.post(api_url, json=payload, headers=headers, auth=auth)
                
            if not response.ok:
                print(f"[JIRA] Error response: {response.text}")
                
            response.raise_for_status()
            data = response.json()
            # /search/jql returns { "issues": [...] } just like /search?
            # Or does it return a different structure?
            # Standard /search returns { "issues": [...], "total": ... }
            # Let's handle both cases safely
            issues = data.get("issues", [])
            if "issues" not in data and isinstance(data, list):
                # Some endpoints return list directly
                issues = data
            
            matching_epics = []
            for issue in issues:
                fields = issue.get("fields", {})
                # Calculate similarity for ranking
                summary_text = fields.get("summary", "")
                desc_text = fields.get("description", "")
                # Description can be complex object in v3 (ADF), handle string or dict
                if isinstance(desc_text, dict):
                    # Simplified handling for ADF - just use summary for similarity if desc is complex
                    desc_text = "" 
                
                summary_sim = calculate_similarity(keywords, summary_text)
                desc_sim = calculate_similarity(keywords, str(desc_text))
                max_sim = max(summary_sim, desc_sim)
                
                matching_epics.append({
                    "key": issue.get("key"),
                    "summary": summary_text,
                    "description": str(desc_text)[:200] + "..." if desc_text else "",
                    "status": str(fields.get("status", {}).get("name", "Unknown")),
                    "created": fields.get("created"),
                    "url": f"{config.JIRA_URL}/browse/{issue.get('key')}",
                    "similarity_score": round(max_sim, 2)
                })
            
            # Sort by similarity
            matching_epics.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return {
                "status": "success",
                "count": len(matching_epics),
                "epics": matching_epics,
                "source": "real_jira",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[JIRA] Search error: {e}")
            return {"status": "error", "message": str(e)}
    
    # Mock search - find similar epics
    matching_epics = []
    for epic in mock_epics:
        # Calculate similarity with summary and description
        summary_sim = calculate_similarity(keywords, epic["summary"])
        desc_sim = calculate_similarity(keywords, epic["description"])
        max_sim = max(summary_sim, desc_sim)
        
        if max_sim >= similarity_threshold:
            matching_epics.append({
                **epic,
                "similarity_score": round(max_sim, 2)
            })
    
    # Sort by similarity
    matching_epics.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    return {
        "status": "success",
        "count": len(matching_epics),
        "epics": matching_epics,
        "source": "mock_jira",
        "timestamp": datetime.now().isoformat()
    }

def create_jira_epic(summary: str, description: str, project_key: str = None) -> Dict:
    """
    Create a new JIRA epic.
    """
    project_key = project_key or config.JIRA_PROJECT_KEY
    print(f"[JIRA] Creating epic: {summary}")
    
    if use_real_jira():
        try:
            jira = get_jira_client()
            epic_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': 'Epic'},
            }
            new_issue = jira.create_issue(fields=epic_dict)
            print(f"[JIRA] Created epic: {new_issue.key}")
            
            return {
                "status": "success",
                "epic": {
                    "key": new_issue.key,
                    "summary": summary,
                    "description": description,
                    "url": f"{config.JIRA_URL}/browse/{new_issue.key}"
                },
                "source": "real_jira",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[JIRA] Create error: {e}")
            return {"status": "error", "message": str(e)}
    
    # Mock epic creation
    epic_key = f"{project_key}-{len(mock_epics) + 100}"
    new_epic = {
        "key": epic_key,
        "summary": summary,
        "description": description,
        "status": "To Do",
        "created": datetime.now().strftime("%Y-%m-%d"),
        "url": f"{config.JIRA_URL or 'https://mock-jira.atlassian.net'}/browse/{epic_key}"
    }
    
    mock_epics.append(new_epic)
    
    return {
        "status": "success",
        "epic": new_epic,
        "source": "mock_jira",
        "timestamp": datetime.now().isoformat()
    }

def create_jira_user_story(epic_key: str, summary: str, description: str, 
                          story_points: int = None) -> Dict:
    """
    Create a new JIRA user story linked to an epic.
    """
    print(f"[JIRA] Creating user story under {epic_key}: {summary}")
    
    if use_real_jira():
        try:
            jira = get_jira_client()
            story_dict = {
                'project': {'key': epic_key.split('-')[0]},
                'summary': summary,
                'description': description,
                'issuetype': {'name': 'Story'},
                # Link to Epic - field name varies by JIRA instance, usually 'parent' for Next-Gen or 'customfield_XXXXX'
                # Trying standard 'parent' first for modern JIRA Cloud
                'parent': {'key': epic_key}
            }
            
            new_issue = jira.create_issue(fields=story_dict)
            print(f"[JIRA] Created story: {new_issue.key}")
            
            return {
                "status": "success",
                "story": {
                    "key": new_issue.key,
                    "summary": summary,
                    "url": f"{config.JIRA_URL}/browse/{new_issue.key}"
                },
                "source": "real_jira",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[JIRA] Create story error: {e}")
            return {"status": "error", "message": str(e)}
    
    # Mock story creation
    story_key = f"{epic_key.split('-')[0]}-{len(mock_user_stories) + 200}"
    new_story = {
        "key": story_key,
        "epic_key": epic_key,
        "summary": summary,
        "description": description,
        "story_points": story_points,
        "status": "To Do",
        "created": datetime.now().strftime("%Y-%m-%d"),
        "url": f"{config.JIRA_URL or 'https://mock-jira.atlassian.net'}/browse/{story_key}"
    }
    
    mock_user_stories.append(new_story)
    
    return {
        "status": "success",
        "story": new_story,
        "source": "mock_jira",
        "timestamp": datetime.now().isoformat()
    }

# ===== Gradio Interface =====
def create_gradio_interface():
    """Create Gradio interface for MCP server"""
    
    with gr.Blocks(title="AI Development Agent MCP Server") as app:
        gr.Markdown("# 🤖 AI Development Agent MCP Server")
        gr.Markdown("Unified interface for RAG, Fine-tuning, and JIRA integration")
        
        with gr.Tab("RAG Query"):
            with gr.Row():
                rag_input = gr.Textbox(
                    label="Requirement",
                    placeholder="Enter your requirement...",
                    lines=5
                )
            rag_btn = gr.Button("Query RAG System", variant="primary")
            rag_output = gr.JSON(label="RAG Response")
            
            rag_btn.click(query_rag, inputs=[rag_input], outputs=[rag_output])
        
        with gr.Tab("Fine-tuned Model"):
            with gr.Row():
                ft_input = gr.Textbox(
                    label="Requirement",
                    placeholder="Enter your requirement...",
                    lines=5
                )
                ft_domain = gr.Dropdown(
                    choices=["general", "insurance", "finance", "healthcare"],
                    value="general",
                    label="Domain"
                )
            ft_btn = gr.Button("Query Fine-tuned Model", variant="primary")
            ft_output = gr.JSON(label="Fine-tuned Model Response")
            
            ft_btn.click(
                query_finetuned_model,
                inputs=[ft_input, ft_domain],
                outputs=[ft_output]
            )
        
        with gr.Tab("JIRA - Search Epics"):
            search_input = gr.Textbox(
                label="Search Keywords",
                placeholder="Enter keywords to search...",
                lines=2
            )
            search_threshold = gr.Slider(
                minimum=0.0,
                maximum=1.0,
                value=0.6,
                step=0.1,
                label="Similarity Threshold"
            )
            search_btn = gr.Button("Search Epics", variant="primary")
            search_output = gr.JSON(label="Search Results")
            
            search_btn.click(
                search_jira_epics,
                inputs=[search_input, search_threshold],
                outputs=[search_output]
            )
        
        with gr.Tab("JIRA - Create Epic"):
            epic_summary = gr.Textbox(label="Epic Summary", placeholder="Epic title...")
            epic_desc = gr.Textbox(
                label="Epic Description",
                placeholder="Detailed description...",
                lines=5
            )
            epic_project = gr.Textbox(
                label="Project Key",
                value=config.JIRA_PROJECT_KEY,
                placeholder="PROJ"
            )
            create_epic_btn = gr.Button("Create Epic", variant="primary")
            epic_output = gr.JSON(label="Created Epic")
            
            create_epic_btn.click(
                create_jira_epic,
                inputs=[epic_summary, epic_desc, epic_project],
                outputs=[epic_output]
            )
        
        with gr.Tab("JIRA - Create User Story"):
            story_epic = gr.Textbox(label="Epic Key", placeholder="PROJ-100")
            story_summary = gr.Textbox(label="Story Summary", placeholder="Story title...")
            story_desc = gr.Textbox(
                label="Story Description",
                placeholder="Detailed description...",
                lines=5
            )
            story_points = gr.Number(label="Story Points (optional)", value=None)
            create_story_btn = gr.Button("Create User Story", variant="primary")
            story_output = gr.JSON(label="Created Story")
            
            create_story_btn.click(
                create_jira_user_story,
                inputs=[story_epic, story_summary, story_desc, story_points],
                outputs=[story_output]
            )
        
        with gr.Tab("Configuration"):
            gr.Markdown(f"""
            ### Current Configuration
            
            **JIRA:**
            - URL: `{config.JIRA_URL or 'Not configured (using mock)'}` 
            - Project: `{config.JIRA_PROJECT_KEY}`
            - Mode: `{'Real JIRA' if use_real_jira() else 'Mock Mode'}`
            
            **RAG:**
            - Enabled: `{config.RAG_ENABLED}`
            - Vector DB: `{config.VECTOR_DB_PATH}`
            
            **Fine-tuned Model:**
            - Path: `{config.FINETUNED_MODEL_PATH or 'Not configured (using mock)'}`
            - Type: `{config.FINETUNED_MODEL_TYPE}`
            
            **MCP Server:**
            - Port: `{config.MCP_PORT}`
            
            ---
            
            To enable real integrations, set environment variables:
            ```bash
            export JIRA_URL="https://your-domain.atlassian.net"
            export JIRA_EMAIL="your-email@example.com"
            export JIRA_API_TOKEN="your-api-token"
            export JIRA_PROJECT_KEY="PROJ"
            export RAG_ENABLED="true"
            export FINETUNED_MODEL_PATH="/path/to/model"
            ```
            """)
    
    return app

# ===== Main =====
if __name__ == "__main__":
    print("🚀 Starting AI Development Agent MCP Server...")
    print(f"📍 Server URL: http://localhost:{config.MCP_PORT}")
    print(f"🔧 Mode: {'Real JIRA' if use_real_jira() else 'Mock Mode'}")
    print(f"🧠 RAG: {'Enabled' if config.RAG_ENABLED else 'Mock'}")
    print(f"🎯 Fine-tuned Model: {'Loaded' if config.FINETUNED_MODEL_PATH else 'Mock'}")
    
    app = create_gradio_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=config.MCP_PORT,
        share=False
    )
