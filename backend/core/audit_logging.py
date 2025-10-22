"""
Audit logging system for security monitoring and compliance
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from sqlmodel import SQLModel, Field, Session, select
from core.database import get_session


class AuditAction(str, Enum):
    """Enumeration of auditable actions"""
    # Authentication actions
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    
    # User management actions
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ACTIVATE = "user_activate"
    USER_DEACTIVATE = "user_deactivate"
    
    # Event management actions
    EVENT_CREATE = "event_create"
    EVENT_UPDATE = "event_update"
    EVENT_DELETE = "event_delete"
    EVENT_DUPLICATE = "event_duplicate"
    
    # Score management actions
    SCORE_SUBMIT = "score_submit"
    SCORE_UPDATE = "score_update"
    SCORE_DELETE = "score_delete"
    SCORE_BULK_SUBMIT = "score_bulk_submit"
    
    # Participant management actions
    PARTICIPANT_CREATE = "participant_create"
    PARTICIPANT_UPDATE = "participant_update"
    PARTICIPANT_DELETE = "participant_delete"
    
    # Course management actions
    COURSE_CREATE = "course_create"
    COURSE_UPDATE = "course_update"
    COURSE_DELETE = "course_delete"
    
    # Data export actions
    DATA_EXPORT = "data_export"
    REPORT_GENERATE = "report_generate"
    
    # System actions
    SYSTEM_ERROR = "system_error"
    SECURITY_VIOLATION = "security_violation"
    PERMISSION_DENIED = "permission_denied"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLog(SQLModel, table=True):
    """Audit log table for tracking all security-relevant actions"""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Event identification
    action: AuditAction = Field(index=True)
    severity: AuditSeverity = Field(default=AuditSeverity.LOW, index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # User information
    user_id: Optional[int] = Field(default=None, index=True)
    user_email: Optional[str] = Field(default=None, index=True)
    user_role: Optional[str] = Field(default=None)
    
    # Request information
    ip_address: Optional[str] = Field(default=None, index=True)
    user_agent: Optional[str] = Field(default=None)
    request_id: Optional[str] = Field(default=None, index=True)
    
    # Event details
    resource_type: Optional[str] = Field(default=None, index=True)  # e.g., "user", "event", "score"
    resource_id: Optional[int] = Field(default=None, index=True)
    event_description: str = Field(max_length=500)
    
    # Additional data (JSON)
    additional_data: Optional[str] = Field(default=None)  # JSON string
    
    # Result information
    success: bool = Field(default=True, index=True)
    error_message: Optional[str] = Field(default=None)
    
    # Metadata
    session_id: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLogger:
    """Centralized audit logging service"""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler for audit logs
        audit_handler = logging.FileHandler('logs/audit.log')
        audit_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        audit_handler.setFormatter(formatter)
        
        # Add handler if not already added
        if not self.logger.handlers:
            self.logger.addHandler(audit_handler)
    
    def log_event(
        self,
        action: AuditAction,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        description: str = "",
        additional_data: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.LOW,
        session_id: Optional[str] = None
    ) -> None:
        """
        Log an audit event to both database and file
        
        Args:
            action: The action being audited
            user_id: ID of the user performing the action
            user_email: Email of the user performing the action
            user_role: Role of the user performing the action
            ip_address: IP address of the request
            user_agent: User agent string
            request_id: Unique request identifier
            resource_type: Type of resource being acted upon
            resource_id: ID of the resource being acted upon
            description: Human-readable description of the event
            additional_data: Additional data as dictionary
            success: Whether the action was successful
            error_message: Error message if action failed
            severity: Severity level of the event
            session_id: Session identifier
        """
        try:
            # Prepare additional data
            additional_data_json = None
            if additional_data:
                additional_data_json = json.dumps(additional_data, default=str)
            
            # Create audit log entry
            audit_entry = AuditLog(
                action=action,
                severity=severity,
                user_id=user_id,
                user_email=user_email,
                user_role=user_role,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                resource_type=resource_type,
                resource_id=resource_id,
                event_description=description,
                additional_data=additional_data_json,
                success=success,
                error_message=error_message,
                session_id=session_id
            )
            
            # Save to database
            session = next(get_session())
            session.add(audit_entry)
            session.commit()
            session.close()
            
            # Log to file
            log_message = self._format_log_message(audit_entry)
            if severity == AuditSeverity.CRITICAL:
                self.logger.critical(log_message)
            elif severity == AuditSeverity.HIGH:
                self.logger.error(log_message)
            elif severity == AuditSeverity.MEDIUM:
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)
                
        except Exception as e:
            # Fallback logging if audit system fails
            self.logger.error(f"Failed to log audit event: {e}")
    
    def _format_log_message(self, audit_entry: AuditLog) -> str:
        """Format audit entry for file logging"""
        return (
            f"ACTION={audit_entry.action} | "
            f"USER={audit_entry.user_email or 'anonymous'} | "
            f"IP={audit_entry.ip_address or 'unknown'} | "
            f"RESOURCE={audit_entry.resource_type}:{audit_entry.resource_id or 'N/A'} | "
            f"SUCCESS={audit_entry.success} | "
            f"DESC={audit_entry.event_description}"
        )
    
    def log_authentication_success(
        self,
        user_id: int,
        user_email: str,
        user_role: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> None:
        """Log successful authentication"""
        self.log_event(
            action=AuditAction.LOGIN_SUCCESS,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            description=f"User {user_email} successfully authenticated",
            severity=AuditSeverity.MEDIUM
        )
    
    def log_authentication_failure(
        self,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        reason: str = "Invalid credentials"
    ) -> None:
        """Log failed authentication attempt"""
        self.log_event(
            action=AuditAction.LOGIN_FAILURE,
            user_email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            description=f"Failed authentication attempt for {email}: {reason}",
            success=False,
            error_message=reason,
            severity=AuditSeverity.HIGH
        )
    
    def log_user_action(
        self,
        action: AuditAction,
        user_id: int,
        user_email: str,
        user_role: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        description: str = "",
        additional_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """Log user-initiated actions"""
        severity = AuditSeverity.HIGH if not success else AuditSeverity.MEDIUM
        
        self.log_event(
            action=action,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            additional_data=additional_data,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            success=success,
            error_message=error_message,
            severity=severity
        )
    
    def log_security_violation(
        self,
        violation_type: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        description: str = "",
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log security violations"""
        self.log_event(
            action=AuditAction.SECURITY_VIOLATION,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            description=f"Security violation ({violation_type}): {description}",
            additional_data=additional_data,
            success=False,
            severity=AuditSeverity.CRITICAL
        )
    
    def log_permission_denied(
        self,
        user_id: int,
        user_email: str,
        user_role: str,
        attempted_action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> None:
        """Log permission denied events"""
        self.log_event(
            action=AuditAction.PERMISSION_DENIED,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            resource_type=resource_type,
            resource_id=resource_id,
            description=f"Permission denied: {user_email} attempted {attempted_action}",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            success=False,
            severity=AuditSeverity.HIGH
        )


# Global audit logger instance
audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance"""
    return audit_logger
