# Phase 2 Implementation Plan: Shared Backend

**Feature**: steering-power-conversion  
**Phase**: 2 - Shared Backend Implementation  
**Duration**: Week 3-4  
**Status**: Planning  
**Created**: 2026-02-17

---

## Executive Summary

Phase 2 focuses on extracting common logic from the v02 implementation into a shared backend that will be used by both CLI and Power interfaces. This is the critical foundation that enables CLI/Power equivalence.

**Key Deliverables**:
1. Shared backend module structure
2. Security wrappers and validation
3. Error handling with automatic rollback
4. Telemetry system
5. Comprehensive unit tests

---

## Prerequisites

### Completed (Phase 1)
- ✅ Architecture validation tests created
- ✅ v02 stability confirmed (40/40 tests passing)
- ✅ Shared backend interface designed
- ✅ Security wrapper design documented
- ✅ Error handling design documented

### Required Before Starting
- [ ] Review Phase 1 validation report
- [ ] Confirm v02 test suite still passing
- [ ] Review shared backend design documents
- [ ] Set up development environment

---

## Implementation Strategy

### Approach: Incremental Extraction

1. **Start with simplest workflow** (Validate) - least dependencies
2. **Extract common patterns** into base classes
3. **Refactor existing workflows** to use shared backend
4. **Add security layer** around shared backend
5. **Add error handling** with rollback
6. **Add telemetry** for monitoring
7. **Test thoroughly** at each step

### Key Principles

- **No breaking changes** to v02 CLI during extraction
- **Test-driven** - write tests before refactoring
- **Incremental** - small, verifiable steps
- **Backward compatible** - v02 tests must continue passing

---

## Task Breakdown

### 2.1 Refactor Existing Code for Shared Backend

#### 2.1.1 Create Shared Module Structure
**Estimated Time**: 1 hour

**Tasks**:
- Create `src/hiveforge/steering/shared/` directory
- Create `__init__.py` with module exports
- Create `base.py` for base classes
- Create `adapters.py` for workflow adapters

**Acceptance Criteria**:
- Directory structure matches design document
- Module imports work correctly
- No circular dependencies

#### 2.1.2 Extract Common Workflow Logic
**Estimated Time**: 4 hours

**Tasks**:
- Analyze v02 workflows for common patterns
- Identify shared configuration handling
- Identify shared validation logic
- Identify shared file I/O patterns
- Document extraction plan

**Acceptance Criteria**:
- Common patterns documented
- Extraction plan reviewed
- No duplicate logic identified

#### 2.1.3 Create SharedWorkflowBase Class
**Estimated Time**: 3 hours

**Tasks**:
- Define base class interface
- Implement common configuration handling
- Implement common validation
- Implement common error handling hooks
- Write unit tests for base class

**Acceptance Criteria**:
- Base class follows design specification
- All common methods implemented
- Unit tests pass
- Documentation complete

#### 2.1.4 Implement SharedInitWorkflow Adapter
**Estimated Time**: 4 hours

**Tasks**:
- Create adapter class extending SharedWorkflowBase
- Wrap existing InitWorkflow logic
- Implement adapter interface
- Write unit tests
- Verify v02 CLI tests still pass

**Acceptance Criteria**:
- Adapter implements shared interface
- Existing functionality preserved
- Unit tests pass
- v02 CLI tests still pass (40/40)

#### 2.1.5 Implement SharedUpdateWorkflow Adapter
**Estimated Time**: 4 hours

**Tasks**:
- Create adapter class extending SharedWorkflowBase
- Wrap existing UpdateWorkflow logic
- Implement adapter interface
- Write unit tests
- Verify v02 CLI tests still pass

**Acceptance Criteria**:
- Adapter implements shared interface
- Existing functionality preserved
- Unit tests pass
- v02 CLI tests still pass (40/40)

#### 2.1.6 Implement SharedValidateWorkflow Adapter
**Estimated Time**: 3 hours

