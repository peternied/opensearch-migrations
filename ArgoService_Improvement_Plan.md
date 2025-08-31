# ArgoService Improvement Plan

## Background

The current ArgoService implementation in the opensearch-migrations codebase has several issues with its input/output model. It returns CommandResult objects with untyped values, leading to type checking issues and making error handling more difficult. This document outlines a comprehensive plan to improve the ArgoService API by introducing proper domain models and typed results.

## Current Issues

1. **Generic CommandResult Usage**: The ArgoService methods return CommandResult objects with untyped values.
2. **Inconsistent Return Types**: Some methods return CommandResult with string values, others with dictionaries.
3. **Error Handling**: Error information is embedded in CommandResult.value, making specific error case handling difficult.
4. **Command Execution Leakage**: Implementation details of kubectl/argo commands leak into the API.
5. **Missing Domain Models**: No proper models for Argo workflow concepts, forcing consumers to work with raw dictionaries.

## Implementation Plan

### Phase 1: Define Core Domain Models

1. **Create Workflow Status Model**:
   ```python
   # Create in new file: console_link/models/argo_models.py
   from dataclasses import dataclass
   from datetime import datetime
   from typing import Dict, List, Optional, Any
   
   @dataclass
   class WorkflowStatus:
       name: str
       phase: str
       has_suspended_nodes: bool
       start_time: Optional[datetime] = None
       end_time: Optional[datetime] = None
       message: Optional[str] = None
       raw_data: Dict[str, Any] = None
       
       @classmethod
       def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStatus":
           """Parse raw workflow data into structured object"""
           status_dict = data.get("status", {})
           metadata = data.get("metadata", {})
           return cls(
               name=metadata.get("name", ""),
               phase=status_dict.get("phase", ""),
               has_suspended_nodes=cls._check_for_suspended_nodes(status_dict.get("nodes", {})),
               start_time=cls._parse_time(status_dict.get("startedAt")),
               end_time=cls._parse_time(status_dict.get("finishedAt")),
               message=status_dict.get("message", ""),
               raw_data=data
           )
           
       @staticmethod
       def _check_for_suspended_nodes(nodes: Dict[str, Any]) -> bool:
           """Check if any nodes are in a suspended state"""
           for node_id, node in nodes.items():
               if node.get("phase") == "Running" and node.get("type", "") == "Suspend":
                   return True
           return False
           
       @staticmethod
       def _parse_time(time_str: Optional[str]) -> Optional[datetime]:
           """Parse ISO time string to datetime"""
           if not time_str:
               return None
           try:
               return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
           except ValueError:
               return None
   ```

2. **Create Workflow Result Classes**:
   ```python
   # Add to console_link/models/argo_models.py
   from typing import Generic, TypeVar, Optional
   
   T = TypeVar('T')
   
   @dataclass
   class WorkflowResult(Generic[T]):
       """Typed result for workflow operations"""
       success: bool
       data: Optional[T] = None
       error: Optional[str] = None
       
       @classmethod
       def success_result(cls, data: T) -> "WorkflowResult[T]":
           return cls(success=True, data=data)
           
       @classmethod
       def error_result(cls, error: str) -> "WorkflowResult[T]":
           return cls(success=False, error=error)
   ```

3. **Create Command Execution Interface**:
   ```python
   # Create in new file: console_link/models/command_execution.py
   from abc import ABC, abstractmethod
   from dataclasses import dataclass
   from typing import List, Tuple, Optional
   import subprocess
   
   @dataclass
   class CommandOutput:
       success: bool
       stdout: str
       stderr: str
       return_code: int
   
   class CommandExecutor(ABC):
       @abstractmethod
       def execute_command(self, command: List[str]) -> CommandOutput:
           """Execute a command and return structured output"""
           pass
   
   class SubprocessCommandExecutor(CommandExecutor):
       def execute_command(self, command: List[str]) -> CommandOutput:
           try:
               result = subprocess.run(command, capture_output=True, text=True, check=True)
               return CommandOutput(
                   success=True,
                   stdout=result.stdout,
                   stderr=result.stderr,
                   return_code=result.returncode
               )
           except subprocess.CalledProcessError as e:
               return CommandOutput(
                   success=False,
                   stdout=e.stdout or "",
                   stderr=e.stderr or "",
                   return_code=e.returncode
               )
   ```

