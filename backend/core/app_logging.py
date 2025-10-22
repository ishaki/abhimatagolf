"""
Application Logging Module

Now powered by centralized logging service with security features including:
- Automatic sensitive data redaction
- Cross-platform log rotation
- Structured logging support
- Request correlation

Maintains backward compatibility with existing code.
"""

import logging
import platform
from core.config import settings

# Import centralized logging service
from core.logging_service import (
    get_logging_service,
    get_logger as get_centralized_logger,
    LogType
)


def setup_logging():
    """
    Configure logging for the application

    Now uses centralized logging service with enhanced features:
    - Automatic sensitive data redaction
    - Cross-platform safe log rotation
    - Multiple log types (app, audit, security, performance, error)
    - Request correlation
    """

    # Initialize centralized logging service
    logging_service = get_logging_service()

    # Get application logger from centralized service
    app_logger = logging_service.get_logger(LogType.APP)

    # Log initialization message
    app_logger.info(
        f"Centralized logging initialized - "
        f"Level: {settings.log_level}, "
        f"Base Dir: {logging_service.base_dir}, "
        f"Platform: {platform.system()}, "
        f"Redaction: {'Enabled' if logging_service.enable_redaction else 'Disabled'}"
    )

    return app_logger


def get_logger(name: str = "abhimata") -> logging.Logger:
    """
    Get logger instance (backward compatible)

    Args:
        name: Logger name (optional, for backward compatibility)

    Returns:
        Logger instance from centralized service
    """
    # Use centralized logging service
    return get_centralized_logger(name)


# Initialize logging and create default logger
# This maintains backward compatibility with code that imports 'logger' directly
logger = setup_logging()
