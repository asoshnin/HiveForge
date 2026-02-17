"""
Performance monitoring for the Steering Assistant v02.

This module provides the PerformanceMonitor class for tracking operation
duration, detecting timeouts, and displaying progress indicators.
"""

import time
from datetime import datetime
from typing import Optional


class PerformanceMonitor:
    """Monitors performance and timing for steering operations."""
    
    # Timeout constants
    DEFAULT_TIMEOUT_MS = 60000  # 60 seconds per LLM call
    WORKING_DELAY_S = 5  # Show working message after 5 seconds
    MAX_RETRIES = 1  # Retry once on timeout
    
    def __init__(
        self,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        working_delay_s: int = WORKING_DELAY_S,
    ):
        """
        Initialize the PerformanceMonitor.
        
        Args:
            timeout_ms: Timeout in milliseconds (default: 60000)
            working_delay_s: Delay before showing working message (default: 5)
        """
        self.timeout_ms = timeout_ms
        self.working_delay_s = working_delay_s
        self._start_time: Optional[float] = None
        self._last_working_message: Optional[float] = None
        self._retry_count = 0
        self._file_count = 0
        self._total_files = 0
        self._operation_durations: list[float] = []
    
    def start_timer(self) -> None:
        """Start timing an operation."""
        self._start_time = time.time()
        self._last_working_message = None
        self._retry_count = 0
    
    def display_working_message(self) -> bool:
        """
        Check if working message should be displayed.
        
        Returns:
            True if working message should be shown, False otherwise
        """
        if self._start_time is None:
            return False
        
        elapsed = time.time() - self._start_time
        
        # Show working message after working_delay_s
        if elapsed >= self.working_delay_s and self._last_working_message is None:
            self._last_working_message = time.time()
            return True
        
        return False
    
    def display_progress_indicators(
        self,
        current: int,
        total: int,
        file_name: Optional[str] = None,
    ) -> str:
        """
        Display progress indicators for file generation.
        
        Args:
            current: Current file number
            total: Total number of files
            file_name: Optional name of current file
            
        Returns:
            Progress string for display
        """
        self._file_count = current
        self._total_files = total
        
        percentage = (current / total) * 100 if total > 0 else 0
        progress_bar = self._create_progress_bar(percentage)
        
        if file_name:
            return f"[{current}/{total}] {progress_bar} {file_name}"
        else:
            return f"[{current}/{total}] {progress_bar} Generating..."
    
    def _create_progress_bar(self, percentage: float) -> str:
        """Create a visual progress bar."""
        bar_length = 20
        filled = int(bar_length * percentage / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        return f"[{bar}] {percentage:3.0f}%"
    
    def check_timeout(self) -> bool:
        """
        Check if operation has exceeded timeout.
        
        Returns:
            True if timeout exceeded, False otherwise
        """
        if self._start_time is None:
            return False
        
        elapsed_ms = (time.time() - self._start_time) * 1000
        return elapsed_ms > self.timeout_ms
    
    def retry_on_timeout(self) -> bool:
        """
        Check if operation should be retried on timeout.
        
        Returns:
            True if retry is allowed, False otherwise
        """
        return self._retry_count < self.MAX_RETRIES
    
    def record_retry(self) -> None:
        """Record a retry attempt."""
        self._retry_count += 1
    
    def get_duration_ms(self) -> float:
        """
        Get the duration of the current operation in milliseconds.
        
        Returns:
            Duration in milliseconds, or 0 if not started
        """
        if self._start_time is None:
            return 0.0
        
        return (time.time() - self._start_time) * 1000
    
    def record_duration(self, duration_ms: float) -> None:
        """Record a completed operation duration."""
        self._operation_durations.append(duration_ms)
    
    def get_duration_summary(self) -> dict:
        """
        Get duration statistics for completed operations.
        
        Returns:
            Dictionary with duration statistics
        """
        if not self._operation_durations:
            return {
                "count": 0,
                "total_ms": 0.0,
                "avg_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
            }
        
        durations = self._operation_durations
        return {
            "count": len(durations),
            "total_ms": sum(durations),
            "avg_ms": sum(durations) / len(durations),
            "min_ms": min(durations),
            "max_ms": max(durations),
        }
    
    def get_streaming_response_support(self) -> bool:
        """
        Check if streaming response is supported.
        
        Returns:
            True if streaming is supported (always true for v02)
        """
        return True
    
    def reset(self) -> None:
        """Reset the monitor for a new operation."""
        self._start_time = None
        self._last_working_message = None
        self._retry_count = 0
        self._file_count = 0
        self._total_files = 0
        self._operation_durations = []