**Tasks**:
- Create adapter class extending SharedWorkflowBase
- Wrap existing ValidateWorkflow logic
- Implement adapter interface
- Write unit tests
- Verify v02 CLI tests still pass

**Acceptance Criteria**:
- Adapter implements shared interface
- Existing functionality preserved
- Unit tests pass
- v02 CLI tests still pass (40/40)

#### 2.1.7 Implement SharedResetWorkflow Adapter
**Estimated Time**: 3 hours

**Tasks**:
- Create new reset workflow (not in v02)
- Implement template restoration logic
- Implement backup creation
- Write unit tests
- Add CLI command (optional for Phase 2)

**Acceptance Criteria**:
- Reset workflow implements shared interface
- Backup/restore logic works
- Unit tests pass
- Can reset individual files or all files

#### 2.1.8 Implement SharedDiscoveryWorkflow Adapter
**Estimated Time**: 3 hours

**Tasks**:
- Create adapter class extending SharedWorkflowBase
- Wrap existing discovery logic
- Implement adapter interface
- Write unit tests
- Verify discovery works independently

**Acceptance Criteria**:
- Adapter implements shared interface
- Discovery logic preserved
- Unit tests pass
- Can be used standalone

---

### 2.2 Security Implementation

#### 2.2.1 Implement security_wrappers.py Module
**Estimated Time**: 4 hours

**Tasks**:
- Create `src/hiveforge/steering/shared/security_wrappers.py`
- Implement `validate_parameters()` function
- Implement `sanitize_path()` function
- Implement `ResourceLimiter` class
- Implement `secure_tool_execution()` decorator
- Implement `obfuscate_errors()` function

**Acceptance Criteria**:
- All security functions implemented
- Follows security design document
- No security vulnerabilities
- Performance impact < 5%

#### 2.2.2 Write Security Unit Tests
**Estimated Time**: 3 hours

**Tasks**:
- Create `tests/test_security_wrappers.py`
- Test path traversal prevention
- Test parameter validation
- Test resource limits
- Test error obfuscation
- Test decorator functionality

**Acceptance Criteria**:
- All security functions tested
- Edge cases covered
- Attack scenarios tested
- 100% code coverage for security module

---

### 2.3 Error Handling with Rollback

#### 2.3.1 Implement error_handling.py Module
**Estimated Time**: 4 hours

**Tasks**:
- Create `src/hiveforge/steering/shared/error_handling.py`
- Implement `ToolExecutor` class
- Implement automatic backup creation
- Implement automatic rollback on failure
- Implement partial failure handling
- Implement user-friendly error messages

**Acceptance Criteria**:
- All error handling implemented
- Follows error handling design document
- Rollback works correctly
- User messages are clear

#### 2.3.2 Write Error Handling Unit Tests
**Estimated Time**: 3 hours

**Tasks**:
- Create `tests/test_shared_error_handling.py`
- Test backup creation
- Test rollback on failure
- Test partial failure handling
- Test error message formatting
- Test edge cases

**Acceptance Criteria**:
- All error scenarios tested
- Rollback verified
- Edge cases covered
- > 90% code coverage

---

### 2.4 Shared Telemetry System

#### 2.4.1 Implement telemetry.py Module
**Estimated Time**: 3 hours

**Tasks**:
- Create `src/hiveforge/steering/shared/telemetry.py`
- Design telemetry data structure
- Implement telemetry collection
- Implement telemetry storage in `.kiro/.telemetry/`
- Add telemetry to shared workflows

**Acceptance Criteria**:
- Telemetry data structure defined
- Collection works for both CLI and Power
- Storage is privacy-compliant
- No PII collected

#### 2.4.2 Write Telemetry Unit Tests
**Estimated Time**: 2 hours

**Tasks**:
- Create `tests/test_telemetry.py`
- Test data collection
- Test data storage
- Test privacy compliance
- Test performance impact

**Acceptance Criteria**:
- All telemetry functions tested
- Privacy verified
- Performance impact < 1%
- > 80% code coverage

---

### 2.5 Unit Tests for Shared Backend

