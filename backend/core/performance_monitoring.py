"""
Performance Monitoring Module

Provides comprehensive performance monitoring including:
- Request/response duration tracking
- Endpoint-specific timing
- Slow query detection
- Database metrics (query time, connection pool)
- WebSocket metrics (connections, throughput, latency)
- Resource usage (memory, CPU, disk I/O)
- Automatic logging of performance issues
"""

import time
import psutil
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from contextlib import contextmanager
from functools import wraps
from contextvars import ContextVar

from core.logging_service import get_logging_service, LogType

# Context variable for request timing
_request_start_time: ContextVar[Optional[float]] = ContextVar('request_start_time', default=None)

# Performance thresholds (configurable)
SLOW_REQUEST_THRESHOLD_MS = 1000  # 1 second
SLOW_QUERY_THRESHOLD_MS = 500     # 500ms
MEMORY_WARNING_THRESHOLD_MB = 500  # 500MB
CPU_WARNING_THRESHOLD_PCT = 80    # 80%


class PerformanceMetrics:
    """
    Track and store performance metrics

    Features:
    - Request duration tracking
    - Endpoint-specific statistics
    - Slow query detection
    - Resource usage monitoring
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize performance metrics

        Args:
            max_history: Maximum number of metrics to keep in memory
        """
        self.max_history = max_history

        # Request metrics
        self.request_count = 0
        self.request_durations = deque(maxlen=max_history)
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0.0,
            'min_duration': float('inf'),
            'max_duration': 0.0,
            'errors': 0
        })

        # Database metrics
        self.query_count = 0
        self.query_durations = deque(maxlen=max_history)
        self.slow_queries = deque(maxlen=100)

        # WebSocket metrics
        self.websocket_connections = 0
        self.websocket_messages_sent = 0
        self.websocket_messages_received = 0
        self.websocket_latencies = deque(maxlen=max_history)

        # Resource metrics (sampled periodically)
        self.resource_samples = deque(maxlen=max_history)

        # Logging service
        self.logger = get_logging_service()

    def record_request(
        self,
        endpoint: str,
        method: str,
        duration: float,
        status_code: int,
        error: bool = False
    ):
        """
        Record request metrics

        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            duration: Request duration in seconds
            status_code: HTTP status code
            error: Whether request resulted in error
        """
        self.request_count += 1
        duration_ms = duration * 1000
        self.request_durations.append(duration_ms)

        # Update endpoint stats
        key = f"{method} {endpoint}"
        stats = self.endpoint_stats[key]
        stats['count'] += 1
        stats['total_duration'] += duration_ms
        stats['min_duration'] = min(stats['min_duration'], duration_ms)
        stats['max_duration'] = max(stats['max_duration'], duration_ms)
        if error:
            stats['errors'] += 1

        # Log slow requests
        if duration_ms > SLOW_REQUEST_THRESHOLD_MS:
            self.logger.performance(
                f"Slow request detected: {key} took {duration_ms:.2f}ms (status: {status_code})",
                extra_data={
                    'endpoint': endpoint,
                    'method': method,
                    'duration_ms': duration_ms,
                    'status_code': status_code,
                    'threshold_ms': SLOW_REQUEST_THRESHOLD_MS
                }
            )

    def record_query(
        self,
        query_type: str,
        duration: float,
        query_text: Optional[str] = None
    ):
        """
        Record database query metrics

        Args:
            query_type: Type of query (SELECT, INSERT, UPDATE, etc.)
            duration: Query duration in seconds
            query_text: SQL query text (optional, for slow query logging)
        """
        self.query_count += 1
        duration_ms = duration * 1000
        self.query_durations.append(duration_ms)

        # Log slow queries
        if duration_ms > SLOW_QUERY_THRESHOLD_MS:
            self.slow_queries.append({
                'query_type': query_type,
                'duration_ms': duration_ms,
                'query_text': query_text[:200] if query_text else None,
                'timestamp': datetime.now()
            })

            self.logger.performance(
                f"Slow query detected: {query_type} took {duration_ms:.2f}ms",
                extra_data={
                    'query_type': query_type,
                    'duration_ms': duration_ms,
                    'query_preview': query_text[:100] if query_text else None,
                    'threshold_ms': SLOW_QUERY_THRESHOLD_MS
                }
            )

    def record_websocket_connection(self, connected: bool):
        """
        Record WebSocket connection change

        Args:
            connected: True if connecting, False if disconnecting
        """
        if connected:
            self.websocket_connections += 1
        else:
            self.websocket_connections = max(0, self.websocket_connections - 1)

        self.logger.performance(
            f"WebSocket connection {'established' if connected else 'closed'}. "
            f"Active connections: {self.websocket_connections}"
        )

    def record_websocket_message(self, sent: bool, latency: Optional[float] = None):
        """
        Record WebSocket message

        Args:
            sent: True if message sent, False if received
            latency: Message latency in seconds (optional)
        """
        if sent:
            self.websocket_messages_sent += 1
        else:
            self.websocket_messages_received += 1

        if latency is not None:
            latency_ms = latency * 1000
            self.websocket_latencies.append(latency_ms)

            # Log high latency
            if latency_ms > 100:  # 100ms threshold
                self.logger.performance(
                    f"High WebSocket latency: {latency_ms:.2f}ms",
                    extra_data={'latency_ms': latency_ms}
                )

    def sample_resource_usage(self):
        """
        Sample current resource usage (memory, CPU, etc.)
        """
        try:
            process = psutil.Process()

            # Memory info
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB

            # CPU usage (percent)
            cpu_percent = process.cpu_percent(interval=0.1)

            # Disk I/O (if available)
            try:
                io_counters = process.io_counters()
                disk_read_mb = io_counters.read_bytes / (1024 * 1024)
                disk_write_mb = io_counters.write_bytes / (1024 * 1024)
            except (AttributeError, OSError):
                disk_read_mb = 0
                disk_write_mb = 0

            # Thread count
            num_threads = process.num_threads()

            sample = {
                'timestamp': datetime.now(),
                'memory_mb': memory_mb,
                'cpu_percent': cpu_percent,
                'disk_read_mb': disk_read_mb,
                'disk_write_mb': disk_write_mb,
                'num_threads': num_threads
            }

            self.resource_samples.append(sample)

            # Log warnings if thresholds exceeded
            if memory_mb > MEMORY_WARNING_THRESHOLD_MB:
                self.logger.warning(
                    f"High memory usage: {memory_mb:.2f}MB (threshold: {MEMORY_WARNING_THRESHOLD_MB}MB)",
                    log_type=LogType.PERFORMANCE,
                    extra_data={'memory_mb': memory_mb}
                )

            if cpu_percent > CPU_WARNING_THRESHOLD_PCT:
                self.logger.warning(
                    f"High CPU usage: {cpu_percent:.1f}% (threshold: {CPU_WARNING_THRESHOLD_PCT}%)",
                    log_type=LogType.PERFORMANCE,
                    extra_data={'cpu_percent': cpu_percent}
                )

            return sample

        except Exception as e:
            self.logger.error(f"Failed to sample resource usage: {e}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance statistics

        Returns:
            Dictionary with performance statistics
        """
        stats = {
            'requests': {
                'total_count': self.request_count,
                'avg_duration_ms': sum(self.request_durations) / len(self.request_durations) if self.request_durations else 0,
                'min_duration_ms': min(self.request_durations) if self.request_durations else 0,
                'max_duration_ms': max(self.request_durations) if self.request_durations else 0,
                'slow_requests': sum(1 for d in self.request_durations if d > SLOW_REQUEST_THRESHOLD_MS)
            },
            'endpoints': {},
            'queries': {
                'total_count': self.query_count,
                'avg_duration_ms': sum(self.query_durations) / len(self.query_durations) if self.query_durations else 0,
                'slow_queries': len(self.slow_queries)
            },
            'websockets': {
                'active_connections': self.websocket_connections,
                'messages_sent': self.websocket_messages_sent,
                'messages_received': self.websocket_messages_received,
                'avg_latency_ms': sum(self.websocket_latencies) / len(self.websocket_latencies) if self.websocket_latencies else 0
            },
            'resources': {}
        }

        # Calculate endpoint statistics
        for endpoint, data in self.endpoint_stats.items():
            if data['count'] > 0:
                stats['endpoints'][endpoint] = {
                    'count': data['count'],
                    'avg_duration_ms': data['total_duration'] / data['count'],
                    'min_duration_ms': data['min_duration'],
                    'max_duration_ms': data['max_duration'],
                    'error_rate': data['errors'] / data['count'] if data['count'] > 0 else 0
                }

        # Calculate resource statistics
        if self.resource_samples:
            recent_samples = list(self.resource_samples)[-10:]  # Last 10 samples
            stats['resources'] = {
                'avg_memory_mb': sum(s['memory_mb'] for s in recent_samples) / len(recent_samples),
                'avg_cpu_percent': sum(s['cpu_percent'] for s in recent_samples) / len(recent_samples),
                'num_threads': recent_samples[-1]['num_threads']
            }

        return stats

    def reset(self):
        """Reset all metrics"""
        self.__init__(max_history=self.max_history)


# Global performance metrics instance
_performance_metrics: Optional[PerformanceMetrics] = None


def get_performance_metrics() -> PerformanceMetrics:
    """
    Get global performance metrics instance

    Returns:
        Global PerformanceMetrics instance
    """
    global _performance_metrics

    if _performance_metrics is None:
        _performance_metrics = PerformanceMetrics()

    return _performance_metrics


# Context managers and decorators
@contextmanager
def track_request_time(endpoint: str, method: str = "GET"):
    """
    Context manager to track request execution time

    Usage:
        with track_request_time("/api/v1/events", "GET"):
            # request handling code
            pass

    Args:
        endpoint: API endpoint path
        method: HTTP method
    """
    metrics = get_performance_metrics()
    start_time = time.time()
    _request_start_time.set(start_time)
    error = False
    status_code = 200

    try:
        yield
    except Exception as e:
        error = True
        status_code = 500
        raise
    finally:
        duration = time.time() - start_time
        metrics.record_request(endpoint, method, duration, status_code, error)
        _request_start_time.set(None)


@contextmanager
def track_query_time(query_type: str, query_text: Optional[str] = None):
    """
    Context manager to track database query execution time

    Usage:
        with track_query_time("SELECT", "SELECT * FROM users"):
            # query execution
            result = session.execute(...)

    Args:
        query_type: Type of query (SELECT, INSERT, etc.)
        query_text: SQL query text (optional)
    """
    metrics = get_performance_metrics()
    start_time = time.time()

    try:
        yield
    finally:
        duration = time.time() - start_time
        metrics.record_query(query_type, duration, query_text)


def monitor_performance(endpoint: Optional[str] = None):
    """
    Decorator to monitor function performance

    Usage:
        @monitor_performance("/api/v1/events")
        async def get_events():
            ...

    Args:
        endpoint: Endpoint path (uses function name if not provided)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal endpoint
            if endpoint is None:
                endpoint = func.__name__

            with track_request_time(endpoint, "FUNC"):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal endpoint
            if endpoint is None:
                endpoint = func.__name__

            with track_request_time(endpoint, "FUNC"):
                return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Background resource monitoring
class ResourceMonitor:
    """
    Background resource monitoring service

    Periodically samples resource usage and logs warnings.
    """

    def __init__(self, interval_seconds: int = 60):
        """
        Initialize resource monitor

        Args:
            interval_seconds: Sampling interval in seconds
        """
        self.interval_seconds = interval_seconds
        self.metrics = get_performance_metrics()
        self.running = False
        self.logger = get_logging_service()

    async def start(self):
        """Start background monitoring"""
        import asyncio

        self.running = True
        self.logger.info("Resource monitoring started", log_type=LogType.PERFORMANCE)

        while self.running:
            try:
                self.metrics.sample_resource_usage()
                await asyncio.sleep(self.interval_seconds)
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}", log_type=LogType.PERFORMANCE)
                await asyncio.sleep(self.interval_seconds)

    def stop(self):
        """Stop background monitoring"""
        self.running = False
        self.logger.info("Resource monitoring stopped", log_type=LogType.PERFORMANCE)


