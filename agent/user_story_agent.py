"""
User Story Agent - "Alex" the User Story Specialist

Role: Product Owner / Business Analyst
Persona: Alex - An experienced BA who converts requirements into user-centered stories

This agent queries the MCP server to transform user queries into structured,
INVEST-compliant user stories with acceptance criteria.
"""

import requests
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json


@dataclass
class UserStory:
    """Represents a single user story"""
    story_id: str
    title: str
    actor: str
    action: str
    benefit: str
    acceptance_criteria: List[str]
    story_points: int
    priority: str
    technical_notes: List[str] = field(default_factory=list)
    description: str = ""
    tasks: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        md = f"### {self.story_id}: {self.title}\n\n"
        md += f"**As a** {self.actor},  \n"
        md += f"**I want** {self.action},  \n"
        md += f"**So that** {self.benefit}.\n\n"
        
        if self.description:
            md += f"{self.description}\n\n"
            
        md += "**Acceptance Criteria:**\n"
        for i, criteria in enumerate(self.acceptance_criteria, 1):
            md += f"{i}. {criteria}\n"
        
        if self.tasks:
            md += "\n**Tasks:**\n"
            for task in self.tasks:
                md += f"- [ ] {task}\n"
            
        md += f"\n**Story Points:** {self.story_points}  \n"
        md += f"**Priority:** {self.priority}\n"
        
        if self.technical_notes:
            md += "\n**Technical Notes:**\n"
            for note in self.technical_notes:
                md += f"- {note}\n"
        
        return md



import datetime
import uuid
import json
from dataclasses import asdict

@dataclass
class ProductSpec:
    """Represents a product specification"""
    spec_id: str
    title: str
    summary: str
    target_audience: str
    key_features: List[str]
    technical_requirements: List[str]
    success_metrics: List[str]
    assumptions: List[str]
    dependencies: List[str] = field(default_factory=list)
    status: str = "draft"  # draft, approved
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    original_query: str = ""
    generated_stories: List[UserStory] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProductSpec':
        # Handle nested UserStory objects
        stories_data = data.get("generated_stories", [])
        stories = [UserStory(**s) if isinstance(s, dict) else s for s in stories_data]
        data["generated_stories"] = stories
        return cls(**data)


@dataclass
class UserStoryResponse:
    """Response from the agent"""
    stories: List[UserStory]
    raw_query: str
    domain: str
    mcp_source: str
    confidence: float
    warnings: List[str] = field(default_factory=list)
    spec_id: Optional[str] = None


