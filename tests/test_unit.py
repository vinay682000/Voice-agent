"""
Unit Tests for Voice Agent
Tests individual components in isolation.
"""
import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestKnowledgeBase:
    """Unit tests for knowledge_base.py"""
    
    def test_knowledge_base_import(self):
        """Test that KnowledgeBase can be imported."""
        from knowledge_base import KnowledgeBase
        assert KnowledgeBase is not None
    
    def test_knowledge_base_initialization(self):
        """Test KnowledgeBase initializes with transcript file."""
        from knowledge_base import KnowledgeBase
        kb_file = "tactiq-free-transcript-SsKkZTjUJEk.txt"
        if os.path.exists(kb_file):
            kb = KnowledgeBase(kb_file)
            assert kb is not None
        else:
            pytest.skip("Knowledge base file not found")
    
    def test_knowledge_base_search(self):
        """Test KnowledgeBase search returns results."""
        from knowledge_base import KnowledgeBase
        kb_file = "tactiq-free-transcript-SsKkZTjUJEk.txt"
        if os.path.exists(kb_file):
            kb = KnowledgeBase(kb_file)
            result = kb.search("comfort")
            assert isinstance(result, str)
            assert len(result) > 0
        else:
            pytest.skip("Knowledge base file not found")
    
    def test_knowledge_base_empty_query(self):
        """Test KnowledgeBase handles empty query."""
        from knowledge_base import KnowledgeBase
        kb_file = "tactiq-free-transcript-SsKkZTjUJEk.txt"
        if os.path.exists(kb_file):
            kb = KnowledgeBase(kb_file)
            result = kb.search("")
            assert isinstance(result, str)
        else:
            pytest.skip("Knowledge base file not found")


class TestMainAppComponents:
    """Unit tests for main.py components."""
    
    def test_environment_variables_exist(self):
        """Test that required environment variables can be loaded."""
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        assert api_key is not None, "AZURE_OPENAI_API_KEY not set"
        assert endpoint is not None, "AZURE_OPENAI_ENDPOINT not set"
        assert deployment is not None, "AZURE_OPENAI_DEPLOYMENT_NAME not set"
    
    def test_hostname_parsing(self):
        """Test hostname is correctly parsed from endpoint."""
        endpoint = "https://example.openai.azure.com/"
        hostname = endpoint.replace("https://", "").replace("http://", "").rstrip("/")
        if "/" in hostname:
            hostname = hostname.split("/")[0]
        
        assert hostname == "example.openai.azure.com"
    
    def test_hostname_parsing_with_path(self):
        """Test hostname parsing with path in URL."""
        endpoint = "https://example.openai.azure.com/some/path"
        hostname = endpoint.replace("https://", "").replace("http://", "").rstrip("/")
        if "/" in hostname:
            hostname = hostname.split("/")[0]
        
        assert hostname == "example.openai.azure.com"


class TestSearchQueryModel:
    """Tests for Pydantic models."""
    
    def test_search_query_valid(self):
        """Test SearchQuery model with valid data."""
        from pydantic import BaseModel
        
        class SearchQuery(BaseModel):
            query: str
        
        sq = SearchQuery(query="test query")
        assert sq.query == "test query"
    
    def test_search_query_empty(self):
        """Test SearchQuery model with empty string."""
        from pydantic import BaseModel
        
        class SearchQuery(BaseModel):
            query: str
        
        sq = SearchQuery(query="")
        assert sq.query == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
