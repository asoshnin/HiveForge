# Phase 2 Quick Start Guide

**Purpose**: Get started with Phase 2 implementation quickly  
**Audience**: Developer implementing shared backend  
**Time to Read**: 5 minutes

---

## Before You Start

### 1. Verify Prerequisites
```bash
# Check v02 tests are passing
python -m pytest tests/test_steering_cli.py -v
# Should show: 40 passed

# Check Python version
python --version
# Should be: Python 3.11+

# Check dependencies
pip list | grep pytest
# Should include: pytest, pytest-cov
```

### 2. Install Missing Dependencies
```bash
# Add to requirements or install directly
pip install pytest-asyncio psutil
```

### 3. Review Key Documents
- [ ] Read `PHASE_2_IMPLEMENTATION_PLAN.md` (15 min)
- [ ] Review `SHARED_BACKEND_INTERFACE.md` (10 min)
- [ ] Review `SECURITY_WRAPPER_DESIGN.md` (10 min)
- [ ] Skim `ARCHITECTURE_VALIDATION_REPORT.md` (5 min)

---

## Implementation Order

### Step 1: Create Directory Structure (15 min)
```bash
# Create shared backend directory
mkdir -p src/hiveforge/steering/shared

# Create test directory
mkdir -p tests/shared

# Create __init__.py files
touch src/hiveforge/steering/shared/__init__.py
touch tests/shared/__init__.py
```

### Step 2: Create Base Module Files (15 min)
```bash
# Create core module files
touch src/hiveforge/steering/shared/base.py
touch src/hiveforge/steering/shared/adapters.py
touch src/hiveforge/steering/shared/security_wrappers.py
touch src/hiveforge/steering/shared/error_handling.py
touch src/hiveforge/steering/shared/telemetry.py

# Create test files
touch tests/shared/test_base.py
touch tests/shared/test_adapters.py
touch tests/shared/test_security_wrappers.py
touch tests/shared/test_error_handling.py
touch tests/shared/test_telemetry.py
```

### Step 3: Implement SharedWorkflowBase (3 hours)
**File**: `src/hiveforge/steering/shared/base.py`

**Key Methods to Implement**:
- `__init__(self, config: dict)`
- `validate_config(self) -> bool`
- `execute(self) -> WorkflowResult`
- `handle_error(self, error: Exception) -> None`

**Test File**: `tests/shared/test_base.py`

**Verify**:
```bash
python -m pytest tests/shared/test_base.py -v
```

### Step 4: Implement First Adapter (4 hours)
**File**: `src/hiveforge/steering/shared/adapters.py`

**Start with**: `SharedValidateWorkflow` (simplest)

**Key Methods**:
- `execute(self) -> WorkflowResult`
- Wrap existing `ValidateWorkflow` logic

**Test File**: `tests/shared/test_adapters.py`

**Verify**:
```bash
# Test new adapter
python -m pytest tests/shared/test_adapters.py::TestSharedValidateWorkflow -v

# Verify v02 still works
python -m pytest tests/test_steering_cli.py::TestSteeringValidateCommand -v
```

### Step 5: Implement Security Wrappers (4 hours)
**File**: `src/hiveforge/steering/shared/security_wrappers.py`

**Key Functions**:
- `validate_parameters(params: dict) -> bool`
- `sanitize_path(path: str) -> str`
- `secure_tool_execution(func) -> decorator`

**Test File**: `tests/shared/test_security_wrappers.py`

**Verify**:
```bash
python -m pytest tests/shared/test_security_wrappers.py -v
```

### Step 6: Continue with Remaining Tasks
Follow `PHASE_2_IMPLEMENTATION_PLAN.md` for detailed steps.

---

## Testing Strategy

### After Each Module
```bash
# Run unit tests for that module
python -m pytest tests/shared/test_<module>.py -v

# Run v02 regression tests
python -m pytest tests/test_steering_cli.py -v

# Check coverage
python -m pytest tests/shared/ --cov=src/hiveforge/steering/shared --cov-report=term-missing
```

