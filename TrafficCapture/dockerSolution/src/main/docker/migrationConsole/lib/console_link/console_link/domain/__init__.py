"""Domain layer for the migration assistant.

This package contains:
- entities: Core business objects with identity
- value_objects: Immutable objects without identity
- exceptions: Domain-specific exceptions
"""

# Re-export commonly used items for convenience
from .entities import *
from .value_objects import *
from .exceptions import *
