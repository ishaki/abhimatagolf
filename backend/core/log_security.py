"""
Log Security Module

Provides security features for logging including:
- Log encryption (AES-256) for sensitive log files
- HMAC tamper detection for audit logs
- Key management and rotation
- Secure key derivation from passwords

Security features are configurable per log type.
"""

import os
import hmac
import hashlib
import base64
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import logging


class LogEncryption:
    """
    Handle log encryption using Fernet (AES-256)

    Features:
    - AES-256 encryption for sensitive log files
    - Key derivation from password using PBKDF2
    - Secure key storage in environment variables
    - Per-log-type encryption control
    """

    def __init__(self, encryption_key: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize log encryption

        Args:
            encryption_key: Base64-encoded Fernet key (32 bytes)
            password: Password for key derivation (alternative to encryption_key)
        """
        self.cipher = None

        if encryption_key:
            # Use provided key directly
            try:
                self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
            except Exception as e:
                logging.warning(f"Invalid encryption key: {e}")
        elif password:
            # Derive key from password
            key = self._derive_key_from_password(password)
            self.cipher = Fernet(key)

    @staticmethod
    def _derive_key_from_password(password: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive encryption key from password using PBKDF2

        Args:
            password: User password
            salt: Salt for key derivation (uses fixed salt if not provided)

        Returns:
            Base64-encoded Fernet key
        """
        # Use fixed salt from environment or default
        # In production, store salt securely
        if salt is None:
            salt = os.environ.get('LOG_ENCRYPTION_SALT', 'abhimata-golf-logs-2024').encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    @staticmethod
    def generate_key() -> str:
        """
        Generate new encryption key

        Returns:
            Base64-encoded Fernet key as string
        """
        return Fernet.generate_key().decode()

    def encrypt(self, data: str) -> Optional[str]:
        """
        Encrypt log data

        Args:
            data: Plain text log data

        Returns:
            Encrypted data as base64 string, or None if encryption fails
        """
        if not self.cipher:
            return data  # Return plain text if encryption not configured

        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logging.error(f"Encryption failed: {e}")
            return None

    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """
        Decrypt log data

        Args:
            encrypted_data: Base64-encoded encrypted data

        Returns:
            Decrypted plain text, or None if decryption fails
        """
        if not self.cipher:
            return encrypted_data  # Return as-is if encryption not configured

        try:
            decoded = base64.b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except InvalidToken:
            logging.error("Decryption failed: Invalid token or corrupted data")
            return None
        except Exception as e:
            logging.error(f"Decryption failed: {e}")
            return None

    def is_enabled(self) -> bool:
        """Check if encryption is enabled"""
        return self.cipher is not None


class LogTamperDetection:
    """
    HMAC-based tamper detection for audit logs

    Features:
    - HMAC-SHA256 signatures for log entries
    - Signature verification
    - Tamper detection alerts
    """

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize tamper detection

        Args:
            secret_key: Secret key for HMAC generation
        """
        self.secret_key = secret_key or os.environ.get('LOG_HMAC_SECRET', 'default-hmac-secret-change-in-production')

    def generate_signature(self, message: str) -> str:
        """
        Generate HMAC signature for log message

        Args:
            message: Log message to sign

        Returns:
            Hex-encoded HMAC signature
        """
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def verify_signature(self, message: str, signature: str) -> bool:
        """
        Verify HMAC signature

        Args:
            message: Original log message
            signature: Hex-encoded HMAC signature

        Returns:
            True if signature is valid, False otherwise
        """
        expected_signature = self.generate_signature(message)
        return hmac.compare_digest(expected_signature, signature)

    def sign_log_entry(self, log_entry: str) -> str:
        """
        Add HMAC signature to log entry

        Args:
            log_entry: Original log entry

        Returns:
            Log entry with signature appended
        """
        signature = self.generate_signature(log_entry)
        return f"{log_entry} | HMAC:{signature}"

    def verify_log_entry(self, signed_entry: str) -> Dict[str, Any]:
        """
        Verify log entry signature and detect tampering

        Args:
            signed_entry: Log entry with signature

        Returns:
            Dictionary with verification results
        """
        try:
            # Split entry and signature
            if ' | HMAC:' not in signed_entry:
                return {
                    'valid': False,
                    'error': 'No signature found',
                    'tampered': True
                }

            parts = signed_entry.rsplit(' | HMAC:', 1)
            if len(parts) != 2:
                return {
                    'valid': False,
                    'error': 'Invalid signature format',
                    'tampered': True
                }

            message, signature = parts
            is_valid = self.verify_signature(message, signature)

            return {
                'valid': is_valid,
                'message': message,
                'signature': signature,
                'tampered': not is_valid
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'tampered': True
            }


class SecureLogHandler(logging.Handler):
    """
    Log handler with encryption and tamper detection

    Features:
    - Optional encryption for sensitive logs
    - HMAC signatures for audit logs
    - Configurable security features per handler
    """

    def __init__(
        self,
        base_handler: logging.Handler,
        encryption: Optional[LogEncryption] = None,
        tamper_detection: Optional[LogTamperDetection] = None,
        enable_encryption: bool = False,
        enable_signatures: bool = False
    ):
        """
        Initialize secure log handler

        Args:
            base_handler: Underlying file handler
            encryption: LogEncryption instance
            tamper_detection: LogTamperDetection instance
            enable_encryption: Enable log encryption
            enable_signatures: Enable HMAC signatures
        """
        super().__init__()
        self.base_handler = base_handler
        self.encryption = encryption
        self.tamper_detection = tamper_detection
        self.enable_encryption = enable_encryption and encryption is not None
        self.enable_signatures = enable_signatures and tamper_detection is not None

    def emit(self, record: logging.LogRecord):
        """
        Emit log record with security features

        Args:
            record: Log record to emit
        """
        try:
            # Format the record
            msg = self.format(record)

            # Add HMAC signature if enabled
            if self.enable_signatures and self.tamper_detection:
                msg = self.tamper_detection.sign_log_entry(msg)

            # Encrypt if enabled
            if self.enable_encryption and self.encryption:
                encrypted_msg = self.encryption.encrypt(msg)
                if encrypted_msg:
                    msg = f"[ENCRYPTED] {encrypted_msg}"

            # Create new record with processed message
            processed_record = logging.LogRecord(
                name=record.name,
                level=record.levelno,
                pathname=record.pathname,
                lineno=record.lineno,
                msg=msg,
                args=(),
                exc_info=None
            )

            # Emit to base handler
            self.base_handler.emit(processed_record)

        except Exception:
            self.handleError(record)

    def close(self):
        """Close handler"""
        self.base_handler.close()
        super().close()


# Global instances (lazy initialization)
_log_encryption: Optional[LogEncryption] = None
_log_tamper_detection: Optional[LogTamperDetection] = None


def get_log_encryption() -> Optional[LogEncryption]:
    """
    Get global log encryption instance

    Returns:
        LogEncryption instance or None if not configured
    """
    global _log_encryption

    if _log_encryption is None:
        # Try to initialize from environment
        encryption_key = os.environ.get('LOG_ENCRYPTION_KEY')
        encryption_password = os.environ.get('LOG_ENCRYPTION_PASSWORD')

        if encryption_key or encryption_password:
            _log_encryption = LogEncryption(
                encryption_key=encryption_key,
                password=encryption_password
            )

    return _log_encryption


def get_log_tamper_detection() -> LogTamperDetection:
    """
    Get global tamper detection instance

    Returns:
        LogTamperDetection instance
    """
    global _log_tamper_detection

    if _log_tamper_detection is None:
        _log_tamper_detection = LogTamperDetection()

    return _log_tamper_detection


# Utility functions
def decrypt_log_file(input_file: str, output_file: str, encryption: Optional[LogEncryption] = None):
    """
    Decrypt encrypted log file

    Args:
        input_file: Path to encrypted log file
        output_file: Path to save decrypted log file
        encryption: LogEncryption instance (uses global if not provided)
    """
    if encryption is None:
        encryption = get_log_encryption()

    if not encryption or not encryption.is_enabled():
        raise ValueError("Encryption not configured")

    with open(input_file, 'r', encoding='utf-8') as f_in:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                line = line.strip()
                if line.startswith('[ENCRYPTED] '):
                    encrypted_data = line[12:]  # Remove '[ENCRYPTED] ' prefix
                    decrypted = encryption.decrypt(encrypted_data)
                    if decrypted:
                        f_out.write(decrypted + '\n')
                else:
                    f_out.write(line + '\n')


def verify_log_file_integrity(log_file: str, tamper_detection: Optional[LogTamperDetection] = None) -> Dict[str, Any]:
    """
    Verify integrity of log file with HMAC signatures

    Args:
        log_file: Path to log file
        tamper_detection: LogTamperDetection instance (uses global if not provided)

    Returns:
        Dictionary with verification results
    """
    if tamper_detection is None:
        tamper_detection = get_log_tamper_detection()

    results = {
        'total_entries': 0,
        'signed_entries': 0,
        'valid_signatures': 0,
        'invalid_signatures': 0,
        'tampered_entries': []
    }

    with open(log_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            results['total_entries'] += 1

            if ' | HMAC:' in line:
                results['signed_entries'] += 1
                verification = tamper_detection.verify_log_entry(line)

                if verification['valid']:
                    results['valid_signatures'] += 1
                else:
                    results['invalid_signatures'] += 1
                    results['tampered_entries'].append({
                        'line_number': line_num,
                        'error': verification.get('error', 'Invalid signature')
                    })

    return results
