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
    RAG_API_URL = os.getenv("RAG_API_URL", "")
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vectordb")
    
    # Fine-tuning Configuration
    FINETUNED_MODEL_PATH = os.getenv("FINETUNED_MODEL_PATH", "")
    FINETUNED_MODEL_API_URL = os.getenv("FINETUNED_MODEL_API_URL", "")
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
def query_rag(requirement: str, rag_source: str = "auto") -> Dict:
    """
    Query the dual RAG system for product specifications based on the requirement.
    
    Args:
        requirement: User's requirement text
        rag_source: Source to query - "auto", "existing", "design", or "both"
    """
    print(f"[RAG] Querying with requirement: {requirement[:50]}...")
    print(f"[RAG] Source: {rag_source}")
    
    if config.RAG_ENABLED and config.RAG_API_URL:
        try:
            import requests
            
            # Use /retrieve endpoint for dual RAG
            api_url = config.RAG_API_URL.rstrip('/')
            if not api_url.endswith('/retrieve'):
                api_url = f"{api_url}/retrieve"
            
            print(f"[RAG] Calling dual RAG endpoint: {api_url}")
            
            response = requests.post(
                api_url,
                json={
                    "question": requirement, 
                    "source": rag_source,
                    "top_k": 5
                },
                headers={"Content-Type": "application/json"},
                timeout=180  # Increased to 3 minutes for cold starts
            )
            
            if response.ok:
                result = response.json()
                documents = result.get("documents", [])
                sources_queried = result.get("sources_queried", [])
                detected_source = result.get("detected_source", "unknown")
                retrieval_time = result.get("retrieval_time", 0)
                
                # Build context from retrieved documents
                context_parts = []
                source_files = []
                for doc in documents:
                    content = doc.get("content", "")
                    metadata = doc.get("metadata", {})
                    filename = metadata.get("filename", metadata.get("source", "Unknown"))
                    collection = metadata.get("collection", "unknown")
                    
                    context_parts.append(f"[{collection}] {filename}:\n{content}")
                    source_files.append({"filename": filename, "collection": collection})
                
                full_context = "\n\n".join(context_parts)
                
                # Parse context to extract features
                features = []
                for line in full_context.split('\n'):
                    line = line.strip()
                    if line.startswith(('-', '*', '•')):
                        features.append(line.lstrip('-*• '))
                
                return {
                    "status": "success",
                    "specification": {
                        "title": "Product Specification (Dual RAG)",
                        "summary": (full_context[:300] + "...") if len(full_context) > 300 else full_context,
                        "features": features[:10] if features else ["See full context for details"],
                        "technical_requirements": ["Derived from dual RAG sources"],
                        "acceptance_criteria": ["See detailed context"],
                        "estimated_effort": "TBD",
                        "full_answer": full_context,
                        "context_retrieved": len(documents)
                    },
                    "source": "dual_rag",
                    "sources_queried": sources_queried,
                    "detected_source": detected_source,
                    "source_files": source_files,
                    "retrieval_time": retrieval_time,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"[RAG] Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[RAG] Exception: {e}")
            
    # Mock response fallback
    print("[RAG] Using mock response")
    
    # Simple keyword matching for mock data
    req_lower = requirement.lower()
    
    spec = {
        "title": "Auto Insurance Product Spec",
        "summary": "Specification based on Tokyo market requirements.",
        "features": [
            "User registration and login",
            "Policy selection interface",
            "Premium calculation engine"
        ],
        "technical_requirements": [
            "Secure database for user data",
            "Integration with payment gateway",
            "Responsive web design"
        ],
        "acceptance_criteria": [
            "User can create an account",
            "User can view policy details",
            "Premium is calculated correctly"
        ],
        "estimated_effort": "2 weeks"
    }
    
    if "mobile" in req_lower or "app" in req_lower:
        spec["title"] = "Mobile App Specification"
        spec["features"].append("Push notifications")
        spec["technical_requirements"].append("iOS and Android support")
        
    if "ai" in req_lower or "agent" in req_lower:
        spec["title"] = "AI Agent Integration Spec"
        spec["features"].append("Chat interface")
        spec["technical_requirements"].append("LLM integration")
        
    return {
        "status": "success",
        "specification": spec,
        "source": "mock_rag",
        "sources_queried": ["mock"],
        "detected_source": "mock",
        "source_files": [],
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
    print(f"[Fine-tuning] Querying {domain} model with requirement: {requirement[:50]}...")
    
    if config.FINETUNED_MODEL_API_URL:
        try:
            import requests
            print(f"[Fine-tuning] Calling remote endpoint: {config.FINETUNED_MODEL_API_URL}")
            
            # Map inputs to the API expected format
            payload = {
                "question": requirement,
                "context": f"Domain: {domain}. Provide specific insights for this domain."
            }
            
            response = requests.post(
                config.FINETUNED_MODEL_API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.ok:
                result = response.json()
                answer = result.get("answer", "")
                latency = result.get("latency_ms", 0)
                
                return {
                    "status": "success",
                    "insights": {
                        "domain": domain,
                        "recommendations": [line.strip('- ') for line in answer.split('\n') if line.strip().startswith('-')],
                        "compliance_notes": ["Generated by fine-tuned model"],
                        "full_response": answer
                    },
                    "source": "real_finetuned_model",
                    "latency_ms": latency,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"[Fine-tuning] Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[Fine-tuning] Exception: {e}")

    # Mock response fallback
    print("[Fine-tuning] Using mock response")
    
    insights = {
        "domain": domain,
        "recommendations": [
            "Ensure GDPR compliance for user data",
            "Implement audit logging for all transactions",
            "Use industry-standard encryption"
        ],
        "compliance_notes": [
            "ISO 27001 certification recommended",
            "Regular security assessments required"
        ]
    }
    
    if domain == "insurance":
        insights["recommendations"] = [
            "Verify policy holder identity (KYC)",
            "Calculate risk score based on actuarial tables",
            "Generate compliant policy documents"
        ]
        insights["compliance_notes"].append("Comply with local insurance regulations")
        
    elif domain == "finance":
        insights["recommendations"] = [
            "Implement PCI-DSS for payment processing",
            "Real-time fraud detection",
            "Double-entry bookkeeping"
        ]
        insights["compliance_notes"].append("Financial Services Agency guidelines")
        
    return {
        "status": "success",
        "insights": insights,
        "source": "mock_finetuned_model",
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

# Helper for Atlassian Document Format (ADF)
def create_adf_description(text: str) -> Dict:
    """Convert plain text to Atlassian Document Format (ADF)"""
    if not text:
        return {
            "version": 1,
            "type": "doc",
            "content": []
        }
        
    return {
        "version": 1,
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
        ]
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
            
            # Use ADF format for description in API v3
            description_adf = create_adf_description(description)
            
            epic_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description_adf,
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
    
    # Extract actual key if format is "KEY: Summary"
    actual_epic_key = epic_key.split(':')[0].strip()
    
    if use_real_jira():
        try:
            jira = get_jira_client()
            
            # Use ADF format for description in API v3
            description_adf = create_adf_description(description)
            
            story_dict = {
                'project': {'key': actual_epic_key.split('-')[0]},
                'summary': summary,
                'description': description_adf,
                'issuetype': {'name': 'Story'},
                # Link to Epic - field name varies by JIRA instance, usually 'parent' for Next-Gen or 'customfield_XXXXX'
                # Trying standard 'parent' first for modern JIRA Cloud
                'parent': {'key': actual_epic_key}
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

# ===== Helper Functions =====
def get_available_epics() -> List[str]:
    """Get list of available epics for dropdown"""
    epics_list = []
    
    if use_real_jira():
        try:
            # Use direct REST API call to avoid deprecated GET endpoint
            import requests
            from requests.auth import HTTPBasicAuth
            
            # Ensure no trailing slash in base URL
            base_url = config.JIRA_URL.rstrip('/')
            api_url = f"{base_url}/rest/api/3/search"
            
            auth = HTTPBasicAuth(config.JIRA_EMAIL, config.JIRA_API_TOKEN)
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # Search for all epics in project
            jql = f'project = "{config.JIRA_PROJECT_KEY}" AND issuetype = Epic ORDER BY created DESC'
            
            payload = {
                "jql": jql,
                "maxResults": 20,
                "fields": ["summary"]
            }
            
            response = requests.post(api_url, json=payload, headers=headers, auth=auth)
            
            # Handle 410 fallback
            if response.status_code == 410:
                api_url = f"{base_url}/rest/api/3/search/jql"
                response = requests.post(api_url, json=payload, headers=headers, auth=auth)
                
            if response.ok:
                data = response.json()
                issues = data.get("issues", [])
                if "issues" not in data and isinstance(data, list):
                    issues = data
                    
                for issue in issues:
                    key = issue.get("key")
                    summary = issue.get("fields", {}).get("summary", "")
                    epics_list.append(f"{key}: {summary}")
        except Exception as e:
            print(f"[JIRA] Error fetching epics: {e}")
    else:
        # Mock mode
        for epic in mock_epics:
            epics_list.append(f"{epic['key']}: {epic['summary']}")
            
    return epics_list

def refresh_epics_dropdown():
    """Refresh the choices for the epic dropdown"""
    choices = get_available_epics()
    if not choices:
        return gr.Dropdown(choices=[], value=None, label="No Epics Found - Please Create an Epic First")
    return gr.Dropdown(choices=choices, value=choices[0] if choices else None, label="Select Epic")

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
            with gr.Row():
                initial_epics = get_available_epics()
                story_epic = gr.Dropdown(
                    choices=initial_epics,
                    value=initial_epics[0] if initial_epics else None,
                    label="Select Epic" if initial_epics else "No Epics Found - Please Create an Epic First",
                    allow_custom_value=True # Allow typing if needed, or strictly selection
                )
                refresh_btn = gr.Button("🔄 Refresh Epics")
            
            story_summary = gr.Textbox(label="Story Summary", placeholder="Story title...")
            story_desc = gr.Textbox(
                label="Story Description",
                placeholder="Detailed description...",
                lines=5
            )
            story_points = gr.Number(label="Story Points (optional)", value=None)
            create_story_btn = gr.Button("Create User Story", variant="primary")
            story_output = gr.JSON(label="Created Story")
            
            refresh_btn.click(refresh_epics_dropdown, outputs=[story_epic])
            
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
            - API URL: `{config.RAG_API_URL or 'Not configured (using mock)'}`
            - Vector DB: `{config.VECTOR_DB_PATH}`
            
            **Fine-tuned Model:**
            - API URL: `{config.FINETUNED_MODEL_API_URL or 'Not configured (using mock)'}`
            - Type: `{config.FINETUNED_MODEL_TYPE}`
            
            **MCP Server:**
            - Port: `{config.MCP_PORT}`
            
            ---
            
            To enable real integrations, set environment variables in Hugging Face Spaces Secrets:
            ```bash
            RAG_ENABLED=true
            RAG_API_URL=https://your-modal-url.modal.run
            FINETUNED_MODEL_API_URL=https://your-modal-url.modal.run
            JIRA_URL=https://your-domain.atlassian.net
            JIRA_EMAIL=your-email@example.com
            JIRA_API_TOKEN=your-api-token
            JIRA_PROJECT_KEY=SCRUM
            ```
            """)
    
    return app

# ===== Main =====
if __name__ == "__main__":
    print("🚀 Starting AI Development Agent MCP Server...")
    print(f"📍 Server URL: http://localhost:{config.MCP_PORT}")
    print(f"🔧 Mode: {'Real JIRA' if use_real_jira() else 'Mock Mode'}")
    print(f"🧠 RAG: {'Enabled' if config.RAG_ENABLED else 'Mock'}")
    print(f"🎯 Fine-tuned Model: {'Enabled' if config.FINETUNED_MODEL_API_URL else 'Mock'}")
    
    app = create_gradio_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=config.MCP_PORT,
        share=False
    )
