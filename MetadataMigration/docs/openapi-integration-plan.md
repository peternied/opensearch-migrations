# OpenAPI Generated Models Integration Plan

## Overview

This document outlines the systematic approach for integrating OpenAPI-generated models with existing CLI classes in the MetadataMigration module. The goal is to leverage trusted backend-generated data structures while preserving existing CLI functionality.

## Core Principles

1. **Follow existing pattern**: Use the approach established in `OpenApiConverter.java`
2. **Preserve CLI output**: Keep human-readable `asCliOutput()` methods unchanged
3. **Full Gson adoption**: Switch entirely to Gson-based JSON serialization (no Jackson compatibility bridge)
4. **Manual mapping for missing models**: Handle classes like `ConnectionContext` with manual conversion utilities
5. **Gradual migration**: Implement class by class to maintain stability

## Phase 1: Clusters Class Integration

### Target Models
- `ClustersInfo` - Container for source and target cluster information  
- `ClusterInfo` - Individual cluster details (type, version, uri, protocol, etc.)

**Status: ✅ COMPLETED** - Manual implementation approach used due to generated model dependency issues.

### Implementation Results

1. **✅ Created ClustersConverter class**
   - Location: `MetadataMigration/src/main/java/org/opensearch/migrations/cli/openapi/ClustersConverter.java`
   - Methods implemented:
     - `clusterReaderToMap(ClusterReader reader)` → `Map<String, Object>` 
     - `clusterWriterToMap(ClusterWriter writer)` → `Map<String, Object>`
     - `clustersToOpenApiJson(Clusters clusters)` → `String`

2. **✅ Updated Clusters.java**
   - Modified `asJsonOutput()` to use OpenAPI-compatible converter with fallback
   - Kept `JsonOutput` interface unchanged for backward compatibility
   - Preserved `asCliOutput()` unchanged as required

3. **✅ Implemented ConnectionContext mapping**
   - Extracts connection details from `ConnectionContext.toUserFacingData()`
   - Maps to OpenAPI model fields: uri, protocol, insecure, awsSpecificAuthentication, disableCompression
   - Handles various field name variations and data type conversions

4. **✅ Implemented Repository type handling**
   - Maps S3Repo URI information to `uri` field
   - Maps FileSystemRepo to `localRepository` field

### Generated Model Limitations Discovered
- OpenAPI generated models have missing dependencies (`org.opensearch.migration.JSON`, `okhttp3`, etc.)
- Models cannot compile in current project setup
- Manual JSON structure creation approach used instead
- JSON output matches OpenAPI schema expectations without using generated classes

## Phase 2: Additional CLI Classes

### Class Mapping Strategy

| Existing CLI Class | Generated Model | Implementation Priority |
|-------------------|-----------------|------------------------|
| `Clusters.java` | `ClustersInfo` + `ClusterInfo` | ✅ Phase 1 |
| `Items.java` | `ItemsInfo` + `ItemResult` | 🔄 Phase 2A |
| `Transformers.java` | `TransformationInfo` | 🔄 Phase 2B |
| Others | TBD | 🔄 Phase 2C |

### Implementation Approach for Each Class

1. Create converter class in `openapi/` package
2. Add conversion methods for complex object mapping
3. Update `asJsonOutput()` method to use generated models
4. Preserve existing `asCliOutput()` methods
5. Update unit tests to verify JSON structure

## Phase 3: Interface Updates

### JsonOutput Interface Changes

Before:
```java
public interface JsonOutput {
    JsonNode asJsonOutput();
}
```

After:
```java
public interface JsonOutput {
    String asJsonOutput();
}
```

### Compatibility Considerations

- All implementing classes will need to be updated simultaneously to avoid compilation errors
- Unit tests expecting `JsonNode` return types will need updates
- Any consumers of the JSON output will need to parse strings instead of using Jackson JsonNode

## Phase 4: Testing Strategy

### Unit Test Updates Required

1. **Change assertions**: From `JsonNode` operations to JSON string parsing
2. **Validate structure**: Ensure generated JSON matches expected schema
3. **Preserve CLI tests**: Verify `asCliOutput()` remains unchanged
4. **Add validation tests**: Test OpenAPI model validation features

### Test Categories

- **Conversion accuracy**: Verify data fidelity in conversions
- **Edge cases**: Handle null values, missing fields, different cluster types
- **Schema compliance**: Ensure JSON output matches OpenAPI specifications
- **CLI preservation**: Confirm human-readable output unchanged

## Implementation Guidelines

### Code Organization

```
MetadataMigration/src/main/java/org/opensearch/migrations/cli/
├── openapi/
│   ├── OpenApiConverter.java        # Existing (Items)
│   ├── ClustersConverter.java       # New (Clusters)
│   ├── TransformersConverter.java   # Future
│   └── ...
├── Clusters.java                    # Updated
├── Items.java                       # Future update
└── ...
```

### Naming Conventions

- **Converter classes**: `[ClassName]Converter.java`
- **Main conversion method**: `[className]ToOpenApiJson()`
- **Field mapping methods**: `[sourceType]To[TargetType]()`

### Error Handling

- Use existing logging patterns (`@Slf4j`)
- Graceful fallback to original JSON for conversion errors
- Preserve existing error behavior in CLI methods

## Dependencies

### Required Dependencies

- OpenAPI generated models (already present in `build/generated/openapi/`)
- Gson library (used by generated models)
- Existing Jackson dependencies (may be removed in future phases)

### Generated Model Usage

- Import from `org.opensearch.migration.model.*`
- Use `.toJson()` method for serialization
- Leverage built-in validation where appropriate

## Rollback Strategy

If issues arise during implementation:

1. **Revert interface changes**: Restore `JsonOutput` to return `JsonNode`
2. **Keep converter classes**: They can be useful for future attempts
3. **Restore original methods**: Use git to revert individual `asJsonOutput()` methods
4. **Incremental rollback**: Can revert class by class if needed

## Success Criteria

- [ ] All existing unit tests pass with minimal changes
- [ ] CLI output remains unchanged for all classes
- [ ] JSON output matches OpenAPI schema specifications
- [ ] Generated models are used for all JSON serialization
- [ ] Code follows established patterns and conventions
- [ ] Documentation is updated to reflect new approach

## Future Considerations

### Potential Enhancements

1. **Remove Jackson dependency**: Once all classes use Gson
2. **Enhanced validation**: Leverage OpenAPI model validation features
3. **Schema versioning**: Handle API evolution gracefully
4. **Performance improvements**: Benchmark Gson vs Jackson performance

### Maintenance

- **Generated model updates**: Process for handling regenerated models
- **Breaking changes**: Strategy for handling OpenAPI schema changes
- **Documentation**: Keep this plan updated as implementation evolves

---

*This document should be updated as implementation progresses and new requirements or challenges are discovered.*
