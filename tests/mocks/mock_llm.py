"""
Mock LLM for deterministic testing.

This module provides a MockLLM class that simulates LLM behavior
for unit tests without making actual API calls.
"""

from typing import Any, Dict, List, Optional


class MockLLM:
    """Mock LLM for testing with deterministic responses."""
    
    def __init__(self):
        """Initialize the mock LLM."""
        self._responses: Dict[str, str] = {}
        self._call_count = 0
        self._call_history: List[Dict[str, Any]] = []
        self._default_response = "# Generated Content\n\nThis is a mock response."
    
    def set_response(
        self,
        prompt_key: str,
        response: str,
    ) -> None:
        """
        Set a response for a specific prompt.
        
        Args:
            prompt_key: Key to identify the prompt
            response: Response to return for this prompt
        """
        self._responses[prompt_key] = response
    
    def set_default_response(self, response: str) -> None:
        """
        Set the default response when no specific match is found.
        
        Args:
            response: Default response string
        """
        self._default_response = response
    
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """
        Generate content based on the prompt.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional arguments
            
        Returns:
            Generated content
        """
        self._call_count += 1
        
        # Store call history
        self._call_history.append({
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "kwargs": kwargs,
        })
        
        # Look for specific response
        prompt_key = self._get_prompt_key(prompt)
        if prompt_key in self._responses:
            return self._responses[prompt_key]
        
        return self._default_response
    
    def _get_prompt_key(self, prompt: str) -> str:
        """Generate a key for prompt lookup."""
        # Use first line or first 50 chars as key
        first_line = prompt.split("\n")[0].strip()
        return first_line[:50] if first_line else "default"
    
    def get_call_count(self) -> int:
        """
        Get the number of LLM calls made.
        
        Returns:
            Number of calls
        """
        return self._call_count
    
    def get_call_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of all LLM calls.
        
        Returns:
            List of call records
        """
        return self._call_history.copy()
    
    def clear_history(self) -> None:
        """Clear the call history."""
        self._call_count = 0
        self._call_history = []
    
    def get_last_call(self) -> Optional[Dict[str, Any]]:
        """
        Get the last LLM call.
        
        Returns:
            Last call record or None
        """
        if not self._call_history:
            return None
        return self._call_history[-1]
    
    def set_streaming_response(
        self,
        prompt_key: str,
        chunks: List[str],
    ) -> None:
        """
        Set a streaming response for a prompt.
        
        Args:
            prompt_key: Key to identify the prompt
            chunks: List of chunks to stream
        """
        self._responses[f"{prompt_key}_stream"] = chunks
    
    def generate_streaming(
        self,
        prompt: str,
        **kwargs,
    ) -> List[str]:
        """
        Generate content as a stream of chunks.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional arguments
            
        Returns:
            List of content chunks
        """
        prompt_key = self._get_prompt_key(prompt)
        stream_key = f"{prompt_key}_stream"
        
        if stream_key in self._responses:
            return self._responses[stream_key]
        
        return [self._default_response]
