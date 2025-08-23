# Console Link Refactoring Plan

## Overview

This document outlines a comprehensive refactoring plan for the console_link project to transition from a CLI-first architecture to a clean, layered architecture that supports both CLI and API interfaces effectively. The current codebase suffers from tight coupling between business logic and presentation concerns, primarily through the pervasive use of `CommandResult` objects.

## Current Architecture Issues

1. **CommandResult Coupling**: Business logic returns `CommandResult` objects instead of raising proper exceptions
2. **Mixed Concerns**: Business logic is intertwined with CLI presentation formatting
3. **API Limitations**: Building proper REST APIs requires significant rework due to CLI-centric design
4. **Naming Conflicts**: Same filenames used across different directories (e.g., multiple `snapshot.py` files)
5. **Testing Challenges**: Difficult to unit test business logic in isolation

## Target Architecture

### Design Principles

1. **Domain-Driven Design**: Pure domain models that are agnostic to presentation layer
2. **Exception-Based Error Handling**: Services raise exceptions; presentation layers handle them appropriately
3. **Dependency Injection**: Loose coupling through interfaces
4. **Single Responsibility**: Each module has one clear purpose
5. **API-First Development**: Business logic designed to support multiple interfaces

### Directory Structure

```
console_link/
├── domain/                    # Pure domain models and interfaces
│   ├── entities/             # Domain entities (data models)
│   │   ├── snapshot_entity.py
│   │   ├── cluster_entity.py
│   │   ├── backfill_entity.py
│   │   ├── replay_entity.py
│   │   ├── metadata_entity.py
│   │   └── kafka_entity.py
│   │
│   ├── value_objects/        # Immutable domain value objects
│   │   ├── auth_config.py
│   │   ├── snapshot_config.py
│   │   ├── s3_config.py
│   │   ├── container_config.py
│   │   └── metrics_config.py
│   │
│   └── exceptions/           # Domain-specific exceptions
│       ├── snapshot_errors.py
│       ├── cluster_errors.py
│       ├── backfill_errors.py
│       └── common_errors.py
│
├── services/                 # Business logic layer
│   ├── snapshot_service.py   # Snapshot operations
│   ├── cluster_service.py    # Cluster operations
│   ├── backfill_service.py   # Backfill operations
│   ├── metadata_service.py   # Metadata operations
│   ├── replay_service.py     # Replay operations
│   ├── kafka_service.py      # Kafka operations
│   └── metrics_service.py    # Metrics collection
│
├── infrastructure/           # External integrations
│   ├── command_executor.py   # System command execution
│   ├── docker_manager.py     # Docker container management
│   ├── k8s_manager.py        # Kubernetes management
│   ├── ecs_manager.py        # ECS management
│   ├── http_client.py        # HTTP client wrapper
│   └── metrics_collector.py  # Metrics integration
│
├── repositories/            # Data access layer
│   ├── session_repository.py
│   ├── metadata_repository.py
│   ├── backfill_work_repository.py
│   └── base_repository.py
│
├── cli/                     # CLI-specific code
│   ├── commands/            # Click command groups
│   │   ├── snapshot_commands.py
│   │   ├── cluster_commands.py
│   │   ├── backfill_commands.py
│   │   ├── metadata_commands.py
│   │   ├── replay_commands.py
│   │   └── kafka_commands.py
│   │
│   ├── formatters/          # CLI output formatting
│   │   ├── table_formatter.py
│   │   ├── json_formatter.py
│   │   ├── progress_formatter.py
│   │   └── base_formatter.py
│   │
│   ├── error_handlers.py    # CLI error handling
│   └── console.py           # Main CLI entry point
│
├── api/                     # REST API layer
│   ├── routers/            # FastAPI routers
│   │   ├── snapshot_router.py
│   │   ├── cluster_router.py
│   │   ├── backfill_router.py
│   │   ├── metadata_router.py
│   │   ├── system_router.py
│   │   └── session_router.py
│   │
│   ├── schemas/            # Pydantic request/response models
│   │   ├── snapshot_schemas.py
│   │   ├── cluster_schemas.py
│   │   ├── backfill_schemas.py
│   │   ├── common_schemas.py
│   │   └── error_schemas.py
│   │
│   ├── middleware/         # API middleware
│   │   ├── error_middleware.py
│   │   ├── auth_middleware.py
│   │   └── logging_middleware.py
│   │
│   └── app.py              # FastAPI app configuration
│
├── shared/                 # Shared utilities
│   ├── config_loader.py    # Configuration management
│   ├── logging_setup.py    # Logging configuration
│   ├── validators.py       # Shared validation logic
│   ├── converters.py       # Data conversion utilities
│   └── constants.py        # Shared constants
│
└── tests/                  # Test organization mirrors source
    ├── unit/
    ├── integration/
    └── e2e/
```

