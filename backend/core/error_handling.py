"""
Comprehensive error handling system for secure error management
"""
import logging
import traceback
from typing import Any, Dict, Optional, Union
from enum import Enum
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
from core.audit_logging import AuditLogger, AuditAction, AuditSeverity
from core.app_logging import logger as app_logger


class ErrorCode(str, Enum):
    """Standardized error codes for consistent error handling"""
    # Authentication errors
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_INSUFFICIENT_PERMISSIONS"
    AUTH_ACCOUNT_INACTIVE = "AUTH_ACCOUNT_INACTIVE"
    
    # Validation errors
    VALIDATION_INVALID_INPUT = "VALIDATION_INVALID_INPUT"
    VALIDATION_MISSING_FIELD = "VALIDATION_MISSING_FIELD"
    VALIDATION_INVALID_FORMAT = "VALIDATION_INVALID_FORMAT"
    VALIDATION_CONSTRAINT_VIOLATION = "VALIDATION_CONSTRAINT_VIOLATION"
    
    # Resource errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    RESOURCE_LOCKED = "RESOURCE_LOCKED"
    
    # Business logic errors
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    BUSINESS_INVALID_STATE = "BUSINESS_INVALID_STATE"
    BUSINESS_OPERATION_NOT_ALLOWED = "BUSINESS_OPERATION_NOT_ALLOWED"
    
    # System errors
    SYSTEM_INTERNAL_ERROR = "SYSTEM_INTERNAL_ERROR"
    SYSTEM_DATABASE_ERROR = "SYSTEM_DATABASE_ERROR"
    SYSTEM_EXTERNAL_SERVICE_ERROR = "SYSTEM_EXTERNAL_SERVICE_ERROR"
    SYSTEM_RATE_LIMIT_EXCEEDED = "SYSTEM_RATE_LIMIT_EXCEEDED"
    
    # Security errors
    SECURITY_SUSPICIOUS_ACTIVITY = "SECURITY_SUSPICIOUS_ACTIVITY"
    SECURITY_INVALID_REQUEST = "SECURITY_INVALID_REQUEST"
    SECURITY_CSRF_TOKEN_INVALID = "SECURITY_CSRF_TOKEN_INVALID"


