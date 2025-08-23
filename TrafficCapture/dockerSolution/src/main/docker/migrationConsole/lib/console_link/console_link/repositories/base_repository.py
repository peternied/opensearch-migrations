"""Base repository interface for data access layer.

This module defines the abstract base class that all repositories should inherit from.
It provides a standard interface for CRUD operations and common data access patterns.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any

# Generic type for entity
T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Abstract base class for all repositories.
    
    This class defines the standard interface for repository operations.
    All concrete repository implementations should inherit from this class
    and implement the abstract methods.
    """

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Retrieve an entity by its ID.
        
        Args:
            entity_id: The unique identifier of the entity
            
        Returns:
            The entity if found, None otherwise
            
        Raises:
            ExternalServiceError: If there's an issue with the data store
        """
        pass

    @abstractmethod
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """Retrieve all entities with optional pagination.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities
            
        Raises:
            ExternalServiceError: If there's an issue with the data store
        """
        pass

    @abstractmethod
    def save(self, entity: T) -> T:
        """Save or update an entity.
        
        If the entity already exists, it will be updated.
        If it doesn't exist, it will be created.
        
        Args:
            entity: The entity to save
            
        Returns:
            The saved entity (may include generated fields like ID)
            
        Raises:
            ValidationError: If the entity is invalid
            ExternalServiceError: If there's an issue with the data store
        """
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete an entity by its ID.
        
        Args:
            entity_id: The unique identifier of the entity to delete
            
        Returns:
            True if the entity was deleted, False if it didn't exist
            
        Raises:
            ExternalServiceError: If there's an issue with the data store
        """
        pass

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Check if an entity exists.
        
        Args:
            entity_id: The unique identifier of the entity
            
        Returns:
            True if the entity exists, False otherwise
            
        Raises:
            ExternalServiceError: If there's an issue with the data store
        """
        pass

    def find_by(self, **criteria: Any) -> List[T]:
        """Find entities matching the given criteria.
        
        This is an optional method that repositories can override
        to provide custom search functionality.
        
        Args:
            **criteria: Key-value pairs of search criteria
            
        Returns:
            List of entities matching the criteria
            
        Raises:
            NotImplementedError: If the repository doesn't support this operation
            ExternalServiceError: If there's an issue with the data store
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not implement find_by")

    def count(self, **criteria: Any) -> int:
        """Count entities matching the given criteria.
        
        This is an optional method that repositories can override
        to provide counting functionality.
        
        Args:
            **criteria: Key-value pairs of search criteria
            
        Returns:
            Number of entities matching the criteria
            
        Raises:
            NotImplementedError: If the repository doesn't support this operation
            ExternalServiceError: If there's an issue with the data store
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not implement count")

    def bulk_save(self, entities: List[T]) -> List[T]:
        """Save multiple entities in a single operation.
        
        This is an optional method that repositories can override
        for better performance when saving multiple entities.
        
        Args:
            entities: List of entities to save
            
        Returns:
            List of saved entities
            
        Raises:
            NotImplementedError: If the repository doesn't support bulk operations
            ValidationError: If any entity is invalid
            ExternalServiceError: If there's an issue with the data store
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not implement bulk_save")

    def bulk_delete(self, entity_ids: List[str]) -> int:
        """Delete multiple entities in a single operation.
        
        This is an optional method that repositories can override
        for better performance when deleting multiple entities.
        
        Args:
            entity_ids: List of entity IDs to delete
            
        Returns:
            Number of entities deleted
            
        Raises:
            NotImplementedError: If the repository doesn't support bulk operations
            ExternalServiceError: If there's an issue with the data store
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not implement bulk_delete")


class TransactionalRepository(BaseRepository[T]):
    """Extended base repository with transaction support.
    
    This abstract class extends BaseRepository to add transaction
    management capabilities for repositories that need ACID guarantees.
    """

    @abstractmethod
    def begin_transaction(self) -> Any:
        """Begin a new transaction.
        
        Returns:
            Transaction context object
            
        Raises:
            ExternalServiceError: If transaction cannot be started
        """
        pass

    @abstractmethod
    def commit_transaction(self, transaction: Any) -> None:
        """Commit a transaction.
        
        Args:
            transaction: The transaction context to commit
            
        Raises:
            ExternalServiceError: If commit fails
        """
        pass

    @abstractmethod
    def rollback_transaction(self, transaction: Any) -> None:
        """Rollback a transaction.
        
        Args:
            transaction: The transaction context to rollback
            
        Raises:
            ExternalServiceError: If rollback fails
        """
        pass
