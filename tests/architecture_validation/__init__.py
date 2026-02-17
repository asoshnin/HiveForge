"""
Architecture Validation Test Suite

This package contains integration tests that validate the architectural claims
about CLI/Power equivalence in the steering-power-conversion spec.

Test Categories:
1. CLI/Power output equivalence tests
2. Shared backend utilization tests
3. Error handling parity tests
4. Performance parity tests
5. Security validation tests
6. Orchestrator integration tests
"""

__all__ = [
    "test_cli_power_output_equivalence",
    "test_shared_backend_utilization",
    "test_error_handling_parity",
    "test_performance_parity",
    "test_security_validation",
    "test_orchestrator_integration"
]