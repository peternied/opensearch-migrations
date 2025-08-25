"""Kafka service for handling Kafka operations.

This service handles Kafka topic and consumer group operations,
raising exceptions on errors instead of returning CommandResult objects.
"""

import logging
from typing import Dict, Any
from console_link.models.kafka import Kafka
from console_link.domain.exceptions.kafka_errors import (
    KafkaTopicCreationError,
    KafkaTopicDeletionError,
    KafkaDescribeError
)

logger = logging.getLogger(__name__)


class KafkaService:
    """Service for handling Kafka operations."""
    
    def __init__(self, kafka: Kafka):
        """Initialize the Kafka service.
        
        Args:
            kafka: The Kafka model instance
        """
        self.kafka = kafka
    
    def create_topic(self, topic_name: str = 'logging-traffic-topic') -> str:
        """Create a Kafka topic.
        
        Args:
            topic_name: Name of the topic to create
            
        Returns:
            Success message
            
        Raises:
            KafkaTopicCreationError: If topic creation fails
        """
        try:
            result = self.kafka.create_topic(topic_name)
            if not result.success:
                raise KafkaTopicCreationError(f"Failed to create topic: {result.value}")
            return str(result.value)
        except Exception as e:
            logger.error(f"Failed to create Kafka topic: {e}")
            raise KafkaTopicCreationError(f"Topic creation failed: {str(e)}")
    
    def delete_topic(self, topic_name: str = 'logging-traffic-topic') -> str:
        """Delete a Kafka topic.
        
        Args:
            topic_name: Name of the topic to delete
            
        Returns:
            Success message
            
        Raises:
            KafkaTopicDeletionError: If topic deletion fails
        """
        try:
            result = self.kafka.delete_topic(topic_name)
            if not result.success:
                raise KafkaTopicDeletionError(f"Failed to delete topic: {result.value}")
            return str(result.value)
        except Exception as e:
            logger.error(f"Failed to delete Kafka topic: {e}")
            raise KafkaTopicDeletionError(f"Topic deletion failed: {str(e)}")
    
    def describe_consumer_group(self, group_name: str = 'logging-group-default') -> Dict[str, Any]:
        """Describe a Kafka consumer group.
        
        Args:
            group_name: Name of the consumer group to describe
            
        Returns:
            Consumer group information
            
        Raises:
            KafkaDescribeError: If describing consumer group fails
        """
        try:
            result = self.kafka.describe_consumer_group(group_name)
            if not result.success:
                raise KafkaDescribeError(f"Failed to describe consumer group: {result.value}")
            
            # Parse the result into a structured format
            return self._parse_consumer_group_output(str(result.value))
        except Exception as e:
            logger.error(f"Failed to describe consumer group: {e}")
            raise KafkaDescribeError(f"Describe consumer group failed: {str(e)}")
    
    def describe_topic_records(self, topic_name: str = 'logging-traffic-topic') -> Dict[str, Any]:
        """Describe records in a Kafka topic.
        
        Args:
            topic_name: Name of the topic to describe
            
        Returns:
            Topic record information
            
        Raises:
            KafkaDescribeError: If describing topic records fails
        """
        try:
            result = self.kafka.describe_topic_records(topic_name)
            if not result.success:
                raise KafkaDescribeError(f"Failed to describe topic records: {result.value}")
            
            # Parse the result into a structured format
            return self._parse_topic_records_output(str(result.value))
        except Exception as e:
            logger.error(f"Failed to describe topic records: {e}")
            raise KafkaDescribeError(f"Describe topic records failed: {str(e)}")
    
    def _parse_consumer_group_output(self, output: str) -> Dict[str, Any]:
        """Parse consumer group output into structured format.
        
        Args:
            output: Raw output from Kafka command
            
        Returns:
            Parsed consumer group information
        """
        # For now, return raw output
        # In the future, this should parse the output into a structured format
        return {
            "raw_output": output,
            "group_details": {}
        }
    
    def _parse_topic_records_output(self, output: str) -> Dict[str, Any]:
        """Parse topic records output into structured format.
        
        Args:
            output: Raw output from Kafka command
            
        Returns:
            Parsed topic record information
        """
        # For now, return raw output
        # In the future, this should parse the output into a structured format
        return {
            "raw_output": output,
            "record_details": {}
        }
