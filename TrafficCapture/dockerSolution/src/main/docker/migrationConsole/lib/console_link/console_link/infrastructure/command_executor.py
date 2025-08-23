"""Command execution infrastructure for running system commands."""
import subprocess
import os
import logging
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from console_link.domain.exceptions.common_errors import InfrastructureError

logger = logging.getLogger(__name__)

# Sentinel value for flag-only arguments
FlagOnlyArgument = object()


class OutputMode(Enum):
    """Output handling modes for command execution."""
    QUIET = "quiet"
    CAPTURE = "capture"
    STREAM = "stream"
    DETACHED = "detached"


@dataclass
class CommandResult:
    """Result of a command execution."""
    stdout: Optional[str]
    stderr: Optional[str]
    returncode: int
    pid: Optional[int] = None  # For detached processes

    @property
    def success(self) -> bool:
        """Check if command executed successfully."""
        return self.returncode == 0


class CommandExecutionError(InfrastructureError):
    """Raised when command execution fails."""
    
    def __init__(self, returncode: int, command: List[str], stdout: Optional[str] = None, 
                 stderr: Optional[str] = None):
        self.returncode = returncode
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        
        message = f"Command [{' '.join(command)}] failed with exit code {returncode}"
        if stderr:
            message += f"\nError: {stderr.strip()}"
        super().__init__(message)


class CommandExecutorInterface(ABC):
    """Abstract interface for command execution."""
    
    @abstractmethod
    def execute(self, command: List[str], mode: OutputMode = OutputMode.CAPTURE,
                print_output: bool = False, log_file: Optional[str] = None) -> CommandResult:
        """Execute a command with specified output mode."""
        pass