### Phase 2: Update ArgoService Implementation

1. **Create New ArgoService Implementation**:
   ```python
   # Create in new file: console_link/models/argo_service_v2.py
   import time
   import json
   import logging
   import tempfile
   import os
   import uuid
   import yaml
   from typing import Optional, Dict, Any, List
   
   from console_link.models.argo_models import WorkflowStatus, WorkflowResult
   from console_link.models.command_execution import CommandExecutor, SubprocessCommandExecutor
   from console_link.models.cluster import Cluster
   
   logger = logging.getLogger(__name__)
   
   ENDING_ARGO_PHASES = ["Succeeded", "Failed", "Error", "Stopped", "Terminated"]
   
   class ArgoServiceV2:
       def __init__(self, 
                   namespace: str = "ma", 
                   argo_image: str = "quay.io/argoproj/argocli:v3.6.5",
                   service_account: str = "argo-workflow-executor",
                   command_executor: Optional[CommandExecutor] = None):
           self.namespace = namespace
           self.argo_image = argo_image
           self.service_account = service_account
           self.command_executor = command_executor or SubprocessCommandExecutor()
       
       def start_workflow(self, workflow_template_name: str, 
                         parameters: Optional[Dict[str, Any]] = None, 
                         workflow_options: Optional[Dict[str, Any]] = None) -> WorkflowResult[str]:
           """Start an Argo workflow and return the workflow name"""
           try:
               # Create temporary workflow file
               temp_file = self._create_workflow_yaml(workflow_template_name, parameters, workflow_options)
               
               # Run kubectl create command
               cmd = [
                   "kubectl", "create", "-f", temp_file, 
                   "--namespace", self.namespace, 
                   "-o", "jsonpath={.metadata.name}"
               ]
               
               result = self.command_executor.execute_command(cmd)
               
               # Clean up temporary file
               try:
                   os.unlink(temp_file)
               except OSError:
                   logger.warning(f"Failed to delete temporary file: {temp_file}")
               
               if not result.success:
                   return WorkflowResult.error_result(f"Failed to start workflow: {result.stderr}")
               
               workflow_name = result.stdout.strip()
               logger.info(f"Started workflow: {workflow_name}")
               
               # Wait for workflow to exist
               exists_result = self._wait_for_workflow_exists(workflow_name)
               if not exists_result.success:
                   return WorkflowResult.error_result(exists_result.error or "Failed to verify workflow exists")
               
               return WorkflowResult.success_result(workflow_name)
               
           except Exception as e:
               logger.error(f"Failed to start workflow: {e}")
               return WorkflowResult.error_result(f"Failed to start workflow: {str(e)}")
       
       def get_workflow_status(self, workflow_name: str) -> WorkflowResult[WorkflowStatus]:
           """Get the current status of a workflow"""
           try:
               workflow_data = self._get_workflow_status_json(workflow_name)
               if not workflow_data:
                   return WorkflowResult.error_result(f"Failed to get workflow status data for {workflow_name}")
                   
               status = WorkflowStatus.from_dict(workflow_data)
               return WorkflowResult.success_result(status)
               
           except Exception as e:
               logger.error(f"Failed to get workflow status: {e}")
               return WorkflowResult.error_result(f"Failed to get workflow status: {str(e)}")
       
       # Add similar updated implementations for other methods...
       
       def _get_workflow_status_json(self, workflow_name: str) -> Optional[Dict[str, Any]]:
           """Get the raw JSON status of a workflow"""
           cmd = [
               "kubectl", "get", "workflow", workflow_name,
               "-o", "json", 
               "--namespace", self.namespace
           ]
           
           result = self.command_executor.execute_command(cmd)
           if not result.success:
               logger.error(f"Failed to get workflow json: {result.stderr}")
               return None
           
           try:
               return json.loads(result.stdout.strip())
           except json.JSONDecodeError as e:
               logger.error(f"Failed to parse workflow JSON: {e}")
               return None
       
       # Add other helper methods...
   ```

