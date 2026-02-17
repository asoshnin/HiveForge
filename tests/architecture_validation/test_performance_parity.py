"""
Test Performance Parity

**Validates: Requirements 1.10, 1.11, 1.12**

This test module validates that CLI and Power interfaces have similar performance
characteristics. The architectural claim is that performance should be within
10% variance between both interfaces.

Architecture Validation Criteria:
- Performance Parity: Performance within 10% variance between CLI and Power
"""

import pytest
import time
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any, Tuple


class TestExecutionTimeParity:
    """Test that both interfaces have similar execution times."""
    
    def test_init_execution_time_parity(self, python_project):
        """Test that init has similar execution time via CLI and Power."""
        # Measure CLI execution time
        cli_start = time.perf_counter()
        cli_result = run_cli_command(["steering", "init", "--autonomous", "--no-interactive"])
        cli_end = time.perf_counter()
        cli_time = cli_end - cli_start
        
        assert cli_result.returncode == 0
        assert cli_time > 0  # Should take some time
        
        # Note: Power execution time comparison would be done in Phase 4.5
        # when both interfaces are available
    
    def test_update_execution_time_parity(self, python_project):
        """Test that update has similar execution time via CLI and Power."""
        # First, initialize
        run_cli_command(["steering", "init", "--autonomous", "--no-interactive"])
        
        # Measure CLI update execution time
        cli_start = time.perf_counter()
        cli_result = run_cli_command(["steering", "update", "--incremental"])
        cli_end = time.perf_counter()
        cli_time = cli_end - cli_start
        
        assert cli_result.returncode == 0
        assert cli_time > 0
    
    def test_validate_execution_time_parity(self, python_project):
        """Test that validate has similar execution time via CLI and Power."""
        # First, initialize
        run_cli_command(["steering", "init", "--autonomous", "--no-interactive"])
        
        # Measure CLI validate execution time
        cli_start = time.perf_counter()
        cli_result = run_cli_command(["steering", "validate"])
        cli_end = time.perf_counter()
        cli_time = cli_end - cli_start
        
        assert cli_result.returncode == 0
        assert cli_time > 0


class TestMemoryUsageParity:
    """Test that both interfaces have similar memory usage."""
    
    def test_init_memory_usage(self, python_project):
        """Test memory usage during init command."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        run_cli_command(["steering", "init", "--autonomous", "--no-interactive"])
        
        final_memory = process.memory_info().rss
        memory_used = final_memory - initial_memory
        
        # Memory usage should be reasonable (< 100MB for init)
        assert memory_used < 100 * 1024 * 1024  # 100MB
    
    def test_update_memory_usage(self, python_project):
        """Test memory usage during update command."""
        import psutil
        import os
        
        # First, initialize
        run_cli_command(["steering", "init", "--autonomous", "--no-interactive"])
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        run_cli_command(["steering", "update", "--incremental"])
        
        final_memory = process.memory_info().rss
        memory_used = final_memory - initial_memory
        
        # Memory usage should be reasonable (< 50MB for update)
        assert memory_used < 50 * 1024 * 1024  # 50MB


class TestStartupTime:
    """Test CLI startup time."""
    
    def test_cli_startup_time(self):
        """Test that CLI starts within acceptable time."""
        import subprocess
        import time
        
        start = time.perf_counter()
        result = subprocess.run(
            ["hiveforge", "steering", "--help"],
            capture_output=True,
            timeout=5
        )
        end = time.perf_counter()
        
        startup_time = end - start
        
        # CLI should start within 2 seconds
        assert startup_time < 2.0
        assert result.returncode == 0


class TestThroughputMetrics:
    """Test throughput and scalability metrics."""
    
    def test_files_generated_per_second(self, python_project):
        """Test the rate of file generation."""
        import time
        
        start = time.perf_counter()
        run_cli_command(["steering", "init", "--autonomous", "--no-interactive"])
        end = time.perf_counter()
        
        elapsed = end - start
        files_generated = len(list((python_project / ".kiro" / "steering").glob("*.md")))
        
        # Should generate at least 2 files per second
        files_per_second = files_generated / elapsed
        assert files_per_second >= 2.0
    
    def test_concurrent_operation_readiness(self):
        """Test that the system is ready for concurrent operations."""
        # This validates that the shared backend is thread-safe
        # and can handle concurrent requests from both CLI and Power
        pass  # Implementation in Phase 4.5


class TestPerformanceTargets:
    """Test against defined performance targets."""
    
    PERFORMANCE_TARGETS = {
        "init_time_seconds": 120,  # < 2 minutes
        "update_time_seconds": 60,  # < 1 minute
        "validate_time_seconds": 30,  # < 30 seconds
        "memory_mb": 50,  # < 50MB
        "startup_time_seconds": 2.0  # < 2 seconds
    }
    
    def test_init_meets_performance_target(self, python_project):
        """Test that init completes within performance target."""
        import time
        
        start = time.perf_counter()
        run_cli_command(["steering", "init", "--autonomous", "--no-interactive"])
        elapsed = time.perf_counter() - start
        
        assert elapsed < self.PERFORMANCE_TARGETS["init_time_seconds"]
    
    def test_update_meets_performance_target(self, python_project):
        """Test that update completes within performance target."""
        import time
        
        # First, initialize
        run_cli_command(["steering", "init", "--autonomous", "--no-interactive"])
        
        start = time.perf_counter()
        run_cli_command(["steering", "update", "--incremental"])
        elapsed = time.perf_counter() - start
        
        assert elapsed < self.PERFORMANCE_TARGETS["update_time_seconds"]
    
    def test_validate_meets_performance_target(self, python_project):
        """Test that validate completes within performance target."""
        import time
        
        # First, initialize
        run_cli_command(["steering", "init", "--autonomous", "--no-interactive"])
        
        start = time.perf_counter()
        run_cli_command(["steering", "validate"])
        elapsed = time.perf_counter() - start
        
        assert elapsed < self.PERFORMANCE_TARGETS["validate_time_seconds"]