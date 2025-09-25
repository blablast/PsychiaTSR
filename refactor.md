# PsychiaTSR Refactoring Plan

## Executive Summary

This refactoring plan addresses critical code quality issues identified in the PsychiaTSR project. The codebase shows signs of rapid development with good architectural intentions but suffers from fundamental violations of clean code principles.

**Key Metrics:**
- **Technical Debt**: High (Critical: 3, High: 4, Medium: 5 issues)
- **Test Coverage**: 1.6% (3 test files only)
- **Maintainability**: Low (God classes, tight coupling)
- **Code Duplication**: 90% in database operations
- **Architecture Compliance**: Poor (layered architecture violations)

## Phase 1: Critical Issues (Priority: URGENT)

### 1.1 Eliminate Database Operations Duplication
**Issue**: 90% identical CRUD methods across configuration loaders
**Files**:
- `src/core/config/loaders/app_loader.py`
- `src/core/config/loaders/agent_loader.py`
- `src/core/config/loaders/directory_loader.py`

**Solution**: Extract common database operations to base class
```python
class BaseConfigLoader:
    def save(self, data): # Common implementation
    def load(self, key): # Common implementation
    def exists(self, key): # Common implementation
```

**Expected Benefit**:
- 70% code reduction in loaders
- Single source of truth for database logic
- Easier maintenance and bug fixes
- Improved testability

### 1.2 Decompose God Class: PromptManagementService
**Issue**: Single class with 10+ responsibilities (394 lines)
**File**: `src/core/services/prompt_management_service.py`

**Solution**: Split into focused services using Single Responsibility Principle
```
PromptManagementService -> {
  PromptRepository (data access)
  PromptValidator (validation logic)
  PromptFormatter (text formatting)
  PromptVersionManager (versioning)
  PromptQueryService (complex queries)
}
```

**Expected Benefit**:
- Each class <100 lines
- Focused responsibilities
- Independent testing
- Parallel development possible
- Reduced cognitive load

### 1.3 Fix Configuration Anti-Pattern
**Issue**: Config class mixing static data, file I/O, and business logic
**File**: `config.py`

**Solution**: Implement proper configuration pattern
```python
# Clean separation
ConfigLoader -> ConfigValidator -> ConfigProvider
```

**Expected Benefit**:
- Testable configuration loading
- Environment-specific configs
- Validation separation
- No global state dependencies

## Phase 2: High Priority Issues

### 2.1 Simplify Over-Engineered DI Container
**Issue**: Complex dependency injection with minimal usage (YAGNI violation)
**Files**: `src/core/di/` (entire directory)

**Solution**: Replace with simple factory pattern or remove entirely
```python
# Instead of complex DI container
ServiceFactory.create_workflow_manager()
ServiceFactory.create_logger(config)
```

**Expected Benefit**:
- 80% code reduction in DI layer
- Simplified object creation
- Reduced learning curve
- Faster development

### 2.2 Break Down Long Methods
**Issue**: Methods exceeding 45+ lines in multiple files
**Files**: Various (identified in analysis)

**Solution**: Extract methods using Extract Method refactoring
- Target: Max 20 lines per method
- Use descriptive method names
- Single purpose per method

**Expected Benefit**:
- Improved readability
- Better testability
- Easier debugging
- Code reusability

### 2.3 Decouple UI from Core Logic
**Issue**: Streamlit dependencies in core business logic
**Files**: Multiple files importing `streamlit`

**Solution**: Implement proper layered architecture
```
UI Layer (Streamlit) -> Application Layer -> Domain Layer
```

**Expected Benefit**:
- Framework independence
- Better testability
- Parallel UI/logic development
- Technology migration flexibility

### 2.4 Fix Complex Inheritance Hierarchies
**Issue**: Deep inheritance making code hard to understand
**Files**: Agent hierarchy, Provider hierarchy

**Solution**: Favor composition over inheritance
```python
# Instead of deep inheritance
class Agent:
    def __init__(self, strategy: AgentStrategy, logger: Logger)
```

**Expected Benefit**:
- Reduced coupling
- More flexible design
- Easier testing
- Better code reuse

