"""Metrics collection infrastructure for monitoring and observability."""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from console_link.domain.exceptions.common_errors import InfrastructureError

logger = logging.getLogger(__name__)


class MetricStatistic(Enum):
    """Types of metric statistics."""
    AVERAGE = "Average"
    SUM = "Sum"
    MINIMUM = "Minimum"
    MAXIMUM = "Maximum"
    SAMPLE_COUNT = "SampleCount"


class MetricComponent(Enum):
    """Components that emit metrics."""
    CAPTURE_PROXY = "captureProxy"
    REPLAYER = "replayer"
    BACKFILL = "backfill"
    MIGRATION_ASSISTANT = "migration-assistant"


@dataclass
class MetricData:
    """A single metric data point."""
    timestamp: datetime
    value: float
    unit: Optional[str] = None


@dataclass
class MetricDefinition:
    """Definition of a metric."""
    name: str
    namespace: str
    component: MetricComponent
    dimensions: Dict[str, str]
    unit: Optional[str] = None
    description: Optional[str] = None


@dataclass
class MetricQuery:
    """Query parameters for retrieving metrics."""
    metric_name: str
    component: MetricComponent
    statistic: MetricStatistic
    start_time: datetime
    end_time: datetime
    period_seconds: int = 60
    dimensions: Optional[Dict[str, str]] = None


class MetricsError(InfrastructureError):
    """Raised when metrics operations fail."""
    pass


class MetricsCollectorInterface(ABC):
    """Abstract interface for metrics collection."""
    
    @abstractmethod
    def list_metrics(self, component: Optional[MetricComponent] = None) -> List[MetricDefinition]:
        """List available metrics."""
        pass
    
    @abstractmethod
    def get_metric_data(self, query: MetricQuery) -> List[MetricData]:
        """Get metric data for a specific query."""
        pass
    
    @abstractmethod
    def put_metric_data(self, metric: MetricDefinition, value: float, timestamp: Optional[datetime] = None):
        """Put a metric data point."""
        pass


class CloudWatchMetricsCollector(MetricsCollectorInterface):
    """Collect metrics using AWS CloudWatch."""
    
    NAMESPACE = "Migration-Assistant"
    
    def __init__(self, region: Optional[str] = None, qualifier: Optional[str] = None,
                 client_options: Optional[Dict[str, Any]] = None):
        """Initialize CloudWatch metrics collector.
        
        Args:
            region: AWS region
            qualifier: Optional qualifier for metric names
            client_options: Additional boto3 client options
        """
        try:
            from console_link.models.utils import create_boto3_client
            
            self.client = create_boto3_client(
                aws_service_name="cloudwatch",
                region=region,
                client_options=client_options
            )
            self.qualifier = qualifier
            self.region = region
            logger.info(f"Initialized CloudWatch metrics collector for region: {region or 'default'}")
            
        except ImportError:
            raise MetricsError("boto3 not installed. Install with: pip install boto3")
        except Exception as e:
            raise MetricsError(f"Failed to initialize CloudWatch client: {e}")
    
    def list_metrics(self, component: Optional[MetricComponent] = None) -> List[MetricDefinition]:
        """List available metrics in CloudWatch.
        
        Args:
            component: Optional component filter
            
        Returns:
            List of MetricDefinition objects
            
        Raises:
            MetricsError: If listing fails
        """
        try:
            dimensions = []
            if component:
                dimensions.append({
                    'Name': 'Component',
                    'Value': component.value
                })
            
            paginator = self.client.get_paginator('list_metrics')
            page_iterator = paginator.paginate(
                Namespace=self.NAMESPACE,
                Dimensions=dimensions
            )
            
            metrics = []
            for page in page_iterator:
                for metric in page.get('Metrics', []):
                    # Extract component from dimensions
                    metric_component = None
                    dimensions_dict = {}
                    for dim in metric.get('Dimensions', []):
                        dimensions_dict[dim['Name']] = dim['Value']
                        if dim['Name'] == 'Component':
                            try:
                                metric_component = MetricComponent(dim['Value'])
                            except ValueError:
                                logger.warning(f"Unknown component: {dim['Value']}")
                    
                    if metric_component:
                        metrics.append(MetricDefinition(
                            name=metric['MetricName'],
                            namespace=metric['Namespace'],
                            component=metric_component,
                            dimensions=dimensions_dict
                        ))
            
            return metrics
            
        except Exception as e:
            raise MetricsError(f"Failed to list metrics: {e}")
    
    def get_metric_data(self, query: MetricQuery) -> List[MetricData]:
        """Get metric data from CloudWatch.
        
        Args:
            query: MetricQuery object
            
        Returns:
            List of MetricData points
            
        Raises:
            MetricsError: If query fails
        """
        try:
            dimensions = [
                {'Name': 'Component', 'Value': query.component.value}
            ]
            
            if query.dimensions:
                for name, value in query.dimensions.items():
                    dimensions.append({'Name': name, 'Value': value})
            
            response = self.client.get_metric_statistics(
                Namespace=self.NAMESPACE,
                MetricName=query.metric_name,
                Dimensions=dimensions,
                StartTime=query.start_time,
                EndTime=query.end_time,
                Period=query.period_seconds,
                Statistics=[query.statistic.value]
            )
            
            data_points = []
            for point in response.get('Datapoints', []):
                data_points.append(MetricData(
                    timestamp=point['Timestamp'],
                    value=point[query.statistic.value],
                    unit=point.get('Unit')
                ))
            
            # Sort by timestamp
            data_points.sort(key=lambda x: x.timestamp)
            
            return data_points
            
        except Exception as e:
            raise MetricsError(f"Failed to get metric data: {e}")
    
    def put_metric_data(self, metric: MetricDefinition, value: float, timestamp: Optional[datetime] = None):
        """Put metric data to CloudWatch.
        
        Args:
            metric: MetricDefinition
            value: Metric value
            timestamp: Optional timestamp (defaults to now)
            
        Raises:
            MetricsError: If put fails
        """
        try:
            dimensions = [
                {'Name': 'Component', 'Value': metric.component.value}
            ]
            
            for name, val in metric.dimensions.items():
                if name != 'Component':
                    dimensions.append({'Name': name, 'Value': val})
            
            metric_data = {
                'MetricName': metric.name,
                'Dimensions': dimensions,
                'Value': value,
                'Timestamp': timestamp or datetime.utcnow()
            }
            
            if metric.unit:
                metric_data['Unit'] = metric.unit
            
            self.client.put_metric_data(
                Namespace=self.NAMESPACE,
                MetricData=[metric_data]
            )
            
        except Exception as e:
            raise MetricsError(f"Failed to put metric data: {e}")


