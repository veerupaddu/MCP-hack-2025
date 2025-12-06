"""
Test suite for User Story Agent

Tests the UserStoryAgent class functionality including:
- MCP server integration
- User story generation
- Story formatting
- INVEST principles validation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from agent.user_story_agent import (
    UserStory,
    UserStoryResponse,
    UserStoryAgent,
    create_user_stories
)


class TestUserStory(unittest.TestCase):
    """Test the UserStory dataclass"""
    
    def test_user_story_creation(self):
        """Test creating a user story"""
        story = UserStory(
            story_id="US-001",
            title="Test Feature",
            actor="customer",
            action="perform an action",
            benefit="achieve a goal"
        )
        
        self.assertEqual(story.story_id, "US-001")
        self.assertEqual(story.actor, "customer")
        self.assertEqual(story.story_points, 3)  # Default value
        self.assertEqual(story.priority, "Medium")  # Default value
    
    def test_user_story_to_markdown(self):
        """Test markdown formatting"""
        story = UserStory(
            story_id="US-001",
            title="Test Feature",
            actor="customer",
            action="perform an action",
            benefit="achieve a goal",
            acceptance_criteria=["Criteria 1", "Criteria 2"],
            story_points=5,
            priority="High"
        )
        
        markdown = story.to_markdown()
        
        self.assertIn("US-001", markdown)
        self.assertIn("**As a** customer", markdown)
        self.assertIn("**I want** perform an action", markdown)
        self.assertIn("**So that** achieve a goal", markdown)
        self.assertIn("Criteria 1", markdown)
        self.assertIn("Story Points:** 5", markdown)
        self.assertIn("Priority:** High", markdown)


class TestUserStoryAgent(unittest.TestCase):
    """Test the UserStoryAgent class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.agent = UserStoryAgent()
        self.test_query = "I need a feature for customers to file insurance claims online"
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        self.assertEqual(self.agent.PERSONA_NAME, "Alex")
        self.assertEqual(self.agent.PERSONA_ROLE, "Senior Product Owner & Business Analyst")
        self.assertIsNotNone(self.agent.mcp_server_url)
    
    def test_agent_without_mcp(self):
        """Test agent generates stories without MCP connection"""
        response = self.agent.transform_to_user_stories(
            self.test_query,
            use_rag=False,
            use_finetuned=False
        )
        
        self.assertIsInstance(response, UserStoryResponse)
        self.assertGreater(len(response.stories), 0)
        self.assertEqual(response.raw_query, self.test_query)
        self.assertIsInstance(response.confidence, float)
        self.assertGreaterEqual(response.confidence, 0.0)
        self.assertLessEqual(response.confidence, 1.0)
    
    def test_story_generation_quality(self):
        """Test that generated stories follow basic structure"""
        response = self.agent.transform_to_user_stories(
            self.test_query,
            use_rag=False,
            use_finetuned=False
        )
        
        for story in response.stories:
            self.assertIsNotNone(story.story_id)
            self.assertIsNotNone(story.title)
            self.assertIsNotNone(story.actor)
            self.assertIsNotNone(story.action)
            self.assertIsNotNone(story.benefit)
            self.assertGreater(len(story.acceptance_criteria), 0)
            self.assertIn(story.story_points, [1, 2, 3, 5, 8, 13])
            self.assertIn(story.priority, ["High", "Medium", "Low"])
    
    def test_acceptance_criteria_format(self):
        """Test that acceptance criteria follow Given-When-Then pattern"""
        response = self.agent.transform_to_user_stories(
            self.test_query,
            use_rag=False,
            use_finetuned=False
        )
        
        for story in response.stories:
            for criteria in story.acceptance_criteria:
                # Check for Given-When-Then keywords
                criteria_upper = criteria.upper()
                has_valid_format = (
                    "GIVEN" in criteria_upper or
                    "WHEN" in criteria_upper or
                    "THEN" in criteria_upper or
                    "SHALL" in criteria_upper
                )
                self.assertTrue(
                    has_valid_format,
                    f"Criteria doesn't follow Given-When-Then: {criteria}"
                )
    
    def test_actor_detection(self):
        """Test that agent correctly identifies actors"""
        test_cases = [
            ("Admin needs to manage users", "administrator"),
            ("Customer wants to buy insurance", "customer"),
            ("Agent needs to process claims", "agent"),
            ("User wants to login", "user"),
        ]
        
        for query, expected_actor in test_cases:
            response = self.agent.transform_to_user_stories(
                query,
                use_rag=False,
                use_finetuned=False
            )
            
            # Check if any story has the expected actor
            actors = [story.actor for story in response.stories]
            self.assertIn(
                expected_actor,
                actors,
                f"Expected actor '{expected_actor}' not found for query: {query}"
            )
    
    def test_confidence_calculation(self):
        """Test confidence score calculation"""
        # Without any MCP data
        response_no_mcp = self.agent.transform_to_user_stories(
            self.test_query,
            use_rag=False,
            use_finetuned=False
        )
        
        # With MCP data (mocked)
        with patch.object(self.agent, '_query_mcp_rag') as mock_rag:
            mock_rag.return_value = {"context": "Some context"}
            
            response_with_mcp = self.agent.transform_to_user_stories(
                self.test_query,
                use_rag=True,
                use_finetuned=False
            )
            
            # Confidence should be higher with MCP data
            self.assertGreater(
                response_with_mcp.confidence,
                response_no_mcp.confidence
            )
    
    def test_warnings_generation(self):
        """Test that warnings are generated appropriately"""
        response = self.agent.transform_to_user_stories(
            self.test_query,
            use_rag=False,
            use_finetuned=False
        )
        
        self.assertGreater(len(response.warnings), 0)
        self.assertTrue(
            any("RAG" in warning for warning in response.warnings)
        )
    
    def test_format_all_stories_markdown(self):
        """Test markdown formatting for all stories"""
        response = self.agent.transform_to_user_stories(
            self.test_query,
            use_rag=False,
            use_finetuned=False
        )
        
        markdown = self.agent.format_all_stories_markdown(response)
        
        self.assertIn("# User Stories:", markdown)
        self.assertIn("**Domain:**", markdown)
        self.assertIn("**Source:**", markdown)
        self.assertIn("**Confidence:**", markdown)
        self.assertIn(self.agent.PERSONA_NAME, markdown)
        
        # Check that all stories are included
        for story in response.stories:
            self.assertIn(story.story_id, markdown)
    
    @patch('requests.post')
    @patch('requests.get')
    def test_mcp_rag_integration(self, mock_get, mock_post):
        """Test MCP RAG query integration"""
        # Mock the event submission
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {"event_id": "test-123"}
        
        # Mock the result stream
        mock_response = Mock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = [
            b'data: [{"status": "success", "specification": {"full_answer": "Test context"}}]'
        ]
        mock_get.return_value = mock_response
        
        result = self.agent._query_mcp_rag("test query")
        
        self.assertIsNotNone(result)
        self.assertIn("context", result)
        self.assertEqual(result["context"], "Test context")
        
        # Verify the correct endpoint was called
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn("/call/query_rag", call_args[0][0])
    
    @patch('requests.post')
    @patch('requests.get')
    def test_mcp_finetuned_integration(self, mock_get, mock_post):
        """Test MCP fine-tuned model query integration"""
        # Mock the event submission
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {"event_id": "test-456"}
        
        # Mock the result stream
        mock_response = Mock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = [
            b'data: [{"status": "success", "insights": {"full_response": "Domain insights", "domain": "insurance"}}]'
        ]
        mock_get.return_value = mock_response
        
        result = self.agent._query_mcp_finetuned("test query")
        
        self.assertIsNotNone(result)
        self.assertIn("context", result)
        self.assertEqual(result["domain"], "insurance")
        
        # Verify the correct endpoint was called
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn("/call/query_finetuned", call_args[0][0])
    
    def test_enriched_prompt_building(self):
        """Test that enriched prompts include context"""
        rag_context = "RAG context here"
        ft_context = "Fine-tuned context here"
        
        prompt = self.agent._build_enriched_prompt(
            self.test_query,
            rag_context,
            ft_context
        )
        
        self.assertIn(self.test_query, prompt)
        self.assertIn(rag_context, prompt)
        self.assertIn(ft_context, prompt)
        self.assertIn(self.agent.PERSONA_NAME, prompt)