# Utility functions
def log_performance_summary():
    """Log performance summary statistics"""
    metrics = get_performance_metrics()
    stats = metrics.get_statistics()
    logger = get_logging_service()

    logger.info(
        "Performance Summary",
        log_type=LogType.PERFORMANCE,
        extra_data=stats
    )

    # Log summary to console
    print("\n" + "="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)
    print(f"\nRequests:")
    print(f"  Total: {stats['requests']['total_count']}")
    print(f"  Avg Duration: {stats['requests']['avg_duration_ms']:.2f}ms")
    print(f"  Slow Requests: {stats['requests']['slow_requests']}")

    print(f"\nDatabase:")
    print(f"  Total Queries: {stats['queries']['total_count']}")
    print(f"  Avg Duration: {stats['queries']['avg_duration_ms']:.2f}ms")
    print(f"  Slow Queries: {stats['queries']['slow_queries']}")

    print(f"\nWebSockets:")
    print(f"  Active Connections: {stats['websockets']['active_connections']}")
    print(f"  Messages Sent: {stats['websockets']['messages_sent']}")
    print(f"  Messages Received: {stats['websockets']['messages_received']}")

    if stats['resources']:
        print(f"\nResources:")
        print(f"  Avg Memory: {stats['resources']['avg_memory_mb']:.2f}MB")
        print(f"  Avg CPU: {stats['resources']['avg_cpu_percent']:.1f}%")
        print(f"  Threads: {stats['resources']['num_threads']}")

    print("="*70 + "\n")

    return stats