class SecurityError(Exception):
    """Custom exception for security-related errors"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.SECURITY_SUSPICIOUS_ACTIVITY):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class BusinessLogicError(Exception):
    """Custom exception for business logic violations"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.BUSINESS_RULE_VIOLATION):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ErrorResponse:
    """Standardized error response format"""
    
    @staticmethod
    def create_error_response(
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized error response
        
        Args:
            error_code: Standardized error code
            message: User-friendly error message
            details: Additional error details (sanitized)
            status_code: HTTP status code
            request_id: Request identifier for tracking
            
        Returns:
            Dict containing standardized error response
        """
        response = {
            "error": {
                "code": error_code.value,
                "message": message,
                "timestamp": "2024-01-01T00:00:00Z",  # Will be set by middleware
                "request_id": request_id
            }
        }
        
        # Add details if provided (sanitized)
        if details:
            response["error"]["details"] = ErrorResponse._sanitize_details(details)
            
        return response
    
    @staticmethod
    def _sanitize_details(details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize error details to prevent information leakage
        
        Args:
            details: Raw error details
            
        Returns:
            Sanitized error details
        """
        sanitized = {}
        
        # Fields that are safe to include
        safe_fields = {
            'field', 'field_name', 'constraint', 'expected_type', 
            'provided_type', 'min_length', 'max_length', 'pattern'
        }
        
        # Fields that should be excluded or masked
        sensitive_fields = {
            'password', 'token', 'secret', 'key', 'credential',
            'sql', 'query', 'stack_trace', 'traceback', 'exception'
        }
        
        for key, value in details.items():
            key_lower = key.lower()
            
            # Skip sensitive fields
            if any(sensitive in key_lower for sensitive in sensitive_fields):
                sanitized[key] = "[REDACTED]"
            # Include safe fields
            elif key_lower in safe_fields:
                sanitized[key] = str(value)
            # Mask other fields
            else:
                sanitized[key] = "[MASKED]"
                
        return sanitized


class ErrorHandler:
    """Centralized error handling service"""
    
    def __init__(self):
        self.audit_logger = AuditLogger()
        self.logger = app_logger
    
    def handle_exception(
        self,
        exc: Exception,
        request: Request,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None
    ) -> JSONResponse:
        """
        Handle exceptions and return appropriate error responses
        
        Args:
            exc: The exception to handle
            request: FastAPI request object
            user_id: Current user ID (if authenticated)
            user_email: Current user email (if authenticated)
            user_role: Current user role (if authenticated)
            
        Returns:
            JSONResponse with appropriate error details
        """
        # Get request context
        request_id = getattr(request.state, 'request_id', None)
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Determine error type and response
        if isinstance(exc, HTTPException):
            return self._handle_http_exception(exc, request_id, client_ip, user_agent)
        elif isinstance(exc, RequestValidationError):
            return self._handle_validation_error(exc, request_id, client_ip, user_agent)
        elif isinstance(exc, SecurityError):
            return self._handle_security_error(exc, request_id, client_ip, user_agent, user_id, user_email, user_role)
        elif isinstance(exc, BusinessLogicError):
            return self._handle_business_error(exc, request_id, client_ip, user_agent, user_id, user_email, user_role)
        elif isinstance(exc, SQLAlchemyError):
            return self._handle_database_error(exc, request_id, client_ip, user_agent, user_id, user_email, user_role)
        else:
            return self._handle_unexpected_error(exc, request_id, client_ip, user_agent, user_id, user_email, user_role)
    
    def _handle_http_exception(
        self,
        exc: HTTPException,
        request_id: Optional[str],
        client_ip: Optional[str],
        user_agent: Optional[str]
    ) -> JSONResponse:
        """Handle HTTP exceptions"""
        error_code = self._map_http_status_to_error_code(exc.status_code)
        
        response_data = ErrorResponse.create_error_response(
            error_code=error_code,
            message=str(exc.detail),
            status_code=exc.status_code,
            request_id=request_id
        )
        
        # Log the error
        self.logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response_data,
            headers=exc.headers
        )
    
    def _handle_validation_error(
        self,
        exc: RequestValidationError,
        request_id: Optional[str],
        client_ip: Optional[str],
        user_agent: Optional[str]
    ) -> JSONResponse:
        """Handle validation errors"""
        # Extract validation details
        validation_details = []
        print(f"!!! VALIDATION ERROR !!!")
        print(f"Errors: {exc.errors()}")
        for error in exc.errors():
            print(f"  - Field: {error['loc']}, Message: {error['msg']}, Type: {error['type']}")
            validation_details.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        response_data = ErrorResponse.create_error_response(
            error_code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="Invalid input data provided",
            details={"validation_errors": validation_details},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            request_id=request_id
        )
        
        # Log validation error
        self.logger.warning(f"Validation Error: {validation_details}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response_data
        )
    
    def _handle_security_error(
        self,
        exc: SecurityError,
        request_id: Optional[str],
        client_ip: Optional[str],
        user_agent: Optional[str],
        user_id: Optional[int],
        user_email: Optional[str],
        user_role: Optional[str]
    ) -> JSONResponse:
        """Handle security-related errors"""
        response_data = ErrorResponse.create_error_response(
            error_code=exc.error_code,
            message="Security violation detected",
            status_code=status.HTTP_403_FORBIDDEN,
            request_id=request_id
        )
        
        # Log security violation
        self.audit_logger.log_event(
            action=AuditAction.SECURITY_VIOLATION,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            ip_address=client_ip,
            user_agent=user_agent,
            request_id=request_id,
            description=f"Security error: {exc.message}",
            success=False,
            error_message=exc.message,
            severity=AuditSeverity.HIGH
        )
        
        self.logger.error(f"Security Error: {exc.message}")
        
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=response_data
        )
    
    def _handle_business_error(
        self,
        exc: BusinessLogicError,
        request_id: Optional[str],
        client_ip: Optional[str],
        user_agent: Optional[str],
        user_id: Optional[int],
        user_email: Optional[str],
        user_role: Optional[str]
    ) -> JSONResponse:
        """Handle business logic errors"""
        response_data = ErrorResponse.create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            status_code=status.HTTP_400_BAD_REQUEST,
            request_id=request_id
        )
        
        # Log business logic error
        self.audit_logger.log_event(
            action=AuditAction.SYSTEM_ERROR,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            ip_address=client_ip,
            user_agent=user_agent,
            request_id=request_id,
            description=f"Business logic error: {exc.message}",
            success=False,
            error_message=exc.message,
            severity=AuditSeverity.MEDIUM
        )
        
        self.logger.warning(f"Business Logic Error: {exc.message}")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=response_data
        )
    
    def _handle_database_error(
        self,
        exc: SQLAlchemyError,
        request_id: Optional[str],
        client_ip: Optional[str],
        user_agent: Optional[str],
        user_id: Optional[int],
        user_email: Optional[str],
        user_role: Optional[str]
    ) -> JSONResponse:
        """Handle database errors"""
        # Determine error type
        if isinstance(exc, IntegrityError):
            error_code = ErrorCode.RESOURCE_CONFLICT
            message = "Data integrity violation"
            status_code = status.HTTP_409_CONFLICT
        else:
            error_code = ErrorCode.SYSTEM_DATABASE_ERROR
            message = "Database operation failed"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        response_data = ErrorResponse.create_error_response(
            error_code=error_code,
            message=message,
            status_code=status_code,
            request_id=request_id
        )
        
        # Log database error
        self.audit_logger.log_event(
            action=AuditAction.SYSTEM_ERROR,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            ip_address=client_ip,
            user_agent=user_agent,
            request_id=request_id,
            description=f"Database error: {type(exc).__name__}",
            success=False,
            error_message=str(exc),
            severity=AuditSeverity.HIGH
        )
        
        self.logger.error(f"Database Error: {exc}")
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    def _handle_unexpected_error(
        self,
        exc: Exception,
        request_id: Optional[str],
        client_ip: Optional[str],
        user_agent: Optional[str],
        user_id: Optional[int],
        user_email: Optional[str],
        user_role: Optional[str]
    ) -> JSONResponse:
        """Handle unexpected errors"""
        response_data = ErrorResponse.create_error_response(
            error_code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            message="An unexpected error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request_id
        )
        
        # Log unexpected error
        self.audit_logger.log_event(
            action=AuditAction.SYSTEM_ERROR,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            ip_address=client_ip,
            user_agent=user_agent,
            request_id=request_id,
            description=f"Unexpected error: {type(exc).__name__}",
            success=False,
            error_message=str(exc),
            severity=AuditSeverity.CRITICAL
        )
        
        # Log full traceback for debugging
        self.logger.error(f"Unexpected Error: {exc}\n{traceback.format_exc()}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_data
        )
    
    def _map_http_status_to_error_code(self, status_code: int) -> ErrorCode:
        """Map HTTP status codes to error codes"""
        mapping = {
            400: ErrorCode.VALIDATION_INVALID_INPUT,
            401: ErrorCode.AUTH_INVALID_CREDENTIALS,
            403: ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            404: ErrorCode.RESOURCE_NOT_FOUND,
            409: ErrorCode.RESOURCE_CONFLICT,
            422: ErrorCode.VALIDATION_INVALID_INPUT,
            429: ErrorCode.SYSTEM_RATE_LIMIT_EXCEEDED,
            500: ErrorCode.SYSTEM_INTERNAL_ERROR,
            502: ErrorCode.SYSTEM_EXTERNAL_SERVICE_ERROR,
            503: ErrorCode.SYSTEM_EXTERNAL_SERVICE_ERROR,
        }
        return mapping.get(status_code, ErrorCode.SYSTEM_INTERNAL_ERROR)


# Global error handler instance
error_handler = ErrorHandler()


def create_secure_http_exception(
    status_code: int,
    message: str,
    error_code: Optional[ErrorCode] = None,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """
    Create a secure HTTP exception with standardized error format
    
    Args:
        status_code: HTTP status code
        message: User-friendly error message
        error_code: Standardized error code
        details: Additional error details
        
    Returns:
        HTTPException with secure error details
    """
    if error_code is None:
        error_code = error_handler._map_http_status_to_error_code(status_code)
    
    error_response = ErrorResponse.create_error_response(
        error_code=error_code,
        message=message,
        details=details,
        status_code=status_code
    )
    
    return HTTPException(
        status_code=status_code,
        detail=error_response["error"]
    )


def raise_security_error(message: str, error_code: ErrorCode = ErrorCode.SECURITY_SUSPICIOUS_ACTIVITY) -> None:
    """Raise a security error"""
    raise SecurityError(message, error_code)


def raise_business_error(message: str, error_code: ErrorCode = ErrorCode.BUSINESS_RULE_VIOLATION) -> None:
    """Raise a business logic error"""
    raise BusinessLogicError(message, error_code)
