"""
Input validation utilities for enhanced security
"""
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, validator, EmailStr, Field
import html


class ValidationError(Exception):
    """Custom validation error for security-related validation failures"""
    pass


def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    Sanitize string input by HTML encoding and length limiting
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
        
    Raises:
        ValidationError: If input is invalid
    """
    if not isinstance(value, str):
        raise ValidationError("Input must be a string")
    
    # Remove null bytes and control characters
    value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
    
    # HTML encode to prevent XSS
    value = html.escape(value)
    
    # Limit length
    if len(value) > max_length:
        raise ValidationError(f"Input too long. Maximum {max_length} characters allowed")
    
    return value.strip()


def validate_password_strength(password: str) -> str:
    """
    Validate password strength according to security requirements
    
    Args:
        password: Password to validate
        
    Returns:
        Validated password
        
    Raises:
        ValidationError: If password doesn't meet requirements
    """
    if not isinstance(password, str):
        raise ValidationError("Password must be a string")
    
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    if len(password) > 128:
        raise ValidationError("Password must be no more than 128 characters long")
    
    # Check for required character types
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if not has_upper:
        raise ValidationError("Password must contain at least one uppercase letter")
    
    if not has_lower:
        raise ValidationError("Password must contain at least one lowercase letter")
    
    if not has_digit:
        raise ValidationError("Password must contain at least one digit")
    
    if not has_special:
        raise ValidationError("Password must contain at least one special character")
    
    # Check for common weak patterns
    weak_patterns = [
        r'password', r'123456', r'qwerty', r'admin', r'user',
        r'letmein', r'welcome', r'monkey', r'dragon', r'master'
    ]
    
    password_lower = password.lower()
    for pattern in weak_patterns:
        if pattern in password_lower:
            raise ValidationError("Password contains common weak patterns")
    
    return password


def validate_email_format(email: str) -> str:
    """
    Validate and sanitize email format
    
    Args:
        email: Email to validate
        
    Returns:
        Validated email
        
    Raises:
        ValidationError: If email format is invalid
    """
    if not isinstance(email, str):
        raise ValidationError("Email must be a string")
    
    email = email.strip().lower()
    
    # Basic email format validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format")
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'<script', r'javascript:', r'data:', r'vbscript:',
        r'onload=', r'onerror=', r'onclick='
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, email, re.IGNORECASE):
            raise ValidationError("Email contains suspicious content")
    
    if len(email) > 254:  # RFC 5321 limit
        raise ValidationError("Email address too long")
    
    return email


def validate_name_format(name: str) -> str:
    """
    Validate and sanitize name format
    
    Args:
        name: Name to validate
        
    Returns:
        Validated name
        
    Raises:
        ValidationError: If name format is invalid
    """
    if not isinstance(name, str):
        raise ValidationError("Name must be a string")
    
    # Sanitize the name
    name = sanitize_string(name, max_length=100)
    
    if len(name.strip()) < 2:
        raise ValidationError("Name must be at least 2 characters long")
    
    # Check for valid characters (letters, spaces, hyphens, apostrophes)
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        raise ValidationError("Name can only contain letters, spaces, hyphens, and apostrophes")
    
    # Check for excessive spaces or special characters
    if re.search(r'\s{2,}', name):  # Multiple consecutive spaces
        raise ValidationError("Name cannot contain multiple consecutive spaces")
    
    return name.strip()


def validate_numeric_range(value: int, min_val: int, max_val: int, field_name: str) -> int:
    """
    Validate numeric input within specified range
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        field_name: Name of the field for error messages
        
    Returns:
        Validated value
        
    Raises:
        ValidationError: If value is out of range
    """
    if not isinstance(value, int):
        raise ValidationError(f"{field_name} must be an integer")
    
    if value < min_val or value > max_val:
        raise ValidationError(f"{field_name} must be between {min_val} and {max_val}")
    
    return value


def validate_text_content(text: str, max_length: int = 1000, allow_html: bool = False) -> str:
    """
    Validate text content for descriptions, comments, etc.
    
    Args:
        text: Text to validate
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML tags
        
    Returns:
        Validated text
        
    Raises:
        ValidationError: If text is invalid
    """
    if not isinstance(text, str):
        raise ValidationError("Text must be a string")
    
    if len(text) > max_length:
        raise ValidationError(f"Text too long. Maximum {max_length} characters allowed")
    
    # Remove null bytes and control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    if not allow_html:
        # HTML encode to prevent XSS
        text = html.escape(text)
    else:
        # Basic HTML tag validation (allow only safe tags)
        allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
        # Remove any tags not in allowed list
        text = re.sub(r'<(?!\/?(?:' + '|'.join(allowed_tags) + r')\b)[^>]*>', '', text)
    
    return text.strip()


class SecurityValidators:
    """Collection of security-focused validators for Pydantic models"""
    
    @staticmethod
    def validate_password(cls, v):
        """Pydantic validator for password strength"""
        return validate_password_strength(v)
    
    @staticmethod
    def validate_email(cls, v):
        """Pydantic validator for email format"""
        return validate_email_format(v)
    
    @staticmethod
    def validate_name(cls, v):
        """Pydantic validator for name format"""
        return validate_name_format(v)
    
    @staticmethod
    def validate_text_content(cls, v, max_length: int = 1000):
        """Pydantic validator for text content"""
        return validate_text_content(v, max_length)
    
    @staticmethod
    def validate_hole_number(cls, v):
        """Pydantic validator for hole numbers"""
        return validate_numeric_range(v, 1, 18, "Hole number")
    
    @staticmethod
    def validate_strokes(cls, v):
        """Pydantic validator for stroke counts"""
        return validate_numeric_range(v, 1, 15, "Strokes")
    
    @staticmethod
    def validate_handicap(cls, v):
        """Pydantic validator for handicap values"""
        if not isinstance(v, (int, float)):
            raise ValidationError("Handicap must be a number")
        
        if v < 0 or v > 54:
            raise ValidationError("Handicap must be between 0 and 54")
        
        return float(v)
