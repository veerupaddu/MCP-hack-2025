# User Story Agent - "Alex"

## Overview
**"Alex"** is a specialized AI agent with the role of **Senior Product Owner & Business Analyst**. The agent transforms user requirements into structured, INVEST-compliant user stories by querying the MCP server.

## Persona

**Name:** Alex  
**Role:** Senior Product Owner & Business Analyst  
**Expertise:**
- Converting technical requirements into user stories
- Applying INVEST principles (Independent, Negotiable, Valuable, Estimable, Small, Testable)
- Writing clear acceptance criteria in Given-When-Then format
- Story point estimation

## Features

### MCP Server Integration
- **RAG Query**: Retrieves product context from knowledge base
- **Fine-tuned Model**: Gets domain-specific insights
- **Fallback Logic**: Generates intelligent stories even without MCP data

### Output Format
Each user story includes:
- **Story ID** (e.g., US-001)
- **Title**: Clear, concise feature name
- **Actor**: User role (customer, admin, agent, etc.)
- **Action**: What they want to do
- **Benefit**: Why they need it (the value)
- **Acceptance Criteria**: 3-5 testable criteria in Given-When-Then format
- **Story Points**: Estimation (1, 2, 3, 5, 8, 13)
- **Priority**: High, Medium, or Low
- **Technical Notes**: Implementation considerations

## Usage

### Basic Usage

```python
from agent.user_story_agent import UserStoryAgent

# Create agent instance
agent = UserStoryAgent()

# Generate user stories
response = agent.transform_to_user_stories(
    "I need a feature for customers to file auto insurance claims online"
)

# Access stories
for story in response.stories:
    print(story.to_markdown())

# Get full markdown document
markdown = agent.format_all_stories_markdown(response)
print(markdown)
```

### Convenience Function

```python
from agent.user_story_agent import create_user_stories

response = create_user_stories("your requirement here")
```

### Configuration

MCP Server URL is configured via environment variable:
```bash
export MCP_SERVER_URL="https://veeru-c-sdlc-mcp.hf.space"
```

## Response Structure

```python
@dataclass
class UserStoryResponse:
    stories: List[UserStory]  # List of structured stories
    raw_query: str             # Original user query
    domain: str                # Detected domain
    mcp_source: str            # MCP sources used (e.g., "RAG + Fine-tuned")
    confidence: float          # Confidence score (0.0 to 1.0)
    warnings: List[str]        # Any warnings or limitations
```

## Example Output

**Input:**
```
I need a feature for customers to file auto insurance claims online
```

**Output:**
```markdown
### US-001: Online Claims Filing

**As a** customer,  
**I want** to file auto insurance claims online,  
**So that** I can report incidents quickly without visiting an office.

**Acceptance Criteria:**
1. GIVEN the customer is authenticated WHEN they access the feature THEN the system SHALL display the claims form
2. GIVEN valid claim details are provided WHEN submitted THEN the system SHALL create a claim record
3. GIVEN an error occurs WHEN processing THEN the system SHALL display a clear error message

**Story Points:** 5  
**Priority:** High

**Technical Notes:**
- Implement input validation for claim details
- Add file upload for supporting documents
- Ensure secure data transmission
```

## INVEST Principles

The agent ensures all stories follow INVEST principles:

- **Independent**: Each story can be developed separately
- **Negotiable**: Details can be discussed and refined
- **Valuable**: Provides clear user/business value
- **Estimable**: Can be sized and estimated
- **Small**: Completable within one sprint
- **Testable**: Has clear, testable acceptance criteria

## Integration with Dashboard

The agent can be integrated into the dashboard workflow to automatically generate user stories from requirements during Step 4 ("Craft User Stories").

## Testing

Run the test example:
```bash
cd /Users/veeru/agents/mcp-hack
python -m agent.user_story_agent
```

## Files

- **Main Agent**: `agent/user_story_agent.py`
- **Documentation**: `agent/user_story_agent.md` (this file)

## Future Enhancements

- LLM integration for more sophisticated story generation
- Support for epic-level story mapping
- Integration with JIRA for direct story creation
- Story splitting recommendations for large stories
- Historical data learning for better estimation