class TestConvenienceFunction(unittest.TestCase):
    """Test the convenience function"""
    
    def test_create_user_stories_function(self):
        """Test the create_user_stories convenience function"""
        response = create_user_stories("Test requirement")
        
        self.assertIsInstance(response, UserStoryResponse)
        self.assertGreater(len(response.stories), 0)


class TestINVESTPrinciples(unittest.TestCase):
    """Test that stories follow INVEST principles"""
    
    def setUp(self):
        self.agent = UserStoryAgent()
        self.response = self.agent.transform_to_user_stories(
            "I need a feature for customers to search policies",
            use_rag=False,
            use_finetuned=False
        )
    
    def test_independent(self):
        """Test that stories have unique IDs (independence)"""
        story_ids = [story.story_id for story in self.response.stories]
        self.assertEqual(len(story_ids), len(set(story_ids)), "Story IDs must be unique")
    
    def test_valuable(self):
        """Test that stories have clear benefits (value)"""
        for story in self.response.stories:
            self.assertIsNotNone(story.benefit)
            self.assertGreater(len(story.benefit), 0)
    
    def test_estimable(self):
        """Test that stories have story points (estimable)"""
        for story in self.response.stories:
            self.assertIsNotNone(story.story_points)
            self.assertGreater(story.story_points, 0)
    
    def test_small(self):
        """Test that story points are reasonable (small)"""
        for story in self.response.stories:
            # Stories should not be larger than 13 points
            self.assertLessEqual(story.story_points, 13)
    
    def test_testable(self):
        """Test that stories have acceptance criteria (testable)"""
        for story in self.response.stories:
            self.assertGreater(
                len(story.acceptance_criteria),
                0,
                f"Story {story.story_id} has no acceptance criteria"
            )


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
