"""
Property-based tests for PerformanceMonitor.

Validates: Requirements 10.1-10.7
"""

import time
from hypothesis import given, strategies as st
from src.hiveforge.steering.performance_monitor import PerformanceMonitor


def test_start_timer_resets_state():
    """Property: Timer starts fresh after start_timer()"""
    monitor = PerformanceMonitor()
    
    # Start first operation
    monitor.start_timer()
    time.sleep(0.01)
    duration1 = monitor.get_duration_ms()
    
    # Start second operation
    monitor.start_timer()
    duration2 = monitor.get_duration_ms()
    
    # Second duration should be much smaller (fresh start)
    assert duration2 < duration1 * 0.5


def test_display_working_message_delay():
    """Property: Working message appears after delay"""
    monitor = PerformanceMonitor(working_delay_s=1)
    monitor.start_timer()
    
    # Before delay - should not show
    time.sleep(0.5)
    assert not monitor.display_working_message()
    
    # After delay - should show
    time.sleep(0.6)
    assert monitor.display_working_message()


def test_timeout_detection():
    """Property: Timeout correctly detected after limit"""
    monitor = PerformanceMonitor(timeout_ms=100)  # 100ms timeout
    
    monitor.start_timer()
    time.sleep(0.15)  # Sleep 150ms
    
    assert monitor.check_timeout()


def test_retry_on_timeout():
    """Property: Retry allowed up to MAX_RETRIES"""
    monitor = PerformanceMonitor()
    
    # MAX_RETRIES=1 means we can retry once
    # Before any retry: allowed
    assert monitor.retry_on_timeout()
    
    # After one retry: not allowed (MAX_RETRIES reached)
    monitor.record_retry()
    assert not monitor.retry_on_timeout()


def test_progress_indicators_format():
    """Property: Progress indicators have correct format"""
    monitor = PerformanceMonitor()
    
    result = monitor.display_progress_indicators(3, 10, "test.md")
    
    # Should contain all expected elements
    assert "[3/10]" in result
    assert "test.md" in result
    assert "%" in result


def test_duration_summary_statistics():
    """Property: Duration summary has correct statistics"""
    monitor = PerformanceMonitor()
    
    # Record some durations
    durations = [100.0, 200.0, 150.0]
    for d in durations:
        monitor.record_duration(d)
    
    summary = monitor.get_duration_summary()
    
    assert summary["count"] == 3
    assert summary["total_ms"] == 450.0
    assert summary["avg_ms"] == 150.0
    assert summary["min_ms"] == 100.0
    assert summary["max_ms"] == 200.0


@given(st.integers(min_value=0, max_value=100))
def test_progress_bar_percentage(percentage):
    """Property: Progress bar correctly represents percentage"""
    monitor = PerformanceMonitor()
    
    # Test various percentages
    bar = monitor._create_progress_bar(float(percentage))
    
    # Bar should contain percentage (rounded down)
    assert f"{percentage}%" in bar


def test_streaming_response_supported():
    """Property: Streaming response is always supported"""
    monitor = PerformanceMonitor()
    
    assert monitor.get_streaming_response_support()


def test_reset_clears_state():
    """Property: Reset clears all state"""
    monitor = PerformanceMonitor()
    
    # Set some state
    monitor.start_timer()
    time.sleep(0.01)
    monitor.record_duration(100.0)
    monitor.display_progress_indicators(5, 10)
    
    # Reset
    monitor.reset()
    
    # State should be cleared
    assert monitor.get_duration_ms() == 0.0
    assert monitor.get_duration_summary()["count"] == 0
    assert monitor._file_count == 0
    assert monitor._total_files == 0


def test_multiple_operations_independent():
    """Property: Multiple operations have independent timing"""
    monitor = PerformanceMonitor()
    
    # First operation
    monitor.start_timer()
    time.sleep(0.02)
    duration1 = monitor.get_duration_ms()
    
    # Second operation (separate timing)
    monitor.start_timer()
    time.sleep(0.03)
    duration2 = monitor.get_duration_ms()
    
    # Durations should be approximately correct
    assert duration1 >= 15  # ~20ms with some tolerance
    assert duration2 >= 25  # ~30ms with some tolerance