### Key Architectural Components

#### 1. Domain Layer
- **Entities**: Core business objects with identity (e.g., Snapshot, Cluster)
- **Value Objects**: Immutable objects without identity (e.g., AuthConfig, S3Config)
- **Exceptions**: Domain-specific exceptions that services raise

#### 2. Service Layer
- Contains all business logic
- Raises exceptions on errors (no CommandResult)
- Depends on repository and infrastructure interfaces
- Stateless and testable

#### 3. Infrastructure Layer
- Handles external system integration
- Implements interfaces defined in domain layer
- Contains adapters for Docker, K8s, ECS, etc.

#### 4. Presentation Layers (CLI & API)
- Transform service exceptions to appropriate responses
- Handle formatting and user interaction
- No business logic

## Example: Snapshot Module Refactoring

### Current Structure
```python
# models/snapshot.py - Mixed concerns
class S3Snapshot(Snapshot):
    def create(self, *args, **kwargs) -> CommandResult:
        # Business logic mixed with CLI formatting
        # Returns CommandResult instead of raising exceptions
```

### Target Structure
```python
# domain/entities/snapshot_entity.py
@dataclass
class SnapshotEntity:
    name: str
    repository_name: str
    state: SnapshotState
    ...

# services/snapshot_service.py
class SnapshotService:
    def create_snapshot(self, config: SnapshotConfig) -> SnapshotEntity:
        # Pure business logic
        # Raises SnapshotCreationError on failure
        
# cli/commands/snapshot_commands.py
@click.command()
def create_snapshot_cmd(ctx):
    try:
        snapshot = snapshot_service.create_snapshot(config)
        formatter.display_snapshot(snapshot)
    except SnapshotCreationError as e:
        error_handler.handle_snapshot_error(e)
        
# api/routers/snapshot_router.py
@router.post("/snapshot", response_model=SnapshotResponse)
def create_snapshot(request: CreateSnapshotRequest):
    try:
        snapshot = snapshot_service.create_snapshot(request.to_config())
        return SnapshotResponse.from_entity(snapshot)
    except SnapshotCreationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

# Transition Plan

## Phase 1: Foundation (Week 1-2)

### Step 1.1: Create New Directory Structure
- Create all new directories as outlined above
- Add `__init__.py` files where needed
- Update `.gitignore` if necessary

### Step 1.2: Create Base Classes and Interfaces
- Create base exception classes in `domain/exceptions/common_errors.py`
- Create base repository interface in `repositories/base_repository.py`
- Define common value objects in `domain/value_objects/`

### Step 1.3: Setup Shared Utilities
- Move logging configuration to `shared/logging_setup.py`
- Extract validation logic to `shared/validators.py`
- Create `shared/constants.py` for shared constants

## Phase 2: Domain Model Migration (Week 3-4)

### Step 2.1: Extract Domain Entities
- Create `SnapshotEntity` in `domain/entities/snapshot_entity.py`
- Create `ClusterEntity` in `domain/entities/cluster_entity.py`
- Create other entities following the same pattern

### Step 2.2: Define Domain Exceptions
- Create specific exception hierarchies for each domain
- Map existing error conditions to new exceptions

### Step 2.3: Create Value Objects
- Extract configuration objects to value objects
- Ensure immutability and validation

## Phase 3: Service Layer Implementation (Week 5-6)

### Step 3.1: Snapshot Service Migration
1. Create `services/snapshot_service.py`
2. Extract business logic from `models/snapshot.py`
3. Replace CommandResult returns with exceptions
4. Write comprehensive unit tests

### Step 3.2: Cluster Service Migration
1. Create `services/cluster_service.py`
2. Extract business logic from middleware and models
3. Implement proper error handling
4. Write unit tests

### Step 3.3: Continue with Other Services
- Follow the same pattern for backfill, metadata, replay, and kafka services

## Phase 4: Infrastructure Extraction (Week 7-8)

### Step 4.1: Command Execution
- Move `CommandRunner` to `infrastructure/command_executor.py`
- Create abstraction for command execution
- Implement proper error handling

### Step 4.2: Container Management
- Extract Docker operations to `infrastructure/docker_manager.py`
- Extract K8s operations to `infrastructure/k8s_manager.py`
- Extract ECS operations to `infrastructure/ecs_manager.py`

## Phase 5: CLI Refactoring (Week 9-10)

### Step 5.1: Command Migration
1. Create new command structure in `cli/commands/`
2. Update commands to use services instead of middleware
3. Implement proper error handling and formatting

### Step 5.2: Formatter Implementation
- Create formatters for different output types
- Move presentation logic out of business logic

### Step 5.3: Update CLI Entry Point
- Update `console.py` to use new command structure
- Ensure backward compatibility

## Phase 6: API Enhancement (Week 11-12)

### Step 6.1: Schema Definition
- Create Pydantic schemas for all endpoints
- Ensure proper validation and serialization

### Step 6.2: Router Implementation
- Update routers to use services
- Implement proper error handling
- Add comprehensive API documentation

### Step 6.3: Middleware Setup
- Implement error handling middleware
- Add logging and monitoring

## Phase 7: Testing and Documentation (Week 13-14)

### Step 7.1: Test Coverage
- Achieve >90% unit test coverage for services
- Write integration tests for critical paths
- Add E2E tests for CLI and API

### Step 7.2: Documentation Update
- Update README with new architecture
- Document API endpoints
- Create migration guide for users

## Phase 8: Cleanup and Deprecation (Week 15-16)

### Step 8.1: Remove Old Code
- Delete deprecated middleware layer
- Remove old model implementations
- Clean up unused imports

### Step 8.2: Final Testing
- Run full regression test suite
- Performance testing
- User acceptance testing

## Migration Guidelines

### For Each Module:
1. **Extract Domain Model**: Define entities, value objects, and exceptions
2. **Create Service**: Move business logic, replace CommandResult with exceptions
3. **Update Infrastructure**: Extract external dependencies
4. **Refactor CLI**: Update commands to use services
5. **Enhance API**: Create proper schemas and error handling
6. **Write Tests**: Unit, integration, and E2E tests
7. **Document Changes**: Update relevant documentation

### Testing Strategy:
- Write tests for new code before removing old code
- Maintain parallel implementations during transition
- Use feature flags if needed for gradual rollout

### Rollback Plan:
- Keep old code in separate branch
- Tag releases before major changes
- Document rollback procedures

## Success Criteria

1. **No CommandResult in Services**: All services raise exceptions
2. **100% API Coverage**: All CLI functions available via API
3. **Test Coverage**: >90% unit test coverage
4. **Performance**: No regression in performance metrics
5. **Documentation**: Complete API and architecture documentation

## Notes

- This plan is designed to be executed incrementally
- Each phase can be adjusted based on team capacity
- Prioritize high-impact modules first
- Maintain backward compatibility where possible

---

# Appendix: LLM Execution Guide

## File Mapping Reference

### Current to Target File Mappings

| Current File | Target File(s) | Notes |
|-------------|----------------|-------|
| `models/snapshot.py` | `domain/entities/snapshot_entity.py`<br>`services/snapshot_service.py`<br>`infrastructure/command_executor.py` | Split by concern |
| `models/cluster.py` | `domain/entities/cluster_entity.py`<br>`domain/value_objects/auth_config.py`<br>`services/cluster_service.py` | Extract auth to value object |
| `models/command_result.py` | *(Delete)* | Replace with exceptions |
| `middleware/snapshot.py` | `cli/commands/snapshot_commands.py` | Move to CLI layer |
| `api/snapshot.py` | `api/routers/snapshot_router.py`<br>`api/schemas/snapshot_schemas.py` | Split router and schemas |

## Execution Checkpoints

### Phase 1 Validation
```bash
# After creating directory structure
find console_link -type d -name "__pycache__" -prune -o -type d -print | sort