#### 2.5.1 Create Comprehensive Test Suite
**Estimated Time**: 4 hours

**Tasks**:
- Create `tests/test_shared_backend.py`
- Test all shared workflow adapters
- Test integration between components
- Test error scenarios
- Test performance

**Acceptance Criteria**:
- All adapters tested
- Integration tests pass
- > 80% code coverage overall
- > 90% coverage for critical paths

#### 2.5.2 Validate Shared Backend Independence
**Estimated Time**: 2 hours

**Tasks**:
- Test shared backend without CLI
- Test shared backend without Power
- Verify no circular dependencies
- Verify clean interfaces

**Acceptance Criteria**:
- Shared backend works standalone
- No dependencies on CLI or Power
- Clean separation of concerns
- Interface contracts validated

---

## Testing Strategy

### Unit Testing
- Test each module independently
- Mock external dependencies
- Focus on edge cases
- Aim for > 80% coverage

### Integration Testing
- Test workflow adapters with real workflows
- Test security wrappers with real operations
- Test error handling with real failures
- Test telemetry with real data

### Regression Testing
- Run v02 CLI test suite after each change
- Ensure 40/40 tests continue passing
- No breaking changes to existing functionality

### Performance Testing
- Measure overhead of security wrappers
- Measure overhead of error handling
- Measure overhead of telemetry
- Ensure < 10% performance impact overall

---

## Risk Management

### Risk 1: Breaking v02 CLI
**Probability**: Medium  
**Impact**: High  
**Mitigation**: 
- Run v02 tests after each change
- Use feature flags for new code
- Keep old code paths until validated

### Risk 2: Performance Degradation
**Probability**: Medium  
**Impact**: Medium  
**Mitigation**:
- Benchmark before and after
- Optimize hot paths
- Use lazy loading where possible

### Risk 3: Security Vulnerabilities
**Probability**: Low  
**Impact**: Critical  
**Mitigation**:
- Security review of all code
- Penetration testing
- Follow security design strictly

### Risk 4: Incomplete Extraction
**Probability**: Medium  
**Impact**: High  
**Mitigation**:
- Thorough code analysis
- Multiple review passes
- Integration tests

---

## Success Criteria

### Must Have
- [ ] All 5 workflow adapters implemented
- [ ] Security wrappers implemented and tested
- [ ] Error handling with rollback implemented
- [ ] Telemetry system implemented
- [ ] v02 CLI tests still pass (40/40)
- [ ] > 80% code coverage for new code

### Should Have
- [ ] > 90% code coverage for critical paths
- [ ] Performance impact < 10%
- [ ] Documentation complete
- [ ] Code review completed

### Nice to Have
- [ ] Performance benchmarks
- [ ] Security audit report
- [ ] Refactoring recommendations

---

## Timeline

### Week 3
- **Day 1-2**: Task 2.1 (Shared Backend Structure)
- **Day 3**: Task 2.2 (Security Implementation)
- **Day 4**: Task 2.3 (Error Handling)
- **Day 5**: Task 2.4 (Telemetry)

### Week 4
- **Day 1-2**: Task 2.5 (Unit Tests)
- **Day 3**: Integration testing
- **Day 4**: Performance testing
- **Day 5**: Documentation and review

---

## Dependencies

### Blocks
- Phase 3 (CLI Maintenance) depends on Phase 2 completion
- Phase 4 (Power Implementation) depends on Phase 2 completion

### Depends On
- Phase 1 completion (✅ Complete)
- v02 stability (✅ Confirmed)
- Design documents (✅ Complete)

---

## Next Steps

1. Review this implementation plan
2. Confirm approach with team
3. Set up development environment
4. Begin Task 2.1.1 (Create Shared Module Structure)

---

## Notes

- This is a planning document for SPECS mode
- Actual implementation will be done in a separate session
- Focus is on careful planning and risk mitigation
- v02 stability is critical - must not break existing functionality

---

**Document Status**: Draft - Ready for Review  
**Next Review**: Before starting implementation  
**Owner**: Development Team
