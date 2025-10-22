"""
Log formatters for centralized logging service

Provides both JSON (machine-readable) and text (human-readable) formatters
with support for structured logging and request correlation.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging

    Outputs logs in JSON format for easy parsing by log aggregation tools
    (ELK Stack, Splunk, CloudWatch, etc.)
    """

    def __init__(
        self,
        include_timestamp: bool = True,
        include_level: bool = True,
        include_logger_name: bool = True,
        date_format: Optional[str] = None
    ):
        """
        Initialize JSON formatter

        Args:
            include_timestamp: Include timestamp in output
            include_level: Include log level in output
            include_logger_name: Include logger name in output
            date_format: Date format string (default: ISO 8601)
        """
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_logger_name = include_logger_name
        self.date_format = date_format or '%Y-%m-%dT%H:%M:%S.%fZ'

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON

        Args:
            record: Log record to format

        Returns:
            JSON string with log data
        """
        log_data: Dict[str, Any] = {}

        # Basic fields
        if self.include_timestamp:
            log_data['timestamp'] = datetime.fromtimestamp(record.created).strftime(self.date_format)

        if self.include_level:
            log_data['level'] = record.levelname

        if self.include_logger_name:
            log_data['logger'] = record.name

        log_data['message'] = record.getMessage()

        # Context fields (if available)
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id

        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id

        if hasattr(record, 'user_email'):
            log_data['user_email'] = record.user_email

        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address

        if hasattr(record, 'session_id'):
            log_data['session_id'] = record.session_id

        # Source location
        log_data['source'] = {
            'file': record.pathname,
            'line': record.lineno,
            'function': record.funcName
        }

        # Exception information
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }

        # Additional custom fields
        if hasattr(record, 'extra_data') and record.extra_data:
            log_data['extra'] = record.extra_data

        # Thread/process info (optional)
        if hasattr(record, 'thread'):
            log_data['thread'] = {
                'id': record.thread,
                'name': record.threadName
            }

        if hasattr(record, 'process'):
            log_data['process'] = {
                'id': record.process,
                'name': record.processName
            }

        return json.dumps(log_data, default=str, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """
    Text formatter for human-readable logging

    Provides colored output (if terminal supports it) and structured
    format for easy reading.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def __init__(
        self,
        use_colors: bool = False,
        include_thread: bool = False,
        include_process: bool = False,
        date_format: Optional[str] = None
    ):
        """
        Initialize text formatter

        Args:
            use_colors: Use ANSI colors in output
            include_thread: Include thread information
            include_process: Include process information
            date_format: Date format string
        """
        # Default format: timestamp - name - level - message
        fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        super().__init__(fmt=fmt, datefmt=date_format or '%Y-%m-%d %H:%M:%S')
        self.use_colors = use_colors
        self.include_thread = include_thread
        self.include_process = include_process

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as text

        Args:
            record: Log record to format

        Returns:
            Formatted text string
        """
        # Apply color if enabled
        if self.use_colors:
            levelname_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{levelname_color}{record.levelname}{self.COLORS['RESET']}"

        # Format basic message
        formatted = super().format(record)

        # Add context information if available
        context_parts = []

        if hasattr(record, 'request_id'):
            context_parts.append(f"request_id={record.request_id}")

        if hasattr(record, 'user_email'):
            context_parts.append(f"user={record.user_email}")

        if hasattr(record, 'ip_address'):
            context_parts.append(f"ip={record.ip_address}")

        if self.include_thread and hasattr(record, 'threadName'):
            context_parts.append(f"thread={record.threadName}")

        if self.include_process and hasattr(record, 'processName'):
            context_parts.append(f"process={record.processName}")

        if context_parts:
            formatted += f" [{', '.join(context_parts)}]"

        # Add exception information if present
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


class CompactTextFormatter(logging.Formatter):
    """
    Compact text formatter for production environments

    Single-line format optimized for log aggregation and storage.
    """

    def __init__(self, date_format: Optional[str] = None):
        """
        Initialize compact formatter

        Args:
            date_format: Date format string
        """
        super().__init__(datefmt=date_format or '%Y-%m-%d %H:%M:%S')

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record in compact single-line format

        Args:
            record: Log record to format

        Returns:
            Compact formatted string
        """
        timestamp = datetime.fromtimestamp(record.created).strftime(self.datefmt)

        # Build compact log line
        parts = [
            timestamp,
            record.levelname[:4],  # Abbreviated level (INFO -> INFO, WARN -> WARN)
            record.name,
            record.getMessage()
        ]

        # Add context
        if hasattr(record, 'request_id'):
            parts.append(f"req={record.request_id[:8]}")  # Short request ID

        if hasattr(record, 'user_email'):
            parts.append(f"user={record.user_email}")

        # Join with pipe separator
        formatted = " | ".join(parts)

        # Add exception on new line if present
        if record.exc_info:
            formatted += "\n  " + self.formatException(record.exc_info).replace('\n', '\n  ')

        return formatted