class CommandExecutor(CommandExecutorInterface):
    """Execute system commands with various output handling modes."""
    
    def __init__(self, sensitive_fields: Optional[List[str]] = None):
        """Initialize command executor.
        
        Args:
            sensitive_fields: List of field names whose values should be masked in logs
        """
        self.sensitive_fields = sensitive_fields or []
    
    def build_command(self, command_root: str, command_args: Dict[str, Any]) -> List[str]:
        """Build command array from root and arguments.
        
        Args:
            command_root: Base command to execute
            command_args: Dictionary of command arguments
            
        Returns:
            List of command parts
        """
        command = [command_root]
        for key, value in command_args.items():
            command.append(key)
            if value is not FlagOnlyArgument:
                if not isinstance(value, str):
                    value = str(value)
                command.append(value)
        return command
    
    def sanitize_command(self, command: List[str]) -> List[str]:
        """Sanitize command for logging by masking sensitive fields.
        
        Args:
            command: Command to sanitize
            
        Returns:
            Sanitized command with sensitive values masked
        """
        if not self.sensitive_fields:
            return command
            
        display_command = command.copy()
        for i, part in enumerate(display_command):
            if part in self.sensitive_fields and i + 1 < len(display_command):
                # Mask the value following a sensitive field flag
                display_command[i + 1] = "********"
        
        return display_command
    
    def execute(self, command: Union[str, List[str]], mode: OutputMode = OutputMode.CAPTURE,
                print_output: bool = False, log_file: Optional[str] = None,
                command_args: Optional[Dict[str, Any]] = None) -> CommandResult:
        """Execute a command with specified output mode.
        
        Args:
            command: Command to execute (string or list)
            mode: Output handling mode
            print_output: Whether to print output to console
            log_file: Log file path for detached mode
            command_args: Optional command arguments (if command is string)
            
        Returns:
            CommandResult with execution details
            
        Raises:
            CommandExecutionError: If command fails
            ValueError: If invalid arguments provided
        """
        # Build command if needed
        if isinstance(command, str) and command_args:
            command = self.build_command(command, command_args)
        elif isinstance(command, str):
            command = [command]
        
        sanitized = self.sanitize_command(command)
        logger.debug(f"Executing command: {' '.join(sanitized)}")
        
        if mode == OutputMode.DETACHED:
            if not log_file:
                raise ValueError("log_file must be provided for detached mode")
            return self._execute_detached(command, log_file)
        elif mode == OutputMode.STREAM:
            return self._execute_streaming(command, print_output)
        else:  # CAPTURE or QUIET
            return self._execute_capture(command, print_output, mode == OutputMode.QUIET)
    
    def _execute_capture(self, command: List[str], print_output: bool, quiet: bool) -> CommandResult:
        """Execute command and capture output."""
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False  # Don't raise on non-zero exit
            )
            
            # Handle output logging/printing
            if result.stdout and not quiet:
                if print_output:
                    sys.stdout.write(result.stdout)
                logger.debug(f"STDOUT: {result.stdout}")
            
            if result.stderr and not quiet:
                if print_output and result.returncode != 0:
                    sys.stderr.write(result.stderr)
                log_level = logging.ERROR if result.returncode != 0 else logging.DEBUG
                logger.log(log_level, f"STDERR: {result.stderr}")
            
            # Check for failure
            if result.returncode != 0:
                raise CommandExecutionError(
                    result.returncode,
                    self.sanitize_command(command),
                    result.stdout,
                    result.stderr
                )
            
            return CommandResult(
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode
            )
            
        except subprocess.SubprocessError as e:
            raise CommandExecutionError(-1, self.sanitize_command(command), None, str(e))
    
    def _execute_streaming(self, command: List[str], print_output: bool) -> CommandResult:
        """Execute command with streaming output."""
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            output_lines = []
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        if print_output:
                            sys.stdout.write(line)
                            sys.stdout.flush()
                        output_lines.append(line)
                        logger.debug(f"STDOUT: {line.rstrip()}")
            
            returncode = process.wait()
            
            if returncode != 0:
                raise CommandExecutionError(
                    returncode,
                    self.sanitize_command(command),
                    ''.join(output_lines),
                    None
                )
            
            return CommandResult(
                stdout=''.join(output_lines),
                stderr=None,
                returncode=returncode
            )
            
        except Exception as e:
            if isinstance(e, CommandExecutionError):
                raise
            raise CommandExecutionError(-1, self.sanitize_command(command), None, str(e))
    
    def _execute_detached(self, command: List[str], log_file: str) -> CommandResult:
        """Execute command in detached mode."""
        try:
            with open(log_file, "w") as f:
                process = subprocess.Popen(
                    command,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setpgrp  # Detach from parent process group
                )
                
                logger.info(f"Process started with PID {process.pid}")
                logger.info(f"Process logs available at {log_file}")
                
                return CommandResult(
                    stdout=f"Process started with PID {process.pid}\nLogs: {log_file}",
                    stderr=None,
                    returncode=0,
                    pid=process.pid
                )
                
        except Exception as e:
            raise CommandExecutionError(-1, self.sanitize_command(command), None, str(e))


class MockCommandExecutor(CommandExecutorInterface):
    """Mock command executor for testing."""
    
    def __init__(self):
        self.executed_commands: List[List[str]] = []
        self.mock_results: Dict[str, CommandResult] = {}
    
    def set_mock_result(self, command_pattern: str, result: CommandResult):
        """Set mock result for commands matching pattern."""
        self.mock_results[command_pattern] = result
    
    def execute(self, command: List[str], mode: OutputMode = OutputMode.CAPTURE,
                print_output: bool = False, log_file: Optional[str] = None) -> CommandResult:
        """Execute mock command."""
        self.executed_commands.append(command)
        
        # Find matching mock result
        command_str = ' '.join(command)
        for pattern, result in self.mock_results.items():
            if pattern in command_str:
                if result.returncode != 0:
                    raise CommandExecutionError(
                        result.returncode,
                        command,
                        result.stdout,
                        result.stderr
                    )
                return result
        
        # Default success result
        return CommandResult(
            stdout="Mock execution successful",
            stderr=None,
            returncode=0
        )