# Expected output should match the planned structure
```

### Phase 2 Validation
```python
# Test that entities are properly defined
from console_link.domain.entities.snapshot_entity import SnapshotEntity
from console_link.domain.exceptions.snapshot_errors import SnapshotCreationError

# Should import without errors
```

### Phase 3 Validation
```bash
# Run unit tests for each service
pipenv run pytest tests/unit/services/test_snapshot_service.py -v
```

## Code Templates

### Domain Entity Template
```python
# domain/entities/{entity_name}_entity.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class {Entity}State(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class {Entity}Entity:
    """Domain entity for {entity_name}."""
    id: str
    name: str
    state: {Entity}State
    created_at: datetime
    updated_at: datetime
    # Add domain-specific fields
    
    def __post_init__(self):
        """Validate entity invariants."""
        if not self.id:
            raise ValueError("Entity ID cannot be empty")
```

### Service Template
```python
# services/{service_name}_service.py
import logging
from typing import List, Optional
from console_link.domain.entities.{entity}_entity import {Entity}Entity
from console_link.domain.exceptions.{domain}_errors import (
    {Domain}NotFoundError,
    {Domain}CreationError,
    {Domain}ValidationError
)

logger = logging.getLogger(__name__)

class {Service}Service:
    """Business logic for {domain} operations."""
    
    def __init__(self, repository, infrastructure_service):
        self.repository = repository
        self.infrastructure = infrastructure_service
    
    def create_{entity}(self, config: dict) -> {Entity}Entity:
        """Create a new {entity}.
        
        Raises:
            {Domain}ValidationError: If config is invalid
            {Domain}CreationError: If creation fails
        """
        try:
            # Validate input
            self._validate_config(config)
            
            # Business logic here
            result = self.infrastructure.execute_operation(config)
            
            # Create and persist entity
            entity = {Entity}Entity(
                id=result['id'],
                name=config['name'],
                state={Entity}State.PENDING
            )
            
            self.repository.save(entity)
            return entity
            
        except ValidationError as e:
            logger.error(f"Validation failed: {e}")
            raise {Domain}ValidationError(str(e))
        except Exception as e:
            logger.error(f"Failed to create {entity}: {e}")
            raise {Domain}CreationError(f"Creation failed: {str(e)}")