2. **Add Migration Utility**:
   ```python
   # Add to console_link/models/argo_service_v2.py
   
   def convert_command_result_to_workflow_result(cmd_result: CommandResult) -> WorkflowResult:
       """Utility to convert old CommandResult to new WorkflowResult for migration"""
       if cmd_result.success:
           return WorkflowResult.success_result(cmd_result.value)
       return WorkflowResult.error_result(str(cmd_result.value) if cmd_result.value else "Unknown error")
   ```

### Phase 3: Update ArgoRFSBackfill

1. **Create a New ArgoRFSBackfill Implementation**:
   ```python
   # Create in new file: console_link/models/backfill_rfs_v2.py
   
   class ArgoRFSBackfillV2(RFSBackfill):
       """
       Improved implementation of RFS backfill using Argo Workflows with the new API.
       """
       def __init__(self, config: Dict, snapshot: Optional[Snapshot], target_cluster: Cluster,
                    client_options: Optional[ClientOptions] = None) -> None:
           super().__init__(config)
           # Similar to original implementation but using ArgoServiceV2
           self.client_options = client_options
           self.target_cluster = target_cluster
           
           # Validate required parameters
           if snapshot is None:
               raise ValueError("A snapshot object is required for ArgoRFSBackfill")
           self.snapshot = snapshot
           
           # Extract Argo configuration
           self.argo_config = self.config["reindex_from_snapshot"]["argo"]
           self.namespace = self.argo_config.get("namespace", "ma")
           self.workflow_template_name = self.argo_config["workflow_template_name"]
           
           # Initialize parameters dictionary
           self.parameters = self._initialize_parameters()
           
           # Initialize the ArgoService
           self.argo_service = ArgoServiceV2(namespace=self.namespace)
           
           # Track the workflow name once started
           self.workflow_name = None
       
       def start(self, *args, **kwargs) -> CommandResult:
           """Start the Argo workflow for document bulk loading"""
           logger.info(f"Starting RFS backfill using Argo workflow template: {self.workflow_template_name}")
           
           # Get entrypoint from config or use default
           entrypoint = self.argo_config.get("entrypoint", "run-bulk-load")
           
           # Create workflow with the specified entrypoint
           workflow_options = {
               "entrypoint": entrypoint,
           }
           
           try:
               result = self.argo_service.start_workflow(
                   workflow_template_name=self.workflow_template_name,
                   parameters=self.parameters,
                   workflow_options=workflow_options
               )
               
               if result.success:
                   self.workflow_name = result.data
                   logger.info(f"Successfully started Argo workflow: {self.workflow_name}")
                   return CommandResult(True, f"Started RFS backfill workflow: {self.workflow_name}")
               else:
                   logger.error(f"Failed to start Argo workflow: {result.error}")
                   return CommandResult(False, f"Failed to start RFS backfill workflow: {result.error}")
           except Exception as e:
               logger.error(f"Exception while starting Argo workflow: {str(e)}", exc_info=True)
               return CommandResult(False, f"Exception while starting RFS backfill workflow: {str(e)}")
       
       # Implement other methods in a similar way...
   ```

### Phase 4: Testing and Validation

1. **Unit Tests for Domain Models**:
   ```python
   # Create in new file: tests/models/test_argo_models.py
   import unittest
   from datetime import datetime
   from console_link.models.argo_models import WorkflowStatus, WorkflowResult
   
   class TestWorkflowStatus(unittest.TestCase):
       def test_from_dict_with_valid_data(self):
           # Test parsing workflow data with all fields
           data = {
               "metadata": {"name": "test-workflow"},
               "status": {
                   "phase": "Running",
                   "startedAt": "2023-01-01T12:00:00Z",
                   "finishedAt": None,
                   "message": "Running workflow",
                   "nodes": {
                       "node1": {
                           "phase": "Running",
                           "type": "Suspend"
                       }
                   }
               }
           }
           status = WorkflowStatus.from_dict(data)
           self.assertEqual(status.name, "test-workflow")
           self.assertEqual(status.phase, "Running")
           self.assertTrue(status.has_suspended_nodes)
           self.assertEqual(status.start_time.year, 2023)
           self.assertIsNone(status.end_time)
           self.assertEqual(status.message, "Running workflow")
       
       def test_from_dict_with_minimal_data(self):
           # Test parsing minimal workflow data
           data = {
               "metadata": {},
               "status": {}
           }
           status = WorkflowStatus.from_dict(data)
           self.assertEqual(status.name, "")
           self.assertEqual(status.phase, "")
           self.assertFalse(status.has_suspended_nodes)
   
   # Add more tests for WorkflowResult and other models...
   ```

