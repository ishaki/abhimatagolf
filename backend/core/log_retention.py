"""
Log Retention and Archival Module

Provides automated log retention and archival including:
- Configurable retention policies per log type
- Automatic archival of old log files
- Gzip compression for archived logs (70-90% storage savings)
- Automatic cleanup of expired logs
- Safe cleanup with verification
"""

import os
import gzip
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import glob

from core.config import settings
from core.logging_service import get_logging_service, LogType


class LogRetentionPolicy:
    """
    Log retention policy configuration

    Features:
    - Per-log-type retention periods
    - Configurable from settings
    - Safe defaults
    """

    def __init__(self):
        """Initialize retention policy from settings"""
        self.policies: Dict[str, int] = {
            LogType.APP.value: settings.log_retention_days_app,
            LogType.AUDIT.value: settings.log_retention_days_audit,
            LogType.SECURITY.value: settings.log_retention_days_security,
            LogType.PERFORMANCE.value: settings.log_retention_days_performance,
            LogType.ERROR.value: settings.log_retention_days_error,
        }

    def get_retention_days(self, log_type: str) -> int:
        """
        Get retention period for log type

        Args:
            log_type: Type of log

        Returns:
            Retention period in days
        """
        return self.policies.get(log_type, 30)  # Default: 30 days

    def get_cutoff_date(self, log_type: str) -> datetime:
        """
        Get cutoff date for log retention

        Args:
            log_type: Type of log

        Returns:
            Datetime before which logs should be archived/deleted
        """
        retention_days = self.get_retention_days(log_type)
        return datetime.now() - timedelta(days=retention_days)


