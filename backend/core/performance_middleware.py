"""
Performance Monitoring Middleware for FastAPI

Automatically tracks:
- Request/response timing
- Endpoint performance
- Slow requests
- Error rates
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.performance_monitoring import get_performance_metrics
from core.logging_service import set_request_context, clear_request_context
import uuid


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request performance

    Features:
    - Automatic request timing
    - Endpoint-specific metrics
    - Slow request detection
    - Request correlation ID
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.metrics = get_performance_metrics()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and track performance

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response from handler
        """
        # Generate request ID for correlation
        request_id = str(uuid.uuid4())

        # Set request context for logging
        set_request_context(
            request_id=request_id,
            ip_address=request.client.host if request.client else None
        )

        # Track timing
        start_time = time.time()
        error = False
        status_code = 200

        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code

            # Check if error status
            error = status_code >= 400

            return response

        except Exception as e:
            # Handle exceptions
            error = True
            status_code = 500
            raise

        finally:
            # Record metrics
            duration = time.time() - start_time
            endpoint = request.url.path
            method = request.method

            self.metrics.record_request(
                endpoint=endpoint,
                method=method,
                duration=duration,
                status_code=status_code,
                error=error
            )

            # Clear request context
            clear_request_context()


# Export middleware
__all__ = ['PerformanceMonitoringMiddleware']