2. **Unit Tests for ArgoServiceV2**:
   ```python
   # Create in new file: tests/models/test_argo_service_v2.py
   import unittest
   from unittest.mock import Mock, patch
   from console_link.models.argo_service_v2 import ArgoServiceV2
   from console_link.models.command_execution import CommandOutput
   
   class TestArgoServiceV2(unittest.TestCase):
       def setUp(self):
           self.mock_executor = Mock()
           self.argo_service = ArgoServiceV2(namespace="test-namespace", command_executor=self.mock_executor)
       
       def test_get_workflow_status_success(self):
           # Setup mock response
           self.mock_executor.execute_command.return_value = CommandOutput(
               success=True,
               stdout='{"metadata":{"name":"test-workflow"},"status":{"phase":"Running"}}',
               stderr="",
               return_code=0
           )
           
           # Call method
           result = self.argo_service.get_workflow_status("test-workflow")
           
           # Verify
           self.assertTrue(result.success)
           self.assertEqual(result.data.name, "test-workflow")
           self.assertEqual(result.data.phase, "Running")
           self.assertFalse(result.data.has_suspended_nodes)
       
       def test_get_workflow_status_command_failure(self):
           # Setup mock response for command failure
           self.mock_executor.execute_command.return_value = CommandOutput(
               success=False,
               stdout="",
               stderr="Error: workflows.argoproj.io \"test-workflow\" not found",
               return_code=1
           )
           
           # Call method
           result = self.argo_service.get_workflow_status("test-workflow")
           
           # Verify
           self.assertFalse(result.success)
           self.assertIsNotNone(result.error)
           self.assertIn("Failed to get workflow status", result.error)
   
   # Add more tests for other methods...
   ```

### Phase 5: Integration and Migration Strategy

1. **Parallel Implementation Period**:
   - Add ArgoServiceV2 while keeping the original ArgoService
   - Add ArgoRFSBackfillV2 while keeping the original ArgoRFSBackfill
   - Initially route 10% of traffic to the new implementations for testing

2. **Migration Script**:
   Create a utility script to help with migration:
   ```python
   # In a new file: scripts/migrate_argo_service.py
   import os
   import re
   
   def find_imports(file_path):
       """Find import statements in a file"""
       with open(file_path, 'r') as f:
           content = f.read()
       
       # Find imports
       import_pattern = r'from console_link\.models\.argo_service import .*'
       imports = re.findall(import_pattern, content)
       return imports
   
   def find_files_using_argo_service():
       """Find all files using ArgoService"""
       result = []
       root_dir = 'console_link'
       for dirpath, _, filenames in os.walk(root_dir):
           for filename in filenames:
               if filename.endswith('.py'):
                   file_path = os.path.join(dirpath, filename)
                   with open(file_path, 'r') as f:
                       content = f.read()
                   if 'ArgoService' in content:
                       result.append(file_path)
       return result
   
   def main():
       """Main entry point"""
       files = find_files_using_argo_service()
       print(f"Found {len(files)} files using ArgoService:")
       for file in files:
           imports = find_imports(file)
           print(f"  - {file}: {imports}")
   
   if __name__ == "__main__":
       main()
   ```

3. **Feature Flag**:
   Add a feature flag to gradually roll out the new implementation:
   ```python
   # In console_link/environment.py
   USE_ARGO_SERVICE_V2 = os.environ.get('USE_ARGO_SERVICE_V2', 'false').lower() == 'true'
   
   # In console_link/models/factories.py
   def create_argo_service(namespace="ma"):
       if USE_ARGO_SERVICE_V2:
           from console_link.models.argo_service_v2 import ArgoServiceV2
           return ArgoServiceV2(namespace=namespace)
       else:
           from console_link.models.argo_service import ArgoService
           return ArgoService(namespace=namespace)
   ```

### Phase 6: Documentation

