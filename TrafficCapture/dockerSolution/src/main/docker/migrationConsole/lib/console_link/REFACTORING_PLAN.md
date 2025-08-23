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
