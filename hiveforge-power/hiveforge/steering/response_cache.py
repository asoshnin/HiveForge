"""
Response Cache for LLM Response Caching

This module implements a file-based cache for storing and retrieving LLM responses
to avoid redundant API calls for identical questions.

Key Features:
- File-based persistent storage
- Question hashing for cache key generation
- Thread-safe operations
- Automatic cache directory creation

Requirements: 7.8
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Optional

from .models import CachedResponse

logger = logging.getLogger(__name__)

# Default cache directory
DEFAULT_CACHE_DIR = Path(".kiro/.cache/llm_responses")


class ResponseCache:
    """
    Cache for storing LLM responses to avoid redundant API calls.
    
    Uses file-based storage with question hashing to identify identical questions.
    Each cached response is stored as a separate JSON file named by the question hash.
    
    Attributes:
        cache_dir: Directory where cache files are stored
    
    Requirements: 7.8
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the response cache.
        
        Args:
            cache_dir: Directory for cache storage. Defaults to .kiro/.cache/llm_responses
        """
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Cache directory ensured: {self.cache_dir}")
        except Exception as e:
            logger.warning(f"Failed to create cache directory: {e}")
    
    def _hash_question(self, question: str) -> str:
        """
        Generate a hash for a question to use as cache key.
        
        Uses SHA-256 to create a unique identifier for each question.
        
        Args:
            question: The question text to hash
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(question.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, question_hash: str) -> Path:
        """
        Get the file path for a cached response.
        
        Args:
            question_hash: Hash of the question
            
        Returns:
            Path to the cache file
        """
        return self.cache_dir / f"{question_hash}.json"
    
    def get(self, question: str) -> Optional[str]:
        """
        Retrieve a cached response for a question.
        
        Args:
            question: The question to look up
            
        Returns:
            Cached response string if found, None otherwise
            
        Requirements: 7.8
        """
        question_hash = self._hash_question(question)
        cache_path = self._get_cache_path(question_hash)
        
        if not cache_path.exists():
            logger.debug(f"Cache miss for question hash: {question_hash[:8]}...")
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cached = CachedResponse(
                question_hash=data['question_hash'],
                response=data['response'],
                timestamp=data['timestamp'],
                metadata=data.get('metadata', {})
            )
            
            logger.info(f"Cache hit for question hash: {question_hash[:8]}...")
            return cached.response
            
        except Exception as e:
            logger.warning(f"Failed to read cache file {cache_path}: {e}")
            return None
    
    def set(self, question: str, response: str, metadata: Optional[dict] = None) -> None:
        """
        Store a response in the cache.
        
        Args:
            question: The question that was asked
            response: The LLM response to cache
            metadata: Optional metadata to store with the response
            
        Requirements: 7.8
        """
        question_hash = self._hash_question(question)
        cache_path = self._get_cache_path(question_hash)
        
        cached = CachedResponse(
            question_hash=question_hash,
            response=response,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'question_hash': cached.question_hash,
                    'response': cached.response,
                    'timestamp': cached.timestamp,
                    'metadata': cached.metadata
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cached response for question hash: {question_hash[:8]}...")
            
        except Exception as e:
            logger.warning(f"Failed to write cache file {cache_path}: {e}")
    
    def clear(self) -> int:
        """
        Clear all cached responses.
        
        Returns:
            Number of cache files deleted
        """
        count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                count += 1
            logger.info(f"Cleared {count} cached responses")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
        
        return count
    
    def size(self) -> int:
        """
        Get the number of cached responses.
        
        Returns:
            Number of cache files
        """
        try:
            return len(list(self.cache_dir.glob("*.json")))
        except Exception as e:
            logger.warning(f"Failed to count cache files: {e}")
            return 0