1. **API Documentation**:
   Create comprehensive API documentation for the new models:
   ```markdown
   # ArgoService V2 API Documentation
   
   ## Overview
   
   The ArgoService V2 API provides a typed interface for interacting with Argo Workflows. It returns 
   structured data objects rather than generic command results, making it easier to work with workflow 
   status and other information.
   
   ## Core Classes
   
   ### WorkflowStatus
   
   Represents the status of an Argo workflow.
   
   ```python
   WorkflowStatus(
       name: str,           # Name of the workflow
       phase: str,          # Current phase (Running, Succeeded, Failed, etc.)
       has_suspended_nodes: bool,  # Whether any nodes are suspended
       start_time: Optional[datetime] = None,  # When the workflow started
       end_time: Optional[datetime] = None,    # When the workflow completed
       message: Optional[str] = None,          # Status message
       raw_data: Dict[str, Any] = None         # Raw workflow data
   )
   ```
   
   ### WorkflowResult[T]
   
   Typed result container for workflow operations.
   
   ```python
   WorkflowResult(
       success: bool,           # Whether the operation succeeded
       data: Optional[T] = None,  # Result data if successful
       error: Optional[str] = None  # Error message if failed
   )
   ```
   
   ## ArgoServiceV2 Methods
   
   ### start_workflow
   
   ```python
   def start_workflow(
       workflow_template_name: str, 
       parameters: Optional[Dict[str, Any]] = None, 
       workflow_options: Optional[Dict[str, Any]] = None
   ) -> WorkflowResult[str]
   ```
   
   Starts a workflow based on a template. Returns the workflow name on success.
   
   ### get_workflow_status
   
   ```python
   def get_workflow_status(workflow_name: str) -> WorkflowResult[WorkflowStatus]
   ```
   
   Gets the current status of a workflow.
   ```
   
2. **Migration Guide**:
   Create a guide for migrating from old to new API:
   ```markdown
   # Migrating to ArgoServiceV2
   
   This guide explains how to migrate from the old ArgoService API to the new ArgoServiceV2 API.
   
   ## Major Changes
   
   1. Typed results instead of generic CommandResult
   2. Structured workflow status object instead of raw dictionaries
   3. Better error handling
   
   ## Step-by-Step Migration
   
   ### 1. Update Import Statements
   
   ```python
   # Old
   from console_link.models.argo_service import ArgoService
   
   # New
   from console_link.models.argo_service_v2 import ArgoServiceV2
   ```
   
   ### 2. Update Method Calls
   
   ```python
   # Old
   status_result = argo_service.get_workflow_status(workflow_name)
   if status_result.success:
       status_info = status_result.value
       phase = status_info.get("phase", "")
   
   # New
   status_result = argo_service.get_workflow_status(workflow_name)
   if status_result.success:
       workflow_status = status_result.data
       phase = workflow_status.phase
   ```
   
   ### 3. Handling Errors
   
   ```python
   # Old
   if not status_result.success:
       logger.error(f"Failed to get workflow status: {status_result.value}")
   
   # New
   if not status_result.success:
       logger.error(f"Failed to get workflow status: {status_result.error}")
   ```
   ```

## Timeline and Milestones

1. **Week 1: Planning and Design**
   - Finalize design for domain models
   - Review and get approval for the overall approach

2. **Week 2: Core Implementation**
   - Implement domain models
   - Implement ArgoServiceV2 with new API

3. **Week 3: Testing and Updates**
   - Write unit tests for new models and service
   - Create ArgoRFSBackfillV2 implementation

4. **Week 4: Integration**
   - Add feature flag for gradual rollout
   - Update documentation

5. **Weeks 5-6: Migration**
   - Help teams migrate to new API
   - Monitor and fix any issues
   - Complete migration and remove old implementations

## Future Considerations

1. **Command Execution Abstraction**:
   Consider further abstracting the command execution layer to support other execution models beyond subprocess.

2. **Error Typing**:
   Implement specific error types for different failure scenarios (e.g., WorkflowNotFoundError, AuthorizationError).

3. **Metrics and Monitoring**:
   Add support for collecting metrics on workflow execution and performance.

4. **Integration with Workflow DB**:
   Consider integrating with a workflow database for persistent storage of workflow information.