class PrometheusMetricsCollector(MetricsCollectorInterface):
    """Collect metrics using Prometheus."""
    
    COMPONENT_JOB_MAPPING = {
        MetricComponent.CAPTURE_PROXY: "capture-proxy",
        MetricComponent.REPLAYER: "traffic-replayer",
        MetricComponent.BACKFILL: "backfill",
        MetricComponent.MIGRATION_ASSISTANT: "migration-assistant"
    }
    
    def __init__(self, endpoint: str, auth: Optional[Any] = None):
        """Initialize Prometheus metrics collector.
        
        Args:
            endpoint: Prometheus endpoint URL
            auth: Optional authentication
        """
        try:
            from console_link.infrastructure.http_client import HttpClient
            
            self.endpoint = endpoint.rstrip('/')
            self.http_client = HttpClient(auth=auth)
            logger.info(f"Initialized Prometheus metrics collector for endpoint: {endpoint}")
            
        except ImportError:
            raise MetricsError("HTTP client dependencies not available")
    
    def list_metrics(self, component: Optional[MetricComponent] = None) -> List[MetricDefinition]:
        """List available metrics in Prometheus.
        
        Args:
            component: Optional component filter
            
        Returns:
            List of MetricDefinition objects
            
        Raises:
            MetricsError: If listing fails
        """
        try:
            # Get all metric names
            response = self.http_client.get(
                f"{self.endpoint}/api/v1/label/__name__/values"
            )
            
            if not response.is_success:
                raise MetricsError(f"Failed to list metrics: HTTP {response.status_code}")
            
            metric_names = response.json.get('data', [])
            metrics = []
            
            # For each component, query its metrics
            for comp in MetricComponent:
                if component and comp != component:
                    continue
                
                job_name = self.COMPONENT_JOB_MAPPING.get(comp)
                if not job_name:
                    continue
                
                # Query metrics for this job
                query = f'{{exported_job="{job_name}"}}'
                response = self.http_client.get(
                    f"{self.endpoint}/api/v1/query",
                    params={'query': query}
                )
                
                if response.is_success:
                    data = response.json.get('data', {})
                    for result in data.get('result', []):
                        metric_name = result.get('metric', {}).get('__name__', '')
                        if metric_name in metric_names:
                            metrics.append(MetricDefinition(
                                name=metric_name,
                                namespace="prometheus",
                                component=comp,
                                dimensions={'exported_job': job_name}
                            ))
            
            return metrics
            
        except Exception as e:
            raise MetricsError(f"Failed to list metrics: {e}")
    
    def get_metric_data(self, query: MetricQuery) -> List[MetricData]:
        """Get metric data from Prometheus.
        
        Args:
            query: MetricQuery object
            
        Returns:
            List of MetricData points
            
        Raises:
            MetricsError: If query fails
        """
        try:
            job_name = self.COMPONENT_JOB_MAPPING.get(query.component)
            if not job_name:
                raise MetricsError(f"Unknown component: {query.component}")
            
            # Build PromQL query
            promql = f'{query.metric_name}{{exported_job="{job_name}"}}'
            
            # Add additional dimensions if provided
            if query.dimensions:
                for name, value in query.dimensions.items():
                    if name != 'exported_job':
                        promql = promql.replace('}', f',{name}="{value}"}}')
            
            # Query range data
            response = self.http_client.get(
                f"{self.endpoint}/api/v1/query_range",
                params={
                    'query': promql,
                    'start': int(query.start_time.timestamp()),
                    'end': int(query.end_time.timestamp()),
                    'step': query.period_seconds
                }
            )
            
            if not response.is_success:
                raise MetricsError(f"Failed to query metrics: HTTP {response.status_code}")
            
            data_points = []
            data = response.json.get('data', {})
            
            for result in data.get('result', []):
                for timestamp, value in result.get('values', []):
                    data_points.append(MetricData(
                        timestamp=datetime.fromtimestamp(timestamp),
                        value=float(value)
                    ))
            
            return data_points
            
        except Exception as e:
            raise MetricsError(f"Failed to get metric data: {e}")
    
    def put_metric_data(self, metric: MetricDefinition, value: float, timestamp: Optional[datetime] = None):
        """Put metric data to Prometheus.
        
        Note: Prometheus typically uses a pull model, so this would need to be
        implemented via pushgateway or by exposing metrics for scraping.
        
        Raises:
            NotImplementedError: Prometheus uses pull model
        """
        raise NotImplementedError("Prometheus uses a pull model. Use pushgateway or expose metrics endpoint.")


