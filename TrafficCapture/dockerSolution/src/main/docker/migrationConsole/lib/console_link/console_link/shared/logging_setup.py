"""Centralized logging configuration for console_link.

This module provides a unified logging setup that can be used across
all components of the application.
"""

import logging
import logging.handlers
import sys
from typing import Optional, Dict, Any
from pathlib import Path
import json


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
    json_format: bool = False,
    **kwargs
) -> None:
    """Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
        log_file: Optional file path to write logs to
        json_format: If True, use JSON formatting for logs
        **kwargs: Additional keyword arguments for handlers
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Set up the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        if format_string is None:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if requested
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=kwargs.get('max_bytes', 10_485_760),  # 10MB default
            backupCount=kwargs.get('backup_count', 5)
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels if provided
    logger_levels = kwargs.get('logger_levels', {})
    for logger_name, logger_level in logger_levels.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, logger_level.upper(), logging.INFO))


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.
        
        Args:
            record: The log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_obj = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'created', 'filename',
                          'funcName', 'levelname', 'levelno', 'lineno',
                          'module', 'msecs', 'message', 'pathname', 'process',
                          'processName', 'relativeCreated', 'thread',
                          'threadName', 'exc_info', 'exc_text', 'stack_info'):
                log_obj[key] = value
        
        return json.dumps(log_obj)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.
    
    Args:
        name: The name of the logger (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def configure_module_logger(
    module_name: str,
    level: Optional[str] = None,
    propagate: bool = True
) -> logging.Logger:
    """Configure a specific module's logger.
    
    Args:
        module_name: Name of the module
        level: Optional specific level for this module
        propagate: Whether to propagate to parent loggers
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(module_name)
    
    if level:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    logger.propagate = propagate
    
    return logger


# Convenience function for structured logging
def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **context: Any
) -> None:
    """Log a message with additional context fields.
    
    Args:
        logger: Logger instance to use
        level: Log level (debug, info, warning, error, critical)
        message: The log message
        **context: Additional context fields to include
    """
    log_method = getattr(logger, level.lower())
    log_method(message, extra=context)
