"""
Custom log handlers for centralized logging service

Provides handlers with security features including sensitive data redaction,
cross-platform log rotation, and directory-based log organization.
"""

import os
import re
import logging
import platform
from typing import Dict, List, Pattern, Optional
from logging.handlers import RotatingFileHandler

# Try to import concurrent-log-handler for Windows-safe rotation
try:
    from concurrent_log_handler import ConcurrentRotatingFileHandler
    HAS_CONCURRENT_HANDLER = True
except ImportError:
    HAS_CONCURRENT_HANDLER = False


# Sensitive data patterns for redaction
SENSITIVE_PATTERNS: Dict[str, Pattern] = {
    'password': re.compile(r'(?:password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE),
    'token': re.compile(r'(?:token|access_token|refresh_token)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE),
    'api_key': re.compile(r'(?:api[-_]?key|apikey)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE),
    'secret': re.compile(r'(?:secret|client_secret)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE),
    'authorization': re.compile(r'(?:authorization|auth)["\']?\s*[:=]\s*["\']?(?:bearer\s+)?([^"\'\s,}]+)', re.IGNORECASE),
    'cookie': re.compile(r'(?:cookie|set-cookie)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE),
    # Credit card (basic pattern - matches 13-19 digit sequences)
    'credit_card': re.compile(r'\b\d{13,19}\b'),
    # SSN (US format: XXX-XX-XXXX)
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    # Email (partial redaction - keep domain visible)
    'email_partial': re.compile(r'\b([a-zA-Z0-9._%+-]{1,3})[a-zA-Z0-9._%+-]*@'),
}

# Redaction marker
REDACTED = '[REDACTED]'
EMAIL_REDACTED = r'\1***@'


class RedactingFormatter(logging.Formatter):
    """
    Formatter that automatically redacts sensitive information from log messages

    Redacts passwords, tokens, API keys, credit cards, SSNs, and partially redacts emails.
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        custom_patterns: Optional[Dict[str, Pattern]] = None,
        enabled: bool = True
    ):
        """
        Initialize redacting formatter

        Args:
            fmt: Log format string
            datefmt: Date format string
            custom_patterns: Additional regex patterns for redaction
            enabled: Enable/disable redaction (for debugging)
        """
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.enabled = enabled
        self.patterns = SENSITIVE_PATTERNS.copy()

        if custom_patterns:
            self.patterns.update(custom_patterns)

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with sensitive data redaction

        Args:
            record: Log record to format

        Returns:
            Formatted string with sensitive data redacted
        """
        # Format the message first
        formatted = super().format(record)

        # Apply redaction if enabled
        if self.enabled:
            formatted = self._redact_sensitive_data(formatted)

        return formatted

    def _redact_sensitive_data(self, message: str) -> str:
        """
        Redact sensitive information from message

        Args:
            message: Original message

        Returns:
            Message with sensitive data redacted
        """
        redacted = message

        # Apply each redaction pattern
        for pattern_name, pattern in self.patterns.items():
            if pattern_name == 'email_partial':
                # Partial email redaction: keep first 1-3 chars + domain
                redacted = pattern.sub(EMAIL_REDACTED, redacted)
            else:
                # Full redaction for other patterns
                redacted = pattern.sub(lambda m: m.group(0).replace(m.group(1), REDACTED), redacted)

        return redacted


def get_rotating_handler(
    filename: str,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB default
    backup_count: int = 5,
    encoding: str = 'utf-8',
    delay: bool = True
) -> logging.Handler:
    """
    Get appropriate rotating file handler based on platform

    Uses ConcurrentRotatingFileHandler on Windows for safe rotation with
    multiple processes, falls back to RotatingFileHandler on Unix.

    Args:
        filename: Log file path
        max_bytes: Maximum file size before rotation
        backup_count: Number of backup files to keep
        encoding: File encoding
        delay: Delay file creation until first write

    Returns:
        Appropriate rotating file handler for the platform
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    is_windows = platform.system() == 'Windows'

    # Use concurrent handler on Windows if available
    if is_windows and HAS_CONCURRENT_HANDLER:
        return ConcurrentRotatingFileHandler(
            filename=filename,
            mode='a',
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
            delay=delay
        )
    elif is_windows:
        # Windows without concurrent handler - use simple FileHandler to avoid locking
        return logging.FileHandler(
            filename=filename,
            mode='a',
            encoding=encoding,
            delay=delay
        )
    else:
        # Unix/Linux - standard RotatingFileHandler works fine
        return RotatingFileHandler(
            filename=filename,
            mode='a',
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
            delay=delay
        )


class DirectoryBasedHandler(logging.Handler):
    """
    Handler that routes log records to different files based on log level
    or custom criteria, organized in directories.

    Example:
        logs/
        ├── app/app.log       # INFO and DEBUG
        ├── errors/error.log  # ERROR and CRITICAL
        ├── audit/audit.log   # Audit logs
    """

    def __init__(
        self,
        base_dir: str = 'logs',
        level_dirs: Optional[Dict[str, List[str]]] = None,
        **handler_kwargs
    ):
        """
        Initialize directory-based handler

        Args:
            base_dir: Base directory for all logs
            level_dirs: Mapping of directory names to log levels
                       Example: {'errors': ['ERROR', 'CRITICAL']}
            handler_kwargs: Additional arguments for file handlers
        """
        super().__init__()
        self.base_dir = base_dir
        self.handlers: Dict[str, logging.Handler] = {}
        self.level_dirs = level_dirs or {
            'app': ['DEBUG', 'INFO', 'WARNING'],
            'errors': ['ERROR', 'CRITICAL']
        }
        self.handler_kwargs = handler_kwargs

        # Create handlers for each directory
        self._create_handlers()

    def _create_handlers(self):
        """Create file handlers for each directory"""
        for dir_name, levels in self.level_dirs.items():
            log_file = os.path.join(self.base_dir, dir_name, f'{dir_name}.log')
            handler = get_rotating_handler(log_file, **self.handler_kwargs)
            self.handlers[dir_name] = handler

    def emit(self, record: logging.LogRecord):
        """
        Emit log record to appropriate file based on level

        Args:
            record: Log record to emit
        """
        # Find appropriate handler(s) for this log level
        for dir_name, levels in self.level_dirs.items():
            if record.levelname in levels:
                handler = self.handlers.get(dir_name)
                if handler:
                    handler.emit(record)

    def close(self):
        """Close all handlers"""
        for handler in self.handlers.values():
            handler.close()
        super().close()


def create_handler_for_log_type(
    log_type: str,
    base_dir: str = 'logs',
    formatter: Optional[logging.Formatter] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5
) -> logging.Handler:
    """
    Create handler for specific log type with appropriate configuration

    Args:
        log_type: Type of log (app, audit, security, performance, error)
        base_dir: Base directory for logs
        formatter: Log formatter to use
        max_bytes: Maximum file size before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logging handler
    """
    # Create directory structure: logs/{type}/{type}.log
    log_dir = os.path.join(base_dir, log_type)
    log_file = os.path.join(log_dir, f'{log_type}.log')

    # Get appropriate rotating handler
    handler = get_rotating_handler(
        filename=log_file,
        max_bytes=max_bytes,
        backup_count=backup_count
    )

    # Apply formatter if provided
    if formatter:
        handler.setFormatter(formatter)

    return handler
