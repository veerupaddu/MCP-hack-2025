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
    """Represents a structured user story"""
    story_id: str
    title: str
    actor: str  # Who (user role)
    action: str  # What (feature/goal)
    benefit: str  # Why (value/reason)
    acceptance_criteria: List[str] = field(default_factory=list)
    story_points: int = 3
    priority: str = "Medium"
    technical_notes: List[str] = field(default_factory=list)
    
    def to_markdown(self) -> str:
        """Format story as markdown"""
        md = f"### {self.story_id}: {self.title}\n\n"
        md += f"**As a** {self.actor},  \n"
        md += f"**I want** {self.action},  \n"
        md += f"**So that** {self.benefit}.\n\n"
        
        if self.acceptance_criteria:
            md += "**Acceptance Criteria:**\n"
            for i, criteria in enumerate(self.acceptance_criteria, 1):
                md += f"{i}. {criteria}\n"
            md += "\n"
        
        md += f"**Story Points:** {self.story_points}  \n"
        md += f"**Priority:** {self.priority}\n"
        
        if self.technical_notes:
            md += "\n**Technical Notes:**\n"
            for note in self.technical_notes:
                md += f"- {note}\n"
        
        return md


@dataclass
class UserStoryResponse:
    """Response from the agent"""
    stories: List[UserStory]
    raw_query: str
    domain: str
    mcp_source: str
    confidence: float
    warnings: List[str] = field(default_factory=list)


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
        "Story point estimation"
    ]
    
    # MCP Server configuration
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "https://veeru-c-sdlc-mcp.hf.space")
    MCP_RAG_ENDPOINT = "/call/query_rag"
    MCP_FINETUNED_ENDPOINT = "/call/query_finetuned"
    
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
    
    def __init__(self):
        """Initialize the User Story Agent"""
        self.mcp_server_url = self.MCP_SERVER_URL
        print(f"[{self.PERSONA_NAME}] User Story Agent initialized")
        print(f"[{self.PERSONA_NAME}] MCP Server: {self.mcp_server_url}")
    
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
        
        # Collect context from MCP
        rag_context = ""
        finetuned_context = ""
        domain = "general"
        mcp_sources = []
        
        if use_rag:
            print(f"[{self.PERSONA_NAME}] Querying RAG for product context...")
            rag_result = self._query_mcp_rag(user_query)
            if rag_result:
                rag_context = rag_result.get("context", "")
                mcp_sources.append("RAG")
        
        if use_finetuned:
            print(f"[{self.PERSONA_NAME}] Querying fine-tuned model for domain insights...")
            ft_result = self._query_mcp_finetuned(user_query)
            if ft_result:
                finetuned_context = ft_result.get("context", "")
                domain = ft_result.get("domain", "general")
                mcp_sources.append("Fine-tuned")
        
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
            actor=primary_actor,
            action=action_summary,
            benefit="I can accomplish my task efficiently and effectively",
            acceptance_criteria=[
                f"GIVEN the {primary_actor} is authenticated WHEN they access the feature THEN the system SHALL display the interface",
                "GIVEN valid input is provided WHEN the action is initiated THEN the system SHALL process it successfully",
                "GIVEN an error occurs WHEN processing THEN the system SHALL display a clear error message",
            ],
            story_points=5,
            priority="High",
            technical_notes=["Implement input validation", "Add error handling", "Ensure security"]
        ))
        
        # Story 2: Admin/Management
        if primary_actor != "administrator":
            stories.append(UserStory(
                story_id="US-002",
                title=f"Admin Management for {user_query[:30]}",
                actor="administrator",
                action=f"manage and monitor {action_summary}",
                benefit="I can maintain system integrity and user experience",
                acceptance_criteria=[
                    "GIVEN the administrator is logged in WHEN they access the management panel THEN all relevant data SHALL be displayed",
                    "GIVEN the administrator modifies settings WHEN changes are saved THEN the system SHALL apply them immediately",
                ],
                story_points=3,
                priority="Medium",
                technical_notes=["Implement admin authorization", "Add audit logging"]
            ))
        
        # Story 3: Error handling & edge cases
        stories.append(UserStory(
            story_id="US-003",
            title="Error Handling and Validation",
            actor=primary_actor,
            action="receive clear feedback when errors occur",
            benefit="I understand what went wrong and how to fix it",
            acceptance_criteria=[
                "GIVEN invalid input WHEN submitted THEN the system SHALL display field-specific error messages",
                "GIVEN a system error occurs WHEN processing THEN the user SHALL see a friendly error message",
                "GIVEN the user fixes errors WHEN resubmitted THEN the system SHALL process successfully",
            ],
            story_points=2,
            priority="High",
            technical_notes=["Implement comprehensive validation", "Design user-friendly error messages"]
        ))
        
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
    
    response = agent.transform_to_user_stories(test_query)
    
    print("\n" + "="*60)
    print("RESULT:")
    print("="*60 + "\n")
    print(agent.format_all_stories_markdown(response))