```

### CLI Command Template
```python
# cli/commands/{domain}_commands.py
import click
from console_link.services.{service}_service import {Service}Service
from console_link.domain.exceptions.{domain}_errors import {Domain}Error
from console_link.cli.formatters.{domain}_formatter import {Domain}Formatter

@click.group(name="{domain}")
@click.pass_context
def {domain}_group(ctx):
    """Commands for {domain} operations."""
    ctx.obj['{service}'] = {Service}Service(
        repository=ctx.obj['repositories']['{domain}'],
        infrastructure=ctx.obj['infrastructure']['{domain}']
    )
    ctx.obj['formatter'] = {Domain}Formatter(json_output=ctx.obj.get('json', False))

@{domain}_group.command(name="create")
@click.option('--name', required=True, help='Name of the {domain}')
@click.pass_context
def create_{domain}_cmd(ctx, name):
    """Create a new {domain}."""
    service = ctx.obj['{service}']
    formatter = ctx.obj['formatter']
    
    try:
        entity = service.create_{domain}({'name': name})
        click.echo(formatter.format_entity(entity))
    except {Domain}ValidationError as e:
        click.echo(formatter.format_error(f"Validation error: {e}"), err=True)
        ctx.exit(1)
    except {Domain}Error as e:
        click.echo(formatter.format_error(f"Operation failed: {e}"), err=True)
        ctx.exit(1)
```

### API Router Template
```python
# api/routers/{domain}_router.py
from fastapi import APIRouter, HTTPException, Depends
from console_link.api.schemas.{domain}_schemas import (
    Create{Domain}Request,
    {Domain}Response,
    {Domain}ErrorResponse
)
from console_link.services.{service}_service import {Service}Service
from console_link.domain.exceptions.{domain}_errors import {Domain}Error

router = APIRouter(prefix="/{domain}", tags=["{domain}"])

@router.post("/", response_model={Domain}Response)
async def create_{domain}(
    request: Create{Domain}Request,
    service: {Service}Service = Depends(get_{service}_service)
):
    """Create a new {domain}."""
    try:
        entity = service.create_{domain}(request.dict())
        return {Domain}Response.from_entity(entity)
    except {Domain}ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except {Domain}Error as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Migration Patterns

### Pattern 1: Extracting Business Logic from CommandResult
```python
# BEFORE (in models or middleware)
def create_snapshot(self, config) -> CommandResult:
    try:
        # business logic
        result = self._do_something(config)
        return CommandResult(success=True, value=result)
    except Exception as e:
        return CommandResult(success=False, value=str(e))

# AFTER (in service)
def create_snapshot(self, config) -> SnapshotEntity:
    # business logic
    result = self._do_something(config)
    return SnapshotEntity.from_dict(result)
    # Exceptions propagate naturally
```

