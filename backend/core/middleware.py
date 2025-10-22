"""
Global error handling middleware for FastAPI
"""
import uuid
import time
from typing import Callable
from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from core.error_handling import error_handler, ErrorCode
from core.audit_logging import AuditLogger, AuditAction, AuditSeverity
from core.app_logging import logger as app_logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.audit_logger = AuditLogger()
        self.logger = app_logger
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', None)
        
        try:
            response = await call_next(request)
            
            # Log successful requests (optional - can be disabled in production)
            if self.logger.isEnabledFor(20):  # DEBUG level
                process_time = time.time() - start_time
                self.logger.debug(
                    f"Request completed: {request.method} {request.url.path} "
                    f"- Status: {response.status_code} - Time: {process_time:.3f}s"
                )
            
            return response
            
        except RequestValidationError as exc:
            return error_handler.handle_exception(exc, request)
            
        except StarletteHTTPException as exc:
            return error_handler.handle_exception(exc, request)
            
        except Exception as exc:
            # Log unexpected errors
            self.logger.error(f"Unhandled exception in {request.method} {request.url.path}: {exc}")
            
            return error_handler.handle_exception(exc, request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Add HSTS header for HTTPS (only in production)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Basic rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # In production, use Redis or similar
        self.audit_logger = AuditLogger()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        self.requests = {
            ip: timestamps for ip, timestamps in self.requests.items()
            if any(ts > current_time - 60 for ts in timestamps)
        }
        
        # Check rate limit
        if client_ip in self.requests:
            recent_requests = [ts for ts in self.requests[client_ip] if ts > current_time - 60]
            if len(recent_requests) >= self.requests_per_minute:
                # Log rate limit violation
                self.audit_logger.log_event(
                    action=AuditAction.SECURITY_VIOLATION,
                    ip_address=client_ip,
                    user_agent=request.headers.get("user-agent"),
                    request_id=getattr(request.state, 'request_id', None),
                    description="Rate limit exceeded",
                    success=False,
                    error_message=f"Rate limit exceeded: {len(recent_requests)} requests in 60 seconds",
                    severity=AuditSeverity.MEDIUM
                )
                
                from fastapi import HTTPException, status
                from core.error_handling import create_secure_http_exception, ErrorCode
                
                raise create_secure_http_exception(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    message="Rate limit exceeded. Please try again later.",
                    error_code=ErrorCode.SYSTEM_RATE_LIMIT_EXCEEDED
                )
        
        # Add current request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)
        
        return await call_next(request)
