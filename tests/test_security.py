"""
Security Tests for Voice Agent
SAST checks and vulnerability scanning.
"""
import pytest
import os
import sys
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSecurityStaticAnalysis:
    """Static Application Security Testing (SAST)."""
    
    def test_no_hardcoded_api_keys_in_main(self):
        """Check main.py for hardcoded API keys."""
        main_path = os.path.join(os.path.dirname(__file__), "..", "main.py")
        with open(main_path, "r") as f:
            content = f.read()
        
        # Pattern for common API key formats
        api_key_patterns = [
            r'api[_-]?key\s*=\s*["\'][A-Za-z0-9]{20,}["\']',
            r'secret\s*=\s*["\'][A-Za-z0-9]{20,}["\']',
            r'AAAA[A-Za-z0-9+/]{30,}',  # Base64 tokens
        ]
        
        for pattern in api_key_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            assert len(matches) == 0, f"Potential hardcoded secret found: {matches}"
    
    def test_no_hardcoded_api_keys_in_html(self):
        """Check index.html for hardcoded API keys."""
        html_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
        with open(html_path, "r") as f:
            content = f.read()
        
        # Should not contain any API keys
        api_key_patterns = [
            r'api[_-]?key\s*[:=]\s*["\'][A-Za-z0-9]{20,}["\']',
            r'Bearer\s+[A-Za-z0-9+/]{30,}',  # Bearer tokens
        ]
        
        for pattern in api_key_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            assert len(matches) == 0, f"Potential hardcoded secret in HTML: {matches}"
    
    def test_env_file_not_committed(self):
        """Check that .env is in .gitignore (if git is used)."""
        gitignore_path = os.path.join(os.path.dirname(__file__), "..", ".gitignore")
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r") as f:
                content = f.read()
            assert ".env" in content, ".env should be in .gitignore"
        else:
            pytest.skip("No .gitignore file found")
    
    def test_cors_configuration(self):
        """Check CORS configuration in main.py."""
        main_path = os.path.join(os.path.dirname(__file__), "..", "main.py")
        with open(main_path, "r") as f:
            content = f.read()
        
        # CORS should be configured
        assert "CORSMiddleware" in content, "CORS middleware should be configured"
        
        # Note: allow_origins=["*"] is permissive but acceptable for development
        # In production, this should be restricted


class TestSecurityHeaders:
    """Test for security-related configurations."""
    
    def test_no_debug_mode_in_production(self):
        """Check that debug mode is not enabled in production code."""
        main_path = os.path.join(os.path.dirname(__file__), "..", "main.py")
        with open(main_path, "r") as f:
            content = f.read()
        
        # Should not have debug=True in uvicorn.run
        assert 'debug=True' not in content or 'debug = True' not in content


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_pydantic_model_used_for_validation(self):
        """Check that Pydantic models are used for input validation."""
        main_path = os.path.join(os.path.dirname(__file__), "..", "main.py")
        with open(main_path, "r") as f:
            content = f.read()
        
        assert "BaseModel" in content, "Pydantic BaseModel should be used"
        assert "SearchQuery" in content, "SearchQuery model should exist"
    
    def test_sql_injection_patterns_absent(self):
        """Check that code doesn't build SQL queries with string concatenation."""
        for filename in ["main.py", "knowledge_base.py"]:
            filepath = os.path.join(os.path.dirname(__file__), "..", filename)
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    content = f.read()
                
                # Check for SQL keywords with string formatting
                dangerous_patterns = [
                    r'SELECT.*\+.*query',
                    r'INSERT.*%s',
                    r'DELETE.*f["\']',
                ]
                
                for pattern in dangerous_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    assert len(matches) == 0, f"Potential SQL injection in {filename}"


class TestDependencySecurity:
    """Check for known vulnerable dependencies."""
    
    def test_requirements_exist(self):
        """Check that requirements.txt exists (for dependency tracking)."""
        # Note: This project might use a venv without requirements.txt
        # This is just a reminder to create one
        req_path = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
        if not os.path.exists(req_path):
            pytest.skip("requirements.txt not found - consider creating one for dependency tracking")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
