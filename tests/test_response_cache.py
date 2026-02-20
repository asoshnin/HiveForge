"""
Unit tests for ResponseCache.

Tests the file-based LLM response caching functionality.
"""

import json
import tempfile
import time
from pathlib import Path

import pytest

from hiveforge.steering.response_cache import ResponseCache


class TestResponseCache:
    """Test suite for ResponseCache class."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create a ResponseCache instance with temporary directory."""
        return ResponseCache(cache_dir=temp_cache_dir / "cache")
    
    def test_cache_initialization(self, temp_cache_dir):
        """Test that cache directory is created on initialization."""
        cache_dir = temp_cache_dir / "test_cache"
        assert not cache_dir.exists()
        
        cache = ResponseCache(cache_dir=cache_dir)
        
        assert cache_dir.exists()
        assert cache_dir.is_dir()
    
    def test_cache_miss(self, cache):
        """Test that get() returns None for non-existent questions."""
        result = cache.get("What is the meaning of life?")
        assert result is None
    
    def test_cache_hit(self, cache):
        """Test that set() and get() work correctly."""
        question = "What is the capital of France?"
        response = "The capital of France is Paris."
        
        cache.set(question, response)
        cached_response = cache.get(question)
        
        assert cached_response == response
    
    def test_cache_with_metadata(self, cache):
        """Test that metadata is stored and retrieved correctly."""
        question = "What is 2 + 2?"
        response = "4"
        metadata = {"model": "gpt-4", "tokens": 10}
        
        cache.set(question, response, metadata=metadata)
        cached_response = cache.get(question)
        
        assert cached_response == response
    
    def test_question_hashing(self, cache):
        """Test that identical questions produce the same hash."""
        question = "What is Python?"
        response1 = "Python is a programming language."
        response2 = "Python is a snake."
        
        # Set first response
        cache.set(question, response1)
        
        # Set second response (should overwrite)
        cache.set(question, response2)
        
        # Should get the second response
        cached_response = cache.get(question)
        assert cached_response == response2
    
    def test_different_questions_different_cache(self, cache):
        """Test that different questions are cached separately."""
        question1 = "What is Python?"
        response1 = "Python is a programming language."
        
        question2 = "What is Java?"
        response2 = "Java is a programming language."
        
        cache.set(question1, response1)
        cache.set(question2, response2)
        
        assert cache.get(question1) == response1
        assert cache.get(question2) == response2
    
    def test_cache_persistence(self, temp_cache_dir):
        """Test that cache persists across ResponseCache instances."""
        cache_dir = temp_cache_dir / "persistent_cache"
        
        # Create first cache instance and store data
        cache1 = ResponseCache(cache_dir=cache_dir)
        question = "What is the speed of light?"
        response = "299,792,458 meters per second"
        cache1.set(question, response)
        
        # Create second cache instance and retrieve data
        cache2 = ResponseCache(cache_dir=cache_dir)
        cached_response = cache2.get(question)
        
        assert cached_response == response
    
    def test_cache_clear(self, cache):
        """Test that clear() removes all cached responses."""
        # Add multiple responses
        cache.set("Question 1", "Answer 1")
        cache.set("Question 2", "Answer 2")
        cache.set("Question 3", "Answer 3")
        
        assert cache.size() == 3
        
        # Clear cache
        count = cache.clear()
        
        assert count == 3
        assert cache.size() == 0
        assert cache.get("Question 1") is None
    
    def test_cache_size(self, cache):
        """Test that size() returns correct count."""
        assert cache.size() == 0
        
        cache.set("Q1", "A1")
        assert cache.size() == 1
        
        cache.set("Q2", "A2")
        assert cache.size() == 2
        
        cache.set("Q3", "A3")
        assert cache.size() == 3
    
    def test_unicode_questions_and_responses(self, cache):
        """Test that cache handles Unicode correctly."""
        question = "¿Qué es Python? 你好"
        response = "Python es un lenguaje de programación. Python是一种编程语言。"
        
        cache.set(question, response)
        cached_response = cache.get(question)
        
        assert cached_response == response
    
    def test_large_response(self, cache):
        """Test that cache handles large responses."""
        question = "Generate a long text"
        response = "Lorem ipsum " * 10000  # Large response
        
        cache.set(question, response)
        cached_response = cache.get(question)
        
        assert cached_response == response
    
    def test_empty_response(self, cache):
        """Test that cache handles empty responses."""
        question = "Empty question"
        response = ""
        
        cache.set(question, response)
        cached_response = cache.get(question)
        
        assert cached_response == response
    
    def test_corrupted_cache_file(self, cache, temp_cache_dir):
        """Test that corrupted cache files are handled gracefully."""
        question = "Test question"
        
        # Create a corrupted cache file
        question_hash = cache._hash_question(question)
        cache_path = cache._get_cache_path(question_hash)
        cache_path.write_text("invalid json content")
        
        # Should return None instead of crashing
        result = cache.get(question)
        assert result is None
    
    def test_timestamp_stored(self, cache, temp_cache_dir):
        """Test that timestamp is stored with cached responses."""
        question = "Time test"
        response = "Response"
        
        before = time.time()
        cache.set(question, response)
        after = time.time()
        
        # Read the cache file directly to check timestamp
        question_hash = cache._hash_question(question)
        cache_path = cache._get_cache_path(question_hash)
        
        with open(cache_path, 'r') as f:
            data = json.load(f)
        
        assert 'timestamp' in data
        assert before <= data['timestamp'] <= after
    
    def test_special_characters_in_question(self, cache):
        """Test that questions with special characters are handled correctly."""
        question = "What is 'this' & \"that\"? <tag> {json: true}"
        response = "Special characters test"
        
        cache.set(question, response)
        cached_response = cache.get(question)
        
        assert cached_response == response
    
    def test_whitespace_sensitivity(self, cache):
        """Test that questions with different whitespace are treated as different."""
        question1 = "What is Python?"
        question2 = "What  is  Python?"  # Extra spaces
        response1 = "Response 1"
        response2 = "Response 2"
        
        cache.set(question1, response1)
        cache.set(question2, response2)
        
        # Different whitespace = different questions
        assert cache.get(question1) == response1
        assert cache.get(question2) == response2
    
    def test_case_sensitivity(self, cache):
        """Test that questions are case-sensitive."""
        question1 = "What is Python?"
        question2 = "what is python?"
        response1 = "Response 1"
        response2 = "Response 2"
        
        cache.set(question1, response1)
        cache.set(question2, response2)
        
        # Different case = different questions
        assert cache.get(question1) == response1
        assert cache.get(question2) == response2