### Pattern 2: Separating Infrastructure Concerns
```python
# BEFORE (mixed in model)
class S3Snapshot:
    def create(self):
        command = f"/root/createSnapshot/bin/CreateSnapshot {args}"
        result = subprocess.run(command, shell=True)
        # ... handle result

# AFTER 
# In infrastructure/command_executor.py
class CommandExecutor:
    def execute(self, command: str, args: dict) -> dict:
        # Handle subprocess execution
        
# In service
class SnapshotService:
    def create_snapshot(self, config):
        result = self.command_executor.execute(
            "/root/createSnapshot/bin/CreateSnapshot",
            config
        )
        # Pure business logic
```

## Common Pitfalls and Solutions

### Pitfall 1: Circular Dependencies
**Problem**: Service A depends on Service B which depends on Service A
**Solution**: Use dependency injection and interfaces
```python
# Define interface in domain layer
class SnapshotRepositoryInterface(ABC):
    @abstractmethod
    def save(self, snapshot: SnapshotEntity): pass
```

### Pitfall 2: Leaking CLI Concepts into Services
**Problem**: Services returning formatted strings or CLI-specific data
**Solution**: Services return domain entities; formatting happens in presentation layer

### Pitfall 3: Incomplete Exception Handling
**Problem**: Not all error cases covered when removing CommandResult
**Solution**: Map each CommandResult failure to a specific exception type

## Testing Strategy for Each Phase

### Unit Test Example
```python
# tests/unit/services/test_snapshot_service.py
import pytest
from unittest.mock import Mock, MagicMock
from console_link.services.snapshot_service import SnapshotService
from console_link.domain.exceptions.snapshot_errors import SnapshotCreationError

class TestSnapshotService:
    def test_create_snapshot_success(self):
        # Arrange
        mock_repo = Mock()
        mock_infra = Mock()
        mock_infra.execute_operation.return_value = {'id': '123', 'status': 'created'}
        
        service = SnapshotService(mock_repo, mock_infra)
        
        # Act
        result = service.create_snapshot({'name': 'test-snapshot'})
        
        # Assert
        assert result.id == '123'
        assert result.name == 'test-snapshot'
        mock_repo.save.assert_called_once()
    
    def test_create_snapshot_infrastructure_failure(self):
        # Arrange
        mock_repo = Mock()
        mock_infra = Mock()
        mock_infra.execute_operation.side_effect = Exception("Connection failed")
        
        service = SnapshotService(mock_repo, mock_infra)
        
        # Act & Assert
        with pytest.raises(SnapshotCreationError) as exc_info:
            service.create_snapshot({'name': 'test-snapshot'})
        
        assert "Connection failed" in str(exc_info.value)
        mock_repo.save.assert_not_called()
```

### Integration Test Example
```python
# tests/integration/test_snapshot_integration.py
import pytest
from console_link.services.snapshot_service import SnapshotService
from console_link.repositories.snapshot_repository import SnapshotRepository
from console_link.infrastructure.command_executor import CommandExecutor

@pytest.mark.integration
class TestSnapshotIntegration:
    def test_create_snapshot_end_to_end(self, test_db, test_config):
        # Use real implementations but test database
        repo = SnapshotRepository(test_db)
        executor = CommandExecutor(test_mode=True)
        service = SnapshotService(repo, executor)
        
        # Full integration test
        result = service.create_snapshot(test_config)
        
        # Verify in database
        saved = repo.get_by_id(result.id)
        assert saved.name == test_config['name']
```

## Incremental Migration Checklist

For each module being migrated:

- [ ] Create domain entity with proper validation
- [ ] Create domain exceptions for all error cases  
- [ ] Create service with business logic (no CommandResult)
- [ ] Create repository interface and implementation
- [ ] Extract infrastructure concerns to separate class
- [ ] Update CLI commands to use service
- [ ] Update API routes to use service
- [ ] Write unit tests for service (>90% coverage)
- [ ] Write integration tests for critical paths
- [ ] Update imports in dependent modules
- [ ] Run full test suite
- [ ] Update documentation

## Validation Commands

```bash
# After each phase, run these commands to validate:

# 1. Check imports are working
python -c "from console_link.domain.entities import *"

# 2. Run type checking
mypy console_link/

# 3. Run tests
pipenv run pytest tests/ -v

# 4. Check for CommandResult usage (should decrease over time)
grep -r "CommandResult" console_link/ --include="*.py" | grep -v "__pycache__" | wc -l

# 5. Verify API is working
curl -X GET http://localhost:8000/docs

# 6. Verify CLI is working
console --help
```
