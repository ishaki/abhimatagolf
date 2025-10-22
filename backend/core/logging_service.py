"""
Centralized Logging Service for Abhimata Golf

Provides unified logging interface with security best practices including:
- Automatic sensitive data redaction
- Multiple log types (app, audit, security, performance, error)
- Request correlation across all logs
- Context management (user, IP, session)
- Cross-platform log rotation
- Structured and text logging
"""

import logging
import os
from typing import Optional, Dict, Any
from enum import Enum
from contextvars import ContextVar

from core.config import settings
from core.log_formatters import JSONFormatter, TextFormatter, CompactTextFormatter
from core.log_handlers import (
    get_rotating_handler,
    create_handler_for_log_type,
    DirectoryBasedHandler,
    RedactingFormatter
)
from core.log_security import (
    SecureLogHandler,
    get_log_encryption,
    get_log_tamper_detection
)


# Context variables for request correlation
_request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
_user_id: ContextVar[Optional[int]] = ContextVar('user_id', default=None)
_user_email: ContextVar[Optional[str]] = ContextVar('user_email', default=None)
_ip_address: ContextVar[Optional[str]] = ContextVar('ip_address', default=None)
_session_id: ContextVar[Optional[str]] = ContextVar('session_id', default=None)


class LogType(str, Enum):
    """Types of logs in the system"""
    APP = "app"
    AUDIT = "audit"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ERROR = "error"


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class CentralizedLoggingService:
    """
    Centralized logging service with security best practices

    Features:
    - Multiple log types (app, audit, security, performance, error)
    - Automatic PII/sensitive data redaction
    - Structured logging (JSON + traditional text)
    - Request correlation across all logs
    - Context management (user, IP, session)
    - Cross-platform log rotation
    """

    def __init__(
        self,
        base_dir: str = "logs",
        use_json: bool = False,
        enable_redaction: bool = True,
        enable_console: bool = True
    ):
        """
        Initialize centralized logging service

        Args:
            base_dir: Base directory for all log files
            use_json: Use JSON format for structured logging
            enable_redaction: Enable automatic sensitive data redaction
            enable_console: Also log to console
        """
        self.base_dir = base_dir
        self.use_json = use_json
        self.enable_redaction = enable_redaction
        self.enable_console = enable_console
        self.loggers: Dict[str, logging.Logger] = {}

        # Create base log directory
        os.makedirs(base_dir, exist_ok=True)

        # Initialize loggers for each type
        self._initialize_loggers()

    def _initialize_loggers(self):
        """Initialize loggers for different log types"""
        for log_type in LogType:
            logger = self._create_logger(log_type.value)
            self.loggers[log_type.value] = logger

    def _create_logger(self, log_type: str) -> logging.Logger:
        """
        Create logger for specific log type

        Args:
            log_type: Type of log (app, audit, security, performance, error)

        Returns:
            Configured logger instance
        """
        logger_name = f"abhimata.{log_type}"
        logger = logging.getLogger(logger_name)

        # Prevent duplicate handlers if logger already exists
        if logger.handlers:
            return logger

        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        logger.propagate = False  # Don't propagate to root logger

        # Create formatter
        if self.use_json:
            formatter = JSONFormatter()
        else:
            # Use redacting formatter wrapper if enabled
            if self.enable_redaction:
                formatter = RedactingFormatter(
                    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    enabled=True
                )
            else:
                formatter = logging.Formatter(
                    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )

        # Create file handler for this log type
        file_handler = create_handler_for_log_type(
            log_type=log_type,
            base_dir=self.base_dir,
            formatter=formatter
        )

        # Wrap with security features if enabled for this log type
        enable_encryption = (
            settings.log_encryption_enabled and
            log_type in settings.encrypted_log_types
        )
        enable_signatures = (
            settings.log_tamper_detection_enabled and
            log_type in settings.signed_log_types
        )

        if enable_encryption or enable_signatures:
            # Get security components
            encryption = get_log_encryption() if enable_encryption else None
            tamper_detection = get_log_tamper_detection() if enable_signatures else None

            # Wrap handler with security features
            secure_handler = SecureLogHandler(
                base_handler=file_handler,
                encryption=encryption,
                tamper_detection=tamper_detection,
                enable_encryption=enable_encryption,
                enable_signatures=enable_signatures
            )
            secure_handler.setFormatter(formatter)
            logger.addHandler(secure_handler)
        else:
            # Use handler directly without security wrapper
            logger.addHandler(file_handler)

        # Add console handler if enabled
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(CompactTextFormatter())
            logger.addHandler(console_handler)

        return logger

    def get_logger(self, log_type: LogType = LogType.APP) -> logging.Logger:
        """
        Get logger for specific log type

        Args:
            log_type: Type of log to retrieve

        Returns:
            Logger instance
        """
        return self.loggers.get(log_type.value, self.loggers[LogType.APP.value])

    def log(
        self,
        message: str,
        level: LogLevel = LogLevel.INFO,
        log_type: LogType = LogType.APP,
        extra_data: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None
    ):
        """
        Log a message with automatic context enrichment

        Args:
            message: Log message
            level: Log level
            log_type: Type of log
            extra_data: Additional data to include
            exc_info: Exception information
        """
        logger = self.get_logger(log_type)

        # Build extra context from context vars
        extra = {
            'request_id': _request_id.get(),
            'user_id': _user_id.get(),
            'user_email': _user_email.get(),
            'ip_address': _ip_address.get(),
            'session_id': _session_id.get(),
        }

        # Remove None values
        extra = {k: v for k, v in extra.items() if v is not None}

        # Add custom extra data
        if extra_data:
            extra['extra_data'] = extra_data

        # Log at appropriate level
        log_method = getattr(logger, level.value.lower())
        log_method(message, extra=extra, exc_info=exc_info)

    # Convenience methods for common log types
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.log(message, level=LogLevel.DEBUG, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.log(message, level=LogLevel.INFO, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.log(message, level=LogLevel.WARNING, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self.log(message, level=LogLevel.ERROR, log_type=LogType.ERROR, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.log(message, level=LogLevel.CRITICAL, log_type=LogType.ERROR, **kwargs)

    def audit(self, message: str, **kwargs):
        """Log audit message"""
        self.log(message, level=LogLevel.INFO, log_type=LogType.AUDIT, **kwargs)

    def security(self, message: str, **kwargs):
        """Log security event"""
        self.log(message, level=LogLevel.WARNING, log_type=LogType.SECURITY, **kwargs)

    def performance(self, message: str, **kwargs):
        """Log performance metric"""
        self.log(message, level=LogLevel.INFO, log_type=LogType.PERFORMANCE, **kwargs)

    # Context management methods
    @staticmethod
    def set_request_context(
        request_id: Optional[str] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Set request context for log correlation

        Args:
            request_id: Unique request identifier
            user_id: User ID
            user_email: User email
            ip_address: Client IP address
            session_id: Session identifier
        """
        if request_id is not None:
            _request_id.set(request_id)
        if user_id is not None:
            _user_id.set(user_id)
        if user_email is not None:
            _user_email.set(user_email)
        if ip_address is not None:
            _ip_address.set(ip_address)
        if session_id is not None:
            _session_id.set(session_id)

    @staticmethod
    def clear_request_context():
        """Clear request context"""
        _request_id.set(None)
        _user_id.set(None)
        _user_email.set(None)
        _ip_address.set(None)
        _session_id.set(None)

    @staticmethod
    def get_request_context() -> Dict[str, Any]:
        """
        Get current request context

        Returns:
            Dictionary with current context values
        """
        return {
            'request_id': _request_id.get(),
            'user_id': _user_id.get(),
            'user_email': _user_email.get(),
            'ip_address': _ip_address.get(),
            'session_id': _session_id.get(),
        }


# Global centralized logging service instance
_logging_service: Optional[CentralizedLoggingService] = None


def get_logging_service() -> CentralizedLoggingService:
    """
    Get or create global logging service instance

    Returns:
        Global centralized logging service
    """
    global _logging_service

    if _logging_service is None:
        _logging_service = CentralizedLoggingService(
            base_dir="logs",
            use_json=False,  # Use text format by default
            enable_redaction=True,  # Enable security features
            enable_console=True  # Log to console as well
        )

    return _logging_service


# Convenience functions for backward compatibility
def get_logger(name: str = "abhimata") -> logging.Logger:
    """
    Get logger (backward compatible interface)

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    service = get_logging_service()
    return service.get_logger(LogType.APP)


def set_request_context(**kwargs):
    """Set request context (convenience function)"""
    service = get_logging_service()
    service.set_request_context(**kwargs)


def clear_request_context():
    """Clear request context (convenience function)"""
    service = get_logging_service()
    service.clear_request_context()
