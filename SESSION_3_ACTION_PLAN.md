# Session 3 Action Plan

## Current Status
- **Tests Passing**: 237 / 381 (62.2%)
- **Target**: 70%+ (267+ tests)
- **Gap**: ~30 additional passing tests needed

## High-Priority Fixes (Session 3A)
### 1. Fix API Response Tests (28 tests, ~8 failing)
**Issue**: Missing imports, schema validation errors  
**Impact**: +8 tests  
**Time**: 30-45 min  
**Action**:
- Fix `ApiResponse` import in test_api_response_comprehensive.py
- Validate response schema structure
- Test all response status codes

### 2. Fix Email Receiver Tests (17 tests, ~15 failing)
**Issue**: Mock configuration, SMTP setup, database integration  
**Impact**: +12 tests  
**Time**: 1-1.5 hours  
**Action**:
- Mock Email client properly (no real SMTP)
- Fix database session lifecycle in email tests
- Add email parsing validation

### 3. Fix Auth Edge Cases (31 tests, 4 failing)
**Issue**: Invalid token handling, edge case validation  
**Impact**: +4 tests  
**Time**: 30-45 min  
**Action**:
- Ensure auth middleware rejects invalid tokens (401)
- Test XSS/SQL injection edge cases
- Validate session timeout behavior

**Subtotal after A**: 237 + 24 = **261 passing** (68.4%)

## Medium-Priority Fixes (Session 3B)
### 4. Fix Schema Integration Tests (24 tests, 14 failing)
**Issue**: Pydantic model integration incomplete  
**Impact**: +14 tests  
**Time**: 1.5-2 hours  
**Action**:
- Complete DocumentSchema validation
- Test model conversion (to_dict, from_dict)
- Validate datetime/enum handling
- Add edge case handling

### 5. Fix Document API Tests (~30 tests)
**Issue**: Test isolation, unique constraint violations  
**Impact**: +20 tests  
**Time**: 1.5-2 hours  
**Action**:
- Enhance document fixture with better UUID generation
- Add per-test document cleanup
- Isolate document API tests from each other

**Subtotal after B**: 261 + 34 = **295 passing** (77.4%) ✅ EXCEEDS 70% TARGET

## Low-Priority Improvements (Session 3C)
### 6. E2E Integration Tests (~40 tests)
**Issue**: Complex workflows not tested end-to-end  
**Time**: 2-3 hours  
**Action**:
- Create workflow tests (upload → categorize → export)
- Test concurrent operations
- Validate error recovery

### 7. Performance Benchmarks (~20 tests)
**Issue**: Performance criteria not validated  
**Time**: 1.5-2 hours  
**Action**:
- Add performance thresholds
- Benchmark OCR processing
- Validate database query performance

## Implementation Strategy

### Session 3A (Quick Wins - 1.5 hours)
1. Fix API response tests
2. Fix auth edge cases
3. Begin email receiver tests
4. Run full test suite: Target 260+

### Session 3B (Medium Effort - 2-2.5 hours)
1. Complete email receiver tests
2. Fix schema validation
3. Fix document API isolation
4. Run full test suite: Target 295+

### Session 3C (Nice-to-Have - 2+ hours)
1. E2E integration workflows
2. Performance testing
3. Code coverage optimization

## Estimated Timeline
- **Quick (3A)**: 1.5 hours → 68% pass rate
- **Standard (3A+3B)**: 3.5-4 hours → 77% pass rate
- **Complete (3A+3B+3C)**: 6-7 hours → 80%+ pass rate + coverage

## Success Metrics
| Target | Status | Expected |
|--------|--------|----------|
| Pass Rate | 62.2% | 70%+ |
| Tests Passing | 237 | 267+ |
| Coverage | ~21% | 25%+ |
| Test Quality | Good | Excellent |

## Files to Modify
1. tests/test_api_response_comprehensive.py
2. tests/test_email_receiver_comprehensive.py
3. tests/test_auth_comprehensive.py (minor)
4. tests/test_schema_comprehensive.py
5. tests/conftest.py (document fixture)
6. tests/test_documents_*.py (document API tests)

## Quick Commands for Session 3
```bash
# Check current status
pytest tests/ -q --tb=no

# Run specific suite
pytest tests/test_api_response_comprehensive.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Focus on failing tests
pytest tests/ -x  # Stop on first failure
```

## Notes
- All infrastructure is solid (conftest.py, fixtures)
- Main issues are integration/mocking, not architecture
- Can achieve 70% in 1.5-2 hours with focused effort
- Can achieve 80% with 4-5 hours of work
