"""Domain exceptions for Kafka operations."""

from console_link.domain.exceptions.common_errors import MigrationAssistantError


class KafkaError(MigrationAssistantError):
    """Base exception for Kafka-related errors."""
    pass


class KafkaTopicCreationError(KafkaError):
    """Exception raised when creating a Kafka topic fails."""
    pass


class KafkaTopicDeletionError(KafkaError):
    """Exception raised when deleting a Kafka topic fails."""
    pass


class KafkaDescribeError(KafkaError):
    """Exception raised when describing Kafka resources fails."""
    pass
