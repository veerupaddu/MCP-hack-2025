"""
Client library for the RAG API
Use this to call the API from Python code
"""

import requests
from typing import Optional, Dict, List

class RAGAPIClient:
    """Client for the Product Design RAG API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL of the RAG API
        """
        self.base_url = base_url.rstrip('/')
    
    def health_check(self) -> Dict:
        """Check if the API is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def query(
        self, 
        question: str, 
        top_k: int = 5, 
        max_tokens: int = 1024,
        timeout: int = 5
    ) -> Dict:
        """
        Query the RAG system
        
        Args:
            question: The question to ask
            top_k: Number of documents to retrieve
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
        
        Returns:
            Dictionary with answer, timing, and sources
        """
        try:
            response = requests.post(
                f"{self.base_url}/query",
                json={
                    "question": question,
                    "top_k": top_k,
                    "max_tokens": max_tokens
                },
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": f"Request timed out after {timeout} seconds"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
    
    def query_fast(self, question: str) -> Dict:
        """
        Fast query with optimized settings for <3 second responses
        
        Args:
            question: The question to ask
        
        Returns:
            Dictionary with answer, timing, and sources
        """
        return self.query(
            question=question,
            top_k=3,  # Fewer docs for speed
            max_tokens=512,  # Shorter responses
            timeout=5
        )

# Example usage
if __name__ == "__main__":
    # Initialize client
    client = RAGAPIClient(base_url="http://localhost:8000")
    
    # Health check
    print("Health check:", client.health_check())
    
    # Query
    result = client.query("What are the three product tiers?")
    print("\nQuery result:")
    print(f"Answer: {result.get('answer', 'N/A')}")
    print(f"Total time: {result.get('total_time', 0):.2f}s")
    print(f"Success: {result.get('success', False)}")