class LogArchiver:
    """
    Log archival service

    Features:
    - Compress old log files with gzip
    - Move to archive directory
    - Preserve directory structure
    - 70-90% storage savings
    """

    def __init__(self, base_dir: str = "logs", archive_dir: str = "logs/archive"):
        """
        Initialize log archiver

        Args:
            base_dir: Base log directory
            archive_dir: Archive directory
        """
        self.base_dir = Path(base_dir)
        self.archive_dir = Path(archive_dir)
        self.logger = get_logging_service()

        # Ensure archive directory exists
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def compress_file(self, source_file: Path) -> Optional[Path]:
        """
        Compress log file using gzip

        Args:
            source_file: Path to source log file

        Returns:
            Path to compressed file, or None if failed
        """
        try:
            compressed_file = source_file.with_suffix(source_file.suffix + '.gz')

            # Compress
            with open(source_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb', compresslevel=9) as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Verify compressed file exists and has content
            if compressed_file.exists() and compressed_file.stat().st_size > 0:
                original_size = source_file.stat().st_size
                compressed_size = compressed_file.stat().st_size
                compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

                self.logger.info(
                    f"Compressed {source_file.name}: "
                    f"{original_size:,} bytes -> {compressed_size:,} bytes "
                    f"({compression_ratio:.1f}% savings)",
                    log_type=LogType.APP
                )

                return compressed_file
            else:
                self.logger.error(f"Compressed file is empty: {compressed_file}")
                if compressed_file.exists():
                    compressed_file.unlink()
                return None

        except Exception as e:
            self.logger.error(f"Failed to compress {source_file}: {e}")
            return None

    def archive_file(self, source_file: Path, log_type: str) -> bool:
        """
        Archive log file (compress and move to archive directory)

        Args:
            source_file: Path to source log file
            log_type: Type of log

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create archive subdirectory for log type
            archive_subdir = self.archive_dir / log_type
            archive_subdir.mkdir(parents=True, exist_ok=True)

            # Compress file
            compressed_file = self.compress_file(source_file)
            if not compressed_file:
                return False

            # Move to archive
            archive_path = archive_subdir / compressed_file.name
            shutil.move(str(compressed_file), str(archive_path))

            # Delete original file
            source_file.unlink()

            self.logger.info(
                f"Archived {source_file.name} to {archive_path}",
                log_type=LogType.APP
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to archive {source_file}: {e}")
            return False

    def archive_old_logs(self, log_type: str, cutoff_date: datetime) -> Tuple[int, int]:
        """
        Archive log files older than cutoff date

        Args:
            log_type: Type of log
            cutoff_date: Archive files modified before this date

        Returns:
            Tuple of (archived_count, failed_count)
        """
        log_dir = self.base_dir / log_type
        if not log_dir.exists():
            return 0, 0

        archived = 0
        failed = 0

        # Find log files (*.log.* but not *.gz)
        for log_file in log_dir.glob("*.log.*"):
            if log_file.suffix == '.gz':
                continue  # Skip already compressed files

            try:
                # Check modification time
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

                if mtime < cutoff_date:
                    if self.archive_file(log_file, log_type):
                        archived += 1
                    else:
                        failed += 1
            except Exception as e:
                self.logger.error(f"Error processing {log_file}: {e}")
                failed += 1

        return archived, failed


class LogCleaner:
    """
    Log cleanup service

    Features:
    - Remove expired logs from archive
    - Safe deletion with verification
    - Preserve logs within retention period
    """

    def __init__(self, archive_dir: str = "logs/archive"):
        """
        Initialize log cleaner

        Args:
            archive_dir: Archive directory
        """
        self.archive_dir = Path(archive_dir)
        self.logger = get_logging_service()
        self.policy = LogRetentionPolicy()

    def cleanup_old_archives(self, log_type: str) -> Tuple[int, int]:
        """
        Remove archived logs older than retention period

        Args:
            log_type: Type of log

        Returns:
            Tuple of (deleted_count, bytes_freed)
        """
        archive_subdir = self.archive_dir / log_type
        if not archive_subdir.exists():
            return 0, 0

        # Get retention cutoff date (double the retention period for archives)
        retention_days = self.policy.get_retention_days(log_type)
        archive_cutoff = datetime.now() - timedelta(days=retention_days * 2)

        deleted = 0
        bytes_freed = 0

        # Find archived files (*.gz)
        for archive_file in archive_subdir.glob("*.gz"):
            try:
                # Check modification time
                mtime = datetime.fromtimestamp(archive_file.stat().st_mtime)

                if mtime < archive_cutoff:
                    file_size = archive_file.stat().st_size
                    archive_file.unlink()
                    deleted += 1
                    bytes_freed += file_size

                    self.logger.info(
                        f"Deleted expired archive: {archive_file.name} "
                        f"({file_size:,} bytes)",
                        log_type=LogType.APP
                    )
            except Exception as e:
                self.logger.error(f"Error deleting {archive_file}: {e}")

        return deleted, bytes_freed


class LogMaintenanceService:
    """
    Automated log maintenance service

    Features:
    - Periodic archival of old logs
    - Automatic cleanup of expired archives
    - Storage optimization
    - Maintenance reports
    """

    def __init__(
        self,
        base_dir: str = "logs",
        archive_dir: str = "logs/archive"
    ):
        """
        Initialize log maintenance service

        Args:
            base_dir: Base log directory
            archive_dir: Archive directory
        """
        self.archiver = LogArchiver(base_dir, archive_dir)
        self.cleaner = LogCleaner(archive_dir)
        self.policy = LogRetentionPolicy()
        self.logger = get_logging_service()

    def run_maintenance(self) -> Dict[str, Any]:
        """
        Run full log maintenance cycle

        Returns:
            Dictionary with maintenance statistics
        """
        self.logger.info("Starting log maintenance", log_type=LogType.APP)

        results = {
            'timestamp': datetime.now().isoformat(),
            'log_types': {}
        }

        for log_type in LogType:
            log_type_name = log_type.value

            # Get cutoff date for this log type
            cutoff_date = self.policy.get_cutoff_date(log_type_name)

            # Archive old logs
            archived, archive_failed = self.archiver.archive_old_logs(
                log_type_name, cutoff_date
            )

            # Cleanup old archives
            deleted, bytes_freed = self.cleaner.cleanup_old_archives(log_type_name)

            results['log_types'][log_type_name] = {
                'retention_days': self.policy.get_retention_days(log_type_name),
                'cutoff_date': cutoff_date.isoformat(),
                'archived': archived,
                'archive_failed': archive_failed,
                'deleted': deleted,
                'bytes_freed': bytes_freed
            }

        # Calculate totals
        results['totals'] = {
            'archived': sum(r['archived'] for r in results['log_types'].values()),
            'deleted': sum(r['deleted'] for r in results['log_types'].values()),
            'bytes_freed': sum(r['bytes_freed'] for r in results['log_types'].values())
        }

        self.logger.info(
            f"Log maintenance completed: "
            f"{results['totals']['archived']} archived, "
            f"{results['totals']['deleted']} deleted, "
            f"{results['totals']['bytes_freed']:,} bytes freed",
            log_type=LogType.APP,
            extra_data=results
        )

        return results

    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics for logs

        Returns:
            Dictionary with storage statistics
        """
        stats = {
            'active_logs': {},
            'archived_logs': {},
            'total_active_bytes': 0,
            'total_archive_bytes': 0
        }

        base_dir = Path(self.archiver.base_dir)
        archive_dir = Path(self.archiver.archive_dir)

        # Active logs
        for log_type in LogType:
            log_dir = base_dir / log_type.value
            if log_dir.exists():
                files = list(log_dir.glob("*.log*"))
                total_bytes = sum(f.stat().st_size for f in files if not f.suffix == '.gz')
                stats['active_logs'][log_type.value] = {
                    'file_count': len(files),
                    'total_bytes': total_bytes
                }
                stats['total_active_bytes'] += total_bytes

        # Archived logs
        for log_type in LogType:
            archive_subdir = archive_dir / log_type.value
            if archive_subdir.exists():
                files = list(archive_subdir.glob("*.gz"))
                total_bytes = sum(f.stat().st_size for f in files)
                stats['archived_logs'][log_type.value] = {
                    'file_count': len(files),
                    'total_bytes': total_bytes
                }
                stats['total_archive_bytes'] += total_bytes

        # Total
        stats['total_bytes'] = stats['total_active_bytes'] + stats['total_archive_bytes']

        return stats


# Global maintenance service
_maintenance_service: Optional[LogMaintenanceService] = None


def get_maintenance_service() -> LogMaintenanceService:
    """
    Get global log maintenance service

    Returns:
        LogMaintenanceService instance
    """
    global _maintenance_service

    if _maintenance_service is None:
        _maintenance_service = LogMaintenanceService()

    return _maintenance_service


def run_log_maintenance() -> Dict[str, Any]:
    """
    Run log maintenance (convenience function)

    Returns:
        Maintenance results
    """
    service = get_maintenance_service()
    return service.run_maintenance()


def get_log_storage_stats() -> Dict[str, Any]:
    """
    Get log storage statistics (convenience function)

    Returns:
        Storage statistics
    """
    service = get_maintenance_service()
    return service.get_storage_statistics()
