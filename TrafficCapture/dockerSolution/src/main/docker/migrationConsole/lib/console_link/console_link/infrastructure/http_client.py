"""HTTP client infrastructure for external API calls."""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass

from console_link.domain.exceptions.common_errors import InfrastructureError, ExternalServiceError

logger = logging.getLogger(__name__)


class HttpMethod(Enum):
    """HTTP request methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"


@dataclass
class HttpResponse:
    """HTTP response wrapper."""
    status_code: int
    headers: Dict[str, str]
    body: Union[str, bytes, Dict[str, Any]]
    url: str
    elapsed_seconds: float

    @property
    def is_success(self) -> bool:
        """Check if response indicates success."""
        return 200 <= self.status_code < 300

    @property
    def json(self) -> Dict[str, Any]:
        """Get JSON body if applicable."""
        if isinstance(self.body, dict):
            return self.body
        raise ValueError("Response body is not JSON")


class HttpError(InfrastructureError):
    """Raised when HTTP operations fail."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[HttpResponse] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class HttpClientInterface(ABC):
    """Abstract interface for HTTP client operations."""
    
    @abstractmethod
    def request(self, method: HttpMethod, url: str, 
                headers: Optional[Dict[str, str]] = None,
                params: Optional[Dict[str, Any]] = None,
                json_data: Optional[Dict[str, Any]] = None,
                data: Optional[Union[str, bytes]] = None,
                timeout: Optional[float] = None,
                verify_ssl: bool = True,
                **kwargs) -> HttpResponse:
        """Make an HTTP request."""
        pass
    
    @abstractmethod
    def get(self, url: str, **kwargs) -> HttpResponse:
        """Make a GET request."""
        pass
    
    @abstractmethod
    def post(self, url: str, **kwargs) -> HttpResponse:
        """Make a POST request."""
        pass
    
    @abstractmethod
    def put(self, url: str, **kwargs) -> HttpResponse:
        """Make a PUT request."""
        pass
    
    @abstractmethod
    def delete(self, url: str, **kwargs) -> HttpResponse:
        """Make a DELETE request."""
        pass


class HttpClient(HttpClientInterface):
    """HTTP client using requests library."""
    
    def __init__(self, default_timeout: float = 30.0, 
                 default_headers: Optional[Dict[str, str]] = None,
                 auth: Optional[Any] = None,
                 verify_ssl: bool = True):
        """Initialize HTTP client.
        
        Args:
            default_timeout: Default timeout for requests
            default_headers: Headers to include in all requests
            auth: Authentication handler
            verify_ssl: Whether to verify SSL certificates
        """
        try:
            import requests
            import urllib3
            
            # Disable SSL warnings if not verifying
            if not verify_ssl:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            self.session = requests.Session()
            self.default_timeout = default_timeout
            self.verify_ssl = verify_ssl
            
            if default_headers:
                self.session.headers.update(default_headers)
            
            if auth:
                self.session.auth = auth
                
        except ImportError:
            raise HttpError("requests library not installed. Install with: pip install requests")
    
    def request(self, method: HttpMethod, url: str,
                headers: Optional[Dict[str, str]] = None,
                params: Optional[Dict[str, Any]] = None,
                json_data: Optional[Dict[str, Any]] = None,
                data: Optional[Union[str, bytes]] = None,
                timeout: Optional[float] = None,
                verify_ssl: Optional[bool] = None,
                **kwargs) -> HttpResponse:
        """Make an HTTP request.
        
        Args:
            method: HTTP method
            url: URL to request
            headers: Additional headers
            params: Query parameters
            json_data: JSON body
            data: Raw body data
            timeout: Request timeout
            verify_ssl: Whether to verify SSL (overrides default)
            **kwargs: Additional request parameters
            
        Returns:
            HttpResponse object
            
        Raises:
            HttpError: If request fails
        """
        import time
        
        if verify_ssl is None:
            verify_ssl = self.verify_ssl
            
        start_time = time.time()
        
        try:
            response = self.session.request(
                method=method.value,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                data=data,
                timeout=timeout or self.default_timeout,
                verify=verify_ssl,
                **kwargs
            )
            
            elapsed = time.time() - start_time
            
            # Parse response body
            body: Union[str, bytes, Dict[str, Any]]
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    body = response.json()
                except ValueError:
                    body = response.text
            else:
                body = response.content if response.headers.get('content-type', '').startswith('application/octet-stream') else response.text
            
            http_response = HttpResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=body,
                url=response.url,
                elapsed_seconds=elapsed
            )
            
            # Raise for HTTP errors if configured
            if not http_response.is_success:
                raise HttpError(
                    f"HTTP {response.status_code}: {response.reason}",
                    status_code=response.status_code,
                    response=http_response
                )
            
            return http_response
            
        except Exception as e:
            if isinstance(e, HttpError):
                raise
            raise HttpError(f"Request failed: {e}")
    
    def get(self, url: str, **kwargs) -> HttpResponse:
        """Make a GET request."""
        return self.request(HttpMethod.GET, url, **kwargs)
    
    def post(self, url: str, **kwargs) -> HttpResponse:
        """Make a POST request."""
        return self.request(HttpMethod.POST, url, **kwargs)
    
    def put(self, url: str, **kwargs) -> HttpResponse:
        """Make a PUT request."""
        return self.request(HttpMethod.PUT, url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> HttpResponse:
        """Make a DELETE request."""
        return self.request(HttpMethod.DELETE, url, **kwargs)
    
    def close(self):
        """Close the HTTP session."""
        if hasattr(self, 'session'):
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class SigV4HttpClient(HttpClient):
    """HTTP client with AWS SigV4 authentication."""
    
    def __init__(self, service: str, region: str, **kwargs):
        """Initialize SigV4 authenticated HTTP client.
        
        Args:
            service: AWS service name (e.g., 'es', 'ecs')
            region: AWS region
            **kwargs: Additional HttpClient parameters
        """
        try:
            from console_link.models.utils import SigV4AuthPlugin
            auth = SigV4AuthPlugin(service, region)
            super().__init__(auth=auth, **kwargs)
        except ImportError:
            raise HttpError("boto3 not installed for SigV4 auth. Install with: pip install boto3")


class MockHttpClient(HttpClientInterface):
    """Mock HTTP client for testing."""
    
    def __init__(self):
        self.requests: list[Dict[str, Any]] = []
        self.responses: list[HttpResponse] = []
        self.response_index = 0
    
    def add_response(self, response: HttpResponse):
        """Add a mock response."""
        self.responses.append(response)
    
    def request(self, method: HttpMethod, url: str, **kwargs) -> HttpResponse:
        """Record request and return mock response."""
        self.requests.append({
            "method": method,
            "url": url,
            **kwargs
        })
        
        if self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
            return response
        
        # Default response
        return HttpResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            body={"status": "ok"},
            url=url,
            elapsed_seconds=0.1
        )
    
    def get(self, url: str, **kwargs) -> HttpResponse:
        """Make a GET request."""
        return self.request(HttpMethod.GET, url, **kwargs)
    
    def post(self, url: str, **kwargs) -> HttpResponse:
        """Make a POST request."""
        return self.request(HttpMethod.POST, url, **kwargs)
    
    def put(self, url: str, **kwargs) -> HttpResponse:
        """Make a PUT request."""
        return self.request(HttpMethod.PUT, url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> HttpResponse:
        """Make a DELETE request."""
        return self.request(HttpMethod.DELETE, url, **kwargs)