## Phase 3: Medium Priority Issues

### 3.1 Interface Segregation Principle
**Issue**: Fat interfaces forcing implementations to depend on unused methods

**Solution**: Split large interfaces into focused ones
```python
# Instead of one large interface
ILogger -> { IEventLogger, IMetricsLogger, IErrorLogger }
```

### 3.2 Replace Primitive Obsession
**Issue**: Using strings/ints instead of domain objects
**Files**: Throughout codebase (agent_type: str, stage_id: str)

**Solution**: Create value objects
```python
@dataclass(frozen=True)
class AgentType:
    value: str

    @classmethod
    def therapist(cls): return cls("therapist")
    @classmethod
    def supervisor(cls): return cls("supervisor")
```

### 3.3 Standardize Error Handling
**Issue**: 124 locations with different error handling patterns

**Solution**: Create centralized error handling strategy
```python
class ErrorHandler:
    def handle_domain_error(self, error: DomainError)
    def handle_infrastructure_error(self, error: InfraError)
```

### 3.4 Implement Testing Strategy
**Issue**: 1.6% test coverage (critical for maintainability)

**Solution**: Implement comprehensive testing pyramid
- Unit tests for business logic (80%)
- Integration tests for services (15%)
- End-to-end tests for workflows (5%)

### 3.5 Reduce Law of Demeter Violations
**Issue**: Long method chains and tight coupling throughout

**Solution**: Implement Tell, Don't Ask principle
```python
# Instead of
session.get_manager().get_state().update()

# Use
session.update_state()
```

## Phase 4: Architecture Improvements

### 4.1 Fix File Organization
**Current Issues**:
- Mixed concerns in single files
- Unclear module boundaries
- Deep directory nesting

**Solution**: Reorganize by domain
```
src/
├── domain/           # Business logic
├── application/      # Use cases
├── infrastructure/   # External concerns
└── ui/              # Presentation
```

### 4.2 Eliminate Circular Dependencies
**Issue**: Potential circular dependencies through global state

**Solution**: Implement dependency inversion with clear boundaries

### 4.3 Remove Legacy Code
**Files to remove/refactor**:
- `technical_log_display_old.py` (backup file)
- Unused test files
- Deprecated configuration files

## Implementation Timeline

### Week 1-2: Critical Issues
- Database operations consolidation
- PromptManagementService decomposition
- Configuration pattern fix

### Week 3-4: High Priority
- DI container simplification
- Method length reduction
- UI/Core decoupling

### Week 5-6: Medium Priority
- Interface segregation
- Primitive obsession fixes
- Error handling standardization

### Week 7-8: Architecture & Testing
- File reorganization
- Testing implementation
- Final cleanup

## Success Metrics

**Before Refactoring**:
- Test Coverage: 1.6%
- Cyclomatic Complexity: High
- Code Duplication: 90% in loaders
- Technical Debt: High

**After Refactoring** (Targets):
- Test Coverage: >80%
- Cyclomatic Complexity: Low-Medium
- Code Duplication: <5%
- Technical Debt: Low
- Build Time: Reduced by 30%
- Developer Onboarding: 50% faster

## Risk Mitigation

1. **Incremental Refactoring**: Small, focused changes
2. **Regression Testing**: Implement tests before major changes
3. **Feature Flags**: Toggle new implementations
4. **Code Reviews**: Mandatory for all changes
5. **Rollback Plan**: Keep working versions tagged

## Benefits Summary

- **Maintainability**: 70% improvement through focused classes
- **Testability**: 80% test coverage target vs 1.6% current
- **Extensibility**: Plugin architecture for new features
- **Developer Experience**: Faster onboarding, clearer code
- **Performance**: Reduced complexity, better caching
- **Quality**: Fewer bugs through better separation of concerns

## Conclusion

This refactoring plan addresses the most critical technical debt while maintaining system functionality. The phased approach ensures continuous delivery while systematically improving code quality. The expected ROI is high - cleaner code leads to faster feature development and fewer production issues.

**Recommended Action**: Start with Phase 1 (Critical Issues) immediately to prevent further technical debt accumulation.