### Before Committing
```bash
# Run all tests
python -m pytest tests/ -v

# Check code coverage
python -m pytest tests/ --cov=src/hiveforge/steering --cov-report=html

# Run linter
flake8 src/hiveforge/steering/shared/
```

---

## Common Issues & Solutions

### Issue 1: v02 Tests Failing
**Symptom**: v02 CLI tests fail after changes  
**Solution**: 
- Revert last change
- Review what broke
- Use feature flags to isolate new code
- Ensure backward compatibility

### Issue 2: Import Errors
**Symptom**: `ModuleNotFoundError` or circular imports  
**Solution**:
- Check `__init__.py` exports
- Review import order
- Use absolute imports
- Check for circular dependencies

### Issue 3: Test Failures
**Symptom**: New tests fail unexpectedly  
**Solution**:
- Check test fixtures
- Verify mock setup
- Review test data
- Check for side effects

---

## Code Style Guidelines

### Python Style
```python
# Use type hints
def validate_parameters(params: dict) -> bool:
    """Validate tool parameters."""
    pass

# Use docstrings
class SharedWorkflowBase:
    """Base class for shared workflows.
    
    Provides common functionality for all workflow adapters.
    """
    pass

# Use descriptive names
def sanitize_path(path: str) -> str:
    """Sanitize file path to prevent directory traversal."""
    pass
```

### Testing Style
```python
# Use descriptive test names
def test_validate_parameters_rejects_invalid_confidence():
    """Test that validate_parameters rejects confidence > 1.0."""
    pass

# Use arrange-act-assert pattern
def test_sanitize_path_removes_parent_references():
    # Arrange
    malicious_path = "../../../etc/passwd"
    
    # Act
    sanitized = sanitize_path(malicious_path)
    
    # Assert
    assert ".." not in sanitized
```

---

## Progress Tracking

### Daily Checklist
- [ ] Morning: Review yesterday's work
- [ ] Morning: Plan today's tasks
- [ ] Throughout: Run tests after each change
- [ ] Afternoon: Update STATUS.md
- [ ] Evening: Commit working code
- [ ] Evening: Update tasks.md

### Weekly Checklist
- [ ] Monday: Review week's goals
- [ ] Wednesday: Mid-week progress check
- [ ] Friday: Week review and planning
- [ ] Friday: Update PHASE_2_IMPLEMENTATION_PLAN.md

---

## Getting Help

### Documentation
- `PHASE_2_IMPLEMENTATION_PLAN.md` - Detailed plan
- `SHARED_BACKEND_INTERFACE.md` - Interface specs
- `SECURITY_WRAPPER_DESIGN.md` - Security design
- `ERROR_HANDLING_ROLLBACK_DESIGN.md` - Error handling

### Code References
- v02 workflows: `src/hiveforge/steering/workflows/`
- v02 tests: `tests/test_steering_cli.py`
- Existing error handling: `src/hiveforge/steering/error_handling.py`

### Questions to Ask
1. Does this maintain v02 compatibility?
2. Is this tested?
3. Is this secure?
4. Is this documented?
5. Does this follow the design?

---

## Success Indicators

### You're on Track If:
- ✅ v02 tests still pass (40/40)
- ✅ New tests are passing
- ✅ Code coverage > 80%
- ✅ No security vulnerabilities
- ✅ Performance impact < 10%

### Warning Signs:
- ⚠️ v02 tests failing
- ⚠️ Test coverage dropping
- ⚠️ Performance degrading
- ⚠️ Circular dependencies
- ⚠️ Security issues

---

## Quick Commands Reference

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/shared/test_base.py -v

# Run with coverage
pytest tests/ --cov=src/hiveforge/steering/shared --cov-report=term-missing

# Run v02 regression tests
pytest tests/test_steering_cli.py -v

# Check code style
flake8 src/hiveforge/steering/shared/

# Type checking (if using mypy)
mypy src/hiveforge/steering/shared/
```

---

**Ready to Start?** Begin with Step 1: Create Directory Structure

**Questions?** Review `PHASE_2_IMPLEMENTATION_PLAN.md` for details

**Stuck?** Check the "Common Issues & Solutions" section above