class MockMetricsCollector(MetricsCollectorInterface):
    """Mock metrics collector for testing."""
    
    def __init__(self):
        self.metrics: List[MetricDefinition] = []
        self.data_points: Dict[str, List[MetricData]] = {}
        self.put_calls: List[Dict[str, Any]] = []
        
        # Add some default metrics
        for component in MetricComponent:
            self.metrics.extend([
                MetricDefinition(
                    name=f"{component.value}_requests_total",
                    namespace="test",
                    component=component,
                    dimensions={"environment": "test"}
                ),
                MetricDefinition(
                    name=f"{component.value}_errors_total",
                    namespace="test",
                    component=component,
                    dimensions={"environment": "test"}
                )
            ])
    
    def list_metrics(self, component: Optional[MetricComponent] = None) -> List[MetricDefinition]:
        """List mock metrics."""
        if component:
            return [m for m in self.metrics if m.component == component]
        return self.metrics.copy()
    
    def get_metric_data(self, query: MetricQuery) -> List[MetricData]:
        """Get mock metric data."""
        key = f"{query.component.value}:{query.metric_name}"
        
        # Generate mock data if not exists
        if key not in self.data_points:
            data = []
            current = query.start_time
            value = 100.0
            
            while current <= query.end_time:
                data.append(MetricData(
                    timestamp=current,
                    value=value,
                    unit="Count"
                ))
                value += 10  # Mock increasing values
                current += timedelta(seconds=query.period_seconds)
            
            self.data_points[key] = data
        
        return self.data_points[key]
    
    def put_metric_data(self, metric: MetricDefinition, value: float, timestamp: Optional[datetime] = None):
        """Record put metric call."""
        self.put_calls.append({
            "metric": metric,
            "value": value,
            "timestamp": timestamp or datetime.utcnow()
        })
        
        # Store the data point
        key = f"{metric.component.value}:{metric.name}"
        if key not in self.data_points:
            self.data_points[key] = []
        
        self.data_points[key].append(MetricData(
            timestamp=timestamp or datetime.utcnow(),
            value=value,
            unit=metric.unit
        ))
