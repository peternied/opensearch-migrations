"""Pydantic schemas for cluster API endpoints."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum

from console_link.domain.entities.cluster_entity import ClusterStatus, ClusterType
from console_link.domain.value_objects.auth_config import AuthMethod


class CreateClusterRequest(BaseModel):
    """Request schema for creating a cluster configuration."""
    name: str = Field(..., description="Cluster name")
    endpoint: str = Field(..., description="Cluster endpoint URL")
    auth_method: AuthMethod = Field(..., description="Authentication method")
    auth_config: Dict[str, Any] = Field(default_factory=dict, description="Authentication configuration")
    verify_ssl: bool = Field(True, description="Whether to verify SSL certificates")
    
    class Config:
        extra = 'forbid'
    
    @validator('endpoint')
    def validate_endpoint(cls, v):
        """Validate endpoint format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Endpoint must start with http:// or https://')
        return v.rstrip('/')


class ClusterResponse(BaseModel):
    """Response schema for cluster operations."""
    id: str = Field(..., description="Unique identifier for the cluster")
    name: str = Field(..., description="Cluster name")
    endpoint: str = Field(..., description="Cluster endpoint URL")
    cluster_type: ClusterType = Field(..., description="Type of cluster")
    version: Optional[str] = Field(None, description="Cluster version")
    state: ClusterStatus = Field(..., description="Current state of the cluster")
    auth_method: AuthMethod = Field(..., description="Authentication method")
    verify_ssl: bool = Field(..., description="Whether SSL verification is enabled")
    node_count: Optional[int] = Field(None, description="Number of nodes in the cluster")
    health: Optional[str] = Field(None, description="Cluster health status")
    
    class Config:
        orm_mode = True
        from_attributes = True
    
    @classmethod
    def from_entity(cls, entity) -> "ClusterResponse":
        """Create response from domain entity."""
        return cls(
            id=entity.id,
            name=entity.name,
            endpoint=entity.endpoint,
            cluster_type=entity.cluster_type,
            version=entity.version,
            state=entity.state,
            auth_method=entity.auth_config.auth_method,
            verify_ssl=entity.auth_config.verify_ssl,
            node_count=entity.node_count,
            health=entity.health
        )


class ClusterHealthResponse(BaseModel):
    """Response schema for cluster health status."""
    cluster_name: str = Field(..., description="Name of the cluster")
    status: str = Field(..., description="Health status (green, yellow, red)")
    number_of_nodes: int = Field(..., description="Number of nodes")
    number_of_data_nodes: int = Field(..., description="Number of data nodes")
    active_primary_shards: int = Field(..., description="Number of active primary shards")
    active_shards: int = Field(..., description="Total number of active shards")
    relocating_shards: int = Field(..., description="Number of relocating shards")
    initializing_shards: int = Field(..., description="Number of initializing shards")
    unassigned_shards: int = Field(..., description="Number of unassigned shards")
    delayed_unassigned_shards: int = Field(..., description="Number of delayed unassigned shards")
    number_of_pending_tasks: int = Field(..., description="Number of pending tasks")
    number_of_in_flight_fetch: int = Field(..., description="Number of in-flight fetch operations")
    task_max_waiting_in_queue_millis: int = Field(..., description="Maximum wait time in queue")
    active_shards_percent_as_number: float = Field(..., description="Percentage of active shards")
    
    class Config:
        orm_mode = True
        from_attributes = True


class ClusterStatsResponse(BaseModel):
    """Response schema for cluster statistics."""
    indices: Dict[str, Any] = Field(..., description="Index statistics")
    nodes: Dict[str, Any] = Field(..., description="Node statistics")
    
    class Config:
        orm_mode = True
        from_attributes = True


class ClusterListResponse(BaseModel):
    """Response schema for listing clusters."""
    clusters: List[ClusterResponse] = Field(..., description="List of clusters")
    total: int = Field(..., description="Total number of clusters")
    
    class Config:
        orm_mode = True
        from_attributes = True


class UpdateClusterRequest(BaseModel):
    """Request schema for updating a cluster configuration."""
    endpoint: Optional[str] = Field(None, description="Cluster endpoint URL")
    auth_method: Optional[AuthMethod] = Field(None, description="Authentication method")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    verify_ssl: Optional[bool] = Field(None, description="Whether to verify SSL certificates")
    
    class Config:
        extra = 'forbid'
    
    @validator('endpoint')
    def validate_endpoint(cls, v):
        """Validate endpoint format if provided."""
        if v is not None:
            if not v.startswith(('http://', 'https://')):
                raise ValueError('Endpoint must start with http:// or https://')
            return v.rstrip('/')
        return v


class ClusterConnectionTestRequest(BaseModel):
    """Request schema for testing cluster connection."""
    endpoint: str = Field(..., description="Cluster endpoint URL")
    auth_method: AuthMethod = Field(..., description="Authentication method")
    auth_config: Dict[str, Any] = Field(default_factory=dict, description="Authentication configuration")
    verify_ssl: bool = Field(True, description="Whether to verify SSL certificates")
    
    class Config:
        extra = 'forbid'


class ClusterConnectionTestResponse(BaseModel):
    """Response schema for cluster connection test."""
    success: bool = Field(..., description="Whether the connection was successful")
    cluster_name: Optional[str] = Field(None, description="Name of the cluster if connected")
    version: Optional[str] = Field(None, description="Version of the cluster if connected")
    error: Optional[str] = Field(None, description="Error message if connection failed")
    
    class Config:
        orm_mode = True
        from_attributes = True