class UserStoryAgent:
    """
    Alex - The User Story Specialist
    
    A persona-driven agent that transforms user queries into structured user stories
    by querying the MCP server (RAG + Fine-tuned models).
    """
    
    # Persona configuration
    PERSONA_NAME = "Alex"
    PERSONA_ROLE = "Senior Product Owner & Business Analyst"
    PERSONA_EXPERTISE = [
        "Converting technical requirements into user stories",
        "Applying INVEST principles",
        "Writing clear acceptance criteria",
        "Story point estimation",
        "Creating comprehensive product specifications"
    ]
    
    # MCP Server configuration
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "https://veeru-c-sdlc-mcp.hf.space")
    MCP_RAG_ENDPOINT = "/call/query_rag"
    MCP_FINETUNED_ENDPOINT = "/call/query_finetuned"
    
    # Storage configuration
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "specs")
    
    # Story templates
    STORY_PROMPT_TEMPLATE = """You are {persona_name}, a {persona_role}.

Your task is to transform the following user requirement into structured user stories.

USER REQUIREMENT:
{user_query}

Please analyze this requirement and create user stories following this format:

For each story:
1. Title: A clear, concise name
2. Actor: The user role (e.g., "customer", "admin", "agent")
3. Action: What they want to do
4. Benefit: Why they need this (the value)
5. Acceptance Criteria: 3-5 testable criteria in Given-When-Then format
6. Story Points: Estimate (1, 2, 3, 5, 8, 13)
7. Priority: High, Medium, or Low

Ensure each story follows INVEST principles:
- Independent: Can be developed separately
- Negotiable: Details can be discussed
- Valuable: Provides clear user value
- Estimable: Can be sized
- Small: Completable in one sprint
- Testable: Has clear acceptance criteria

Generate 2-5 user stories that cover the requirement comprehensively.
"""

    SPEC_PROMPT_TEMPLATE = """You are {persona_name}, a {persona_role}.

Your task is to create a comprehensive Product Specification based on the user requirement.

USER REQUIREMENT:
{user_query}

Create a structured specification including:
1. Title & Summary
2. Target Audience
3. Key Features (Functional requirements)
4. Technical Requirements (Non-functional)
5. Success Metrics (KPIs)
6. Assumptions & Constraints

Use the provided context to ensure accuracy.
"""
    
    def __init__(self):
        """Initialize the User Story Agent"""
        self.mcp_server_url = self.MCP_SERVER_URL
        
        # Ensure data directory exists
        os.makedirs(self.DATA_DIR, exist_ok=True)
        
        print(f"[{self.PERSONA_NAME}] User Story Agent initialized")
        print(f"[{self.PERSONA_NAME}] MCP Server: {self.mcp_server_url}")
        print(f"[{self.PERSONA_NAME}] Data Dir: {self.DATA_DIR}")
    
    # ===== Product Spec Workflow =====

    def create_draft_spec(
        self,
        user_query: str,
        use_rag: bool = True,
        use_finetuned: bool = True
    ) -> ProductSpec:
        """Create a draft product specification from a query"""
        print(f"\n[{self.PERSONA_NAME}] Creating draft spec for: {user_query[:50]}...")
        
        # 1. Gather Context
        rag_context, finetuned_context, _ = self._gather_context(user_query, use_rag, use_finetuned)
        
        # 2. Generate Spec Content (Mock LLM logic for now, would use LLM in prod)
        spec = self._generate_spec_content(user_query, rag_context, finetuned_context)
        
        # 3. Analyze Dependencies
        spec.dependencies = self._analyze_dependencies(spec)
        
        # 4. Store Draft
        self._store_spec(spec)
        
        return spec

    def get_spec(self, spec_id: str) -> Optional[ProductSpec]:
        """Retrieve a spec by ID"""
        filepath = os.path.join(self.DATA_DIR, f"{spec_id}.json")
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                data = json.load(f)
                return ProductSpec.from_dict(data)
        return None
    
    def list_specs(self) -> List[Dict]:
        """List all specs (summary)"""
        specs = []
        if os.path.exists(self.DATA_DIR):
            for filename in os.listdir(self.DATA_DIR):
                if filename.endswith(".json"):
                    with open(os.path.join(self.DATA_DIR, filename), "r") as f:
                        try:
                            data = json.load(f)
                            specs.append({
                                "spec_id": data["spec_id"],
                                "title": data["title"],
                                "status": data["status"],
                                "created_at": data["created_at"]
                            })
                        except:
                            pass
        return sorted(specs, key=lambda x: x["created_at"], reverse=True)

    def approve_spec(self, spec_id: str) -> Optional[ProductSpec]:
        """Approve a draft spec"""
        spec = self.get_spec(spec_id)
        if spec:
            spec.status = "approved"
            self._store_spec(spec)
            print(f"[{self.PERSONA_NAME}] Spec {spec_id} approved")
            return spec
        return None

    def generate_stories_from_spec(self, spec_id: str) -> UserStoryResponse:
        """Generate user stories from an APPROVED spec"""
        spec = self.get_spec(spec_id)
        if not spec:
            raise ValueError("Spec not found")
        
        if spec.status != "approved":
            raise ValueError("Spec must be approved before generating stories")
            
        print(f"[{self.PERSONA_NAME}] Generating stories from spec: {spec.title}")
        
        # Use the spec content as the rich context for story generation
        # We simulate the "enriched prompt" logic here
        
        # Generate stories based on spec features
        stories = []
        for i, feature in enumerate(spec.key_features[:1], 1):
            # Get customized details based on feature type
            details = self._get_feature_details(feature, spec.target_audience.split(',')[0].strip())
            
            stories.append(UserStory(
                story_id=f"US-{spec_id[:4]}-{i:03d}",
                title=f"Implement {feature}",
                description=details["description"],
                actor=spec.target_audience.split(',')[0].strip(), # Primary actor
                action=details["action"],
                benefit=details["benefit"],
                acceptance_criteria=details["acceptance_criteria"],
                tasks=details["tasks"],
                story_points=5,
                priority="High"
            ))
            
        # Update spec with generated stories
        spec.generated_stories = stories
        self._store_spec(spec)
        
        return UserStoryResponse(
            stories=stories,
            raw_query=spec.original_query,
            domain="product-spec",
            mcp_source="Spec-Driven",
            confidence=0.95,
            spec_id=spec.spec_id
        )

    # ===== Internal Helpers =====

    def _get_feature_details(self, feature: str, actor: str) -> Dict[str, Any]:
        """Get specific story details based on feature keywords"""
        feature_lower = feature.lower()
        
        # Default/Generic
        details = {
            "description": f"This story covers the implementation of {feature}. It ensures that {actor} can effectively utilize this capability to achieve their goals as outlined in the product specification.",
            "action": f"use {feature}",
            "benefit": "achieve my goals",
            "acceptance_criteria": [
                f"GIVEN the user is on the {feature} screen WHEN they interact THEN it should work",
                "GIVEN invalid input WHEN submitted THEN show error",
                "GIVEN successful completion WHEN finished THEN show success message"
            ],
            "tasks": [
                f"Design UI components for {feature}",
                f"Implement API endpoints for {feature}",
                f"Update database schema if required",
                f"Write unit and integration tests",
                f"Verify against acceptance criteria"
            ]
        }

        # Authentication
        if any(k in feature_lower for k in ["auth", "login", "sign up", "register", "password"]):
            details = {
                "description": "Secure authentication is the gateway to the application. This story covers the implementation of the login/registration flow, ensuring that only authorized users can access the system. It includes handling credentials securely, session management, and providing feedback for login failures.",
                "action": "log in to the system securely",
                "benefit": "access my account and protected resources",
                "acceptance_criteria": [
                    "GIVEN a user is on the login page WHEN they enter valid credentials THEN they should be redirected to the dashboard",
                    "GIVEN a user enters invalid credentials WHEN they submit THEN an error message 'Invalid username or password' should appear",
                    "GIVEN a user clicks 'Forgot Password' WHEN they enter their email THEN a reset link should be sent",
                    "GIVEN a logged-in user WHEN they click logout THEN their session should be terminated"
                ],
                "tasks": [
                    "Implement login form UI with validation",
                    "Set up JWT/Session authentication backend",
                    "Implement password hashing (bcrypt/argon2)",
                    "Create 'Forgot Password' flow and email triggers",
                    "Add rate limiting to prevent brute force attacks",
                    "Write integration tests for auth flows"
                ]
            }
        
        # Dashboard
        elif any(k in feature_lower for k in ["dashboard", "overview", "home"]):
            details = {
                "description": "The dashboard serves as the central hub for the user, providing a high-level overview of key metrics and quick access to recent activities. This story focuses on creating a responsive, widget-based layout that aggregates data from various sources.",
                "action": "view an overview of my activities and key metrics",
                "benefit": "quickly understand my current status and take action",
                "acceptance_criteria": [
                    "GIVEN the user logs in WHEN they land on the dashboard THEN they should see a summary of key metrics",
                    "GIVEN the dashboard loads WHEN data is being fetched THEN a loading skeleton should be displayed",
                    "GIVEN the user clicks on a widget WHEN interacted with THEN it should navigate to the detailed view",
                    "GIVEN the layout is viewed on mobile WHEN resized THEN widgets should stack vertically"
                ],
                "tasks": [
                    "Design responsive dashboard grid layout",
                    "Implement summary widgets (charts/counters)",
                    "Create API endpoints to aggregate dashboard data",
                    "Implement loading states and error handling for widgets",
                    "Add caching for expensive dashboard queries",
                    "Verify responsiveness on mobile devices"
                ]
            }

        # Reporting
        elif any(k in feature_lower for k in ["report", "analytics", "chart", "graph"]):
            details = {
                "description": "Reporting and analytics are crucial for data-driven decision making. This story covers the creation of interactive reports that allow users to visualize trends, filter data by date ranges, and export results for offline analysis.",
                "action": "generate and view reports on system data",
                "benefit": "analyze trends and make informed decisions",
                "acceptance_criteria": [
                    "GIVEN the user is on the reports page WHEN they select a date range THEN the charts should update accordingly",
                    "GIVEN a report is generated WHEN the user clicks 'Export' THEN a CSV/PDF file should be downloaded",
                    "GIVEN no data exists for a range WHEN filtered THEN an empty state message should be shown",
                    "GIVEN complex data WHEN visualized THEN tooltips should show exact values on hover"
                ],
                "tasks": [
                    "Integrate charting library (e.g., Chart.js, Recharts)",
                    "Implement backend aggregation queries for analytics",
                    "Create date range picker and filter components",
                    "Implement CSV/PDF export functionality",
                    "Optimize query performance for large datasets",
                    "Write unit tests for data aggregation logic"
                ]
            }
            
        # Settings
        elif any(k in feature_lower for k in ["setting", "config", "profile", "preference"]):
            details = {
                "description": "User settings allow for personalization and configuration of the system. This story covers the implementation of a settings management interface where users can update their profile, change preferences, and manage security settings.",
                "action": "manage my profile and application preferences",
                "benefit": "customize the application to my needs",
                "acceptance_criteria": [
                    "GIVEN the user changes a setting WHEN saved THEN the change should persist immediately",
                    "GIVEN the user edits their profile WHEN they upload a new avatar THEN the image should be optimized and stored",
                    "GIVEN invalid data is entered WHEN saving THEN field-level validation errors should appear",
                    "GIVEN critical changes (e.g., email) WHEN requested THEN a re-authentication prompt should appear"
                ],
                "tasks": [
                    "Create settings navigation and layout",
                    "Implement profile update form with validation",
                    "Set up file upload for user avatars",
                    "Implement preference storage in database",
                    "Add audit logging for configuration changes",
                    "Verify data persistence and validation"
                ]
            }
            
        # Workflow/Core Features
        elif any(k in feature_lower for k in ["workflow", "process", "core", "claim", "application"]):
            details = {
                "description": f"This story implements the core {feature} workflow, which is the heart of the application. It involves a multi-step process where the user inputs data, the system validates it, and a final state is reached.",
                "action": f"complete the {feature} workflow",
                "benefit": "successfully submit my request/data",
                "acceptance_criteria": [
                    "GIVEN the user starts the workflow WHEN they complete step 1 THEN they should proceed to step 2",
                    "GIVEN the user leaves the workflow mid-way WHEN they return THEN their progress should be saved (draft)",
                    "GIVEN all steps are completed WHEN submitted THEN a confirmation summary should be shown",
                    "GIVEN validation fails at any step THEN clear inline errors should be displayed"
                ],
                "tasks": [
                    "Design multi-step wizard UI/UX",
                    "Implement state management for workflow progress",
                    "Create API endpoints for saving drafts and final submission",
                    "Implement complex form validation logic",
                    "Add progress bar and navigation controls",
                    "Write end-to-end tests for the complete workflow"
                ]
            }

        return details

    def _gather_context(self, query, use_rag, use_finetuned):
        """Helper to gather RAG and FT context"""
        rag_context = ""
        finetuned_context = ""
        mcp_sources = []
        
        if use_rag:
            print(f"[{self.PERSONA_NAME}] Querying RAG for product context...")
            rag_result = self._query_mcp_rag(query)
            if rag_result:
                rag_context = rag_result.get("context", "")
                mcp_sources.append("RAG")
        
        if use_finetuned:
            print(f"[{self.PERSONA_NAME}] Querying fine-tuned model for domain insights...")
            ft_result = self._query_mcp_finetuned(query)
            if ft_result:
                finetuned_context = ft_result.get("context", "")
                mcp_sources.append("Fine-tuned")
                
        return rag_context, finetuned_context, mcp_sources

    def _generate_spec_content(self, query: str, rag_context: str, ft_context: str) -> ProductSpec:
        """Generate the actual spec object (Mock LLM logic)"""
        
        # In a real implementation, this would call an LLM with the SPEC_PROMPT_TEMPLATE
        # For now, we use heuristics and extracted context
        
        title = f"Product Spec: {query[:30]}..."
        summary = f"Comprehensive specification for: {query}. Leveraging insights from existing products and design docs."
        
        features = [
            "User Authentication & Authorization",
            "Dashboard & Overview",
            "Core Workflow Implementation",
            "Reporting & Analytics",
            "Settings & Configuration"
        ]
        
        # Add RAG-specific features if available
        if "login" in query.lower() or "auth" in query.lower():
            features.append("Multi-factor Authentication (MFA)")
        
        return ProductSpec(
            spec_id=str(uuid.uuid4())[:8],
            title=title,
            summary=summary,
            target_audience="Customers, Administrators, Agents",
            key_features=features,
            technical_requirements=[
                "Secure API endpoints",
                "Responsive Web Design",
                "GDPR/Privacy Compliance"
            ],
            success_metrics=[
                "User adoption rate > 50%",
                "System uptime > 99.9%"
            ],
            assumptions=[
                "Users have internet access",
                "Backend API is available"
            ],
            original_query=query
        )

    def _analyze_dependencies(self, spec: ProductSpec) -> List[str]:
        """Analyze dependencies against other specs"""
        dependencies = []
        # Simple check: if other specs exist, maybe we depend on them?
        # In reality, this would use semantic similarity
        existing_specs = self.list_specs()
        if existing_specs:
            dependencies.append(f"Potential integration with {existing_specs[0]['title']}")
        return dependencies

    def _store_spec(self, spec: ProductSpec):
        """Save spec to disk"""
        filepath = os.path.join(self.DATA_DIR, f"{spec.spec_id}.json")
        with open(filepath, "w") as f:
            json.dump(spec.to_dict(), f, indent=2)
        print(f"[{self.PERSONA_NAME}] Saved spec to {filepath}")

    # ===== Legacy / Direct Story Generation (Keep for backward compatibility) =====

    def transform_to_user_stories(
        self,
        user_query: str,
        use_rag: bool = True,
        use_finetuned: bool = True
    ) -> UserStoryResponse:
        """
        Transform a user query into structured user stories
        
        Args:
            user_query: The user's requirement description
            use_rag: Whether to query RAG for context
            use_finetuned: Whether to query fine-tuned model
            
        Returns:
            UserStoryResponse with structured stories
        """
        print(f"\n[{self.PERSONA_NAME}] Processing requirement...")
        print(f"[{self.PERSONA_NAME}] Query: {user_query[:100]}...")
        
        # 1. Gather Context
        rag_context, finetuned_context, mcp_sources = self._gather_context(user_query, use_rag, use_finetuned)
        domain = "general" # simplified
        
        # Build enriched prompt
        enriched_prompt = self._build_enriched_prompt(
            user_query,
            rag_context,
            finetuned_context
        )
        
        # Parse response into structured stories
        print(f"[{self.PERSONA_NAME}] Generating user stories...")
        stories = self._generate_stories(
            user_query,
            enriched_prompt,
            rag_context,
            finetuned_context
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(stories, rag_context, finetuned_context)
        
        # Generate warnings
        warnings = []
        if not rag_context:
            warnings.append("No RAG context available - stories may lack product-specific details")
        if not finetuned_context:
            warnings.append("No domain insights available - estimates may be less accurate")
        
        mcp_source = " + ".join(mcp_sources) if mcp_sources else "Fallback"
        
        print(f"[{self.PERSONA_NAME}] Generated {len(stories)} user stories (confidence: {confidence:.0%})")
        
        return UserStoryResponse(
            stories=stories,
            raw_query=user_query,
            domain=domain,
            mcp_source=mcp_source,
            confidence=confidence,
            warnings=warnings
        )
    
    def _query_mcp_rag(self, query: str) -> Optional[Dict[str, Any]]:
        """Query MCP RAG endpoint"""
        try:
            response = requests.post(
                f"{self.mcp_server_url}{self.MCP_RAG_ENDPOINT}",
                json={"data": [query]},
                timeout=60
            )
            
            if response.ok:
                event_data = response.json()
                event_id = event_data.get("event_id")
                
                if event_id:
                    result_response = requests.get(
                        f"{self.mcp_server_url}{self.MCP_RAG_ENDPOINT}/{event_id}",
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
                                            spec = result.get("specification", {})
                                            return {
                                                "context": spec.get("full_answer", ""),
                                                "features": spec.get("features", []),
                                                "requirements": spec.get("technical_requirements", [])
                                            }
        except Exception as e:
            print(f"[{self.PERSONA_NAME}] RAG query error: {e}")
        
        return None
    
    def _query_mcp_finetuned(self, query: str, domain: str = "general") -> Optional[Dict[str, Any]]:
        """Query MCP fine-tuned model endpoint"""
        try:
            response = requests.post(
                f"{self.mcp_server_url}{self.MCP_FINETUNED_ENDPOINT}",
                json={"data": [query, domain]},
                timeout=60
            )
            
            if response.ok:
                event_data = response.json()
                event_id = event_data.get("event_id")
                
                if event_id:
                    result_response = requests.get(
                        f"{self.mcp_server_url}{self.MCP_FINETUNED_ENDPOINT}/{event_id}",
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
                                            insights = result.get("insights", {})
                                            return {
                                                "context": insights.get("full_response", ""),
                                                "domain": insights.get("domain", "general"),
                                                "recommendations": insights.get("recommendations", [])
                                            }
        except Exception as e:
            print(f"[{self.PERSONA_NAME}] Fine-tuned query error: {e}")
        
        return None
    
    def _build_enriched_prompt(
        self,
        user_query: str,
        rag_context: str,
        finetuned_context: str
    ) -> str:
        """Build enriched prompt with MCP context"""
        prompt = self.STORY_PROMPT_TEMPLATE.format(
            persona_name=self.PERSONA_NAME,
            persona_role=self.PERSONA_ROLE,
            user_query=user_query
        )
        
        if rag_context:
            prompt += f"\n\nPRODUCT CONTEXT (from RAG):\n{rag_context[:500]}\n"
        
        if finetuned_context:
            prompt += f"\n\nDOMAIN INSIGHTS (from fine-tuned model):\n{finetuned_context[:500]}\n"
        
        return prompt
    
    def _generate_stories(
        self,
        user_query: str,
        prompt: str,
        rag_context: str,
        finetuned_context: str
    ) -> List[UserStory]:
        """Generate structured user stories (with fallback logic)"""
        
        # For now, create intelligent fallback stories based on query analysis
        # In production, this would call an LLM with the enriched prompt
        
        stories = []
        
        # Analyze query to extract actors and actions
        query_lower = user_query.lower()
        
        # Determine primary actor
        if "admin" in query_lower or "administrator" in query_lower:
            primary_actor = "administrator"
        elif "agent" in query_lower or "staff" in query_lower:
            primary_actor = "agent"
        elif "customer" in query_lower:
            primary_actor = "customer"
        elif "user" in query_lower:
            primary_actor = "user"
        else:
            primary_actor = "user"
        
        # Extract action keywords
        action_words = [w for w in query_lower.split() if len(w) > 4][:5]
        action_summary = " ".join(action_words) if action_words else "use the system"
        
        # Story 1: Main feature
        stories.append(UserStory(
            story_id="US-001",
            title=f"{user_query[:50]}..." if len(user_query) > 50 else user_query,
            description=f"As a {primary_actor}, I need to {action_summary}. This feature is critical for the workflow and allows users to complete their tasks efficiently.",
            actor=primary_actor,
            action=action_summary,
            benefit="I can accomplish my task efficiently and effectively",
            acceptance_criteria=[
                f"GIVEN the {primary_actor} is authenticated WHEN they access the feature THEN the system SHALL display the interface",
                "GIVEN valid input is provided WHEN the action is initiated THEN the system SHALL process it successfully",
                "GIVEN an error occurs WHEN processing THEN the system SHALL display a clear error message",
            ],
            tasks=[
                "Create frontend view",
                "Implement backend logic",
                "Add validation rules",
                "Write automated tests"
            ],
            story_points=5,
            priority="High",
            technical_notes=["Implement input validation", "Add error handling", "Ensure security"]
        ))
        
        # Story 2: Admin/Management (Disabled for single story request)
        # if primary_actor != "administrator":
        #     stories.append(UserStory(...))
        
        # Story 3: Error handling & edge cases
        # Story 3: Error handling & edge cases (Disabled for single story request)
        # stories.append(UserStory(...))
        
        return stories
    
    def _calculate_confidence(
        self,
        stories: List[UserStory],
        rag_context: str,
        finetuned_context: str
    ) -> float:
        """Calculate confidence score"""
        confidence = 0.5  # Base
        
        if stories:
            confidence += 0.2
        if rag_context:
            confidence += 0.15
        if finetuned_context:
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    def format_all_stories_markdown(self, response: UserStoryResponse) -> str:
        """Format all stories as markdown document"""
        md = f"# User Stories: {response.raw_query[:60]}\n\n"
        md += f"**Domain:** {response.domain}  \n"
        md += f"**Source:** {response.mcp_source}  \n"
        md += f"**Confidence:** {response.confidence:.0%}  \n\n"
        
        if response.warnings:
            md += "## ⚠️ Warnings\n"
            for warning in response.warnings:
                md += f"- {warning}\n"
            md += "\n"
        
        md += "---\n\n"
        
        for story in response.stories:
            md += story.to_markdown()
            md += "\n---\n\n"
        
        md += f"*Generated by {self.PERSONA_NAME}, {self.PERSONA_ROLE}*\n"
        
        return md


# Convenience function
def create_user_stories(user_query: str) -> UserStoryResponse:
    """
    Convenience function to create user stories from a query
    
    Args:
        user_query: The user's requirement description
        
    Returns:
        UserStoryResponse with structured stories
    """
    agent = UserStoryAgent()
    return agent.transform_to_user_stories(user_query)


if __name__ == "__main__":
    # Example usage
    agent = UserStoryAgent()
    
    test_query = "I need a feature for customers to file auto insurance claims online"
    
    print(f"\n{'='*60}")
    print(f"Testing {agent.PERSONA_NAME}'s User Story Agent")
    print(f"{'='*60}\n")
    
    # Test 1: Create Draft Spec
    spec = agent.create_draft_spec(test_query)
    print(f"Draft Spec Created: {spec.spec_id} - {spec.title}")
    
    # Test 2: Approve Spec
    agent.approve_spec(spec.spec_id)
    
    # Test 3: Generate Stories from Spec
    response = agent.generate_stories_from_spec(spec.spec_id)
    print(f"Generated {len(response.stories)} stories from spec")

