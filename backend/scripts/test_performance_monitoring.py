"""
Test script for Phase 6 Task 6.3 - Performance Monitoring

Tests:
1. Request tracking
2. Query tracking
3. WebSocket metrics
4. Resource monitoring
5. Performance decorators
6. Statistics generation
"""

import os
import sys
import time
import asyncio

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.performance_monitoring import (
    PerformanceMetrics,
    get_performance_metrics,
    track_request_time,
    track_query_time,
    monitor_performance,
    log_performance_summary,
    ResourceMonitor
)

# Test markers
OK = "[OK]"
FAIL = "[FAIL]"
INFO = "[INFO]"

def print_section(title):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}\n")

def test_request_tracking():
    """Test 1: Request tracking"""
    print_section("Test 1: Request Tracking")

    metrics = PerformanceMetrics()

    # Simulate requests
    metrics.record_request("/api/v1/events", "GET", 0.1, 200)
    metrics.record_request("/api/v1/users", "POST", 0.05, 201)
    metrics.record_request("/api/v1/events", "GET", 0.15, 200)
    metrics.record_request("/api/v1/events", "GET", 2.0, 200)  # Slow request

    print(f"{INFO} Recorded 4 requests (1 slow)")

    stats = metrics.get_statistics()
    print(f"{INFO} Total requests: {stats['requests']['total_count']}")
    print(f"{INFO} Average duration: {stats['requests']['avg_duration_ms']:.2f}ms")
    print(f"{INFO} Slow requests: {stats['requests']['slow_requests']}")

    # Check results
    if stats['requests']['total_count'] == 4:
        print(f"{OK} Request count correct")
    else:
        print(f"{FAIL} Request count incorrect")
        return False

    if stats['requests']['slow_requests'] == 1:
        print(f"{OK} Slow request detection working")
        return True
    else:
        print(f"{FAIL} Slow request detection failed")
        return False

def test_query_tracking():
    """Test 2: Database query tracking"""
    print_section("Test 2: Query Tracking")

    metrics = PerformanceMetrics()

    # Simulate queries
    metrics.record_query("SELECT", 0.01, "SELECT * FROM users")
    metrics.record_query("INSERT", 0.02, "INSERT INTO events ...")
    metrics.record_query("SELECT", 0.6, "SELECT * FROM events JOIN ...")  # Slow query

    print(f"{INFO} Recorded 3 queries (1 slow)")

    stats = metrics.get_statistics()
    print(f"{INFO} Total queries: {stats['queries']['total_count']}")
    print(f"{INFO} Average duration: {stats['queries']['avg_duration_ms']:.2f}ms")
    print(f"{INFO} Slow queries: {stats['queries']['slow_queries']}")

    if stats['queries']['total_count'] == 3 and stats['queries']['slow_queries'] == 1:
        print(f"{OK} Query tracking working correctly")
        return True
    else:
        print(f"{FAIL} Query tracking failed")
        return False

def test_websocket_metrics():
    """Test 3: WebSocket metrics"""
    print_section("Test 3: WebSocket Metrics")

    metrics = PerformanceMetrics()

    # Simulate WebSocket connections
    metrics.record_websocket_connection(True)
    metrics.record_websocket_connection(True)
    print(f"{INFO} Simulated 2 connections")

    # Simulate messages
    metrics.record_websocket_message(sent=True, latency=0.05)
    metrics.record_websocket_message(sent=True, latency=0.02)
    metrics.record_websocket_message(sent=False)  # Received
    print(f"{INFO} Simulated 3 messages")

    stats = metrics.get_statistics()
    print(f"{INFO} Active connections: {stats['websockets']['active_connections']}")
    print(f"{INFO} Messages sent: {stats['websockets']['messages_sent']}")
    print(f"{INFO} Messages received: {stats['websockets']['messages_received']}")
    print(f"{INFO} Avg latency: {stats['websockets']['avg_latency_ms']:.2f}ms")

    if (stats['websockets']['active_connections'] == 2 and
        stats['websockets']['messages_sent'] == 2 and
        stats['websockets']['messages_received'] == 1):
        print(f"{OK} WebSocket metrics working correctly")
        return True
    else:
        print(f"{FAIL} WebSocket metrics failed")
        return False

def test_resource_monitoring():
    """Test 4: Resource monitoring"""
    print_section("Test 4: Resource Monitoring")

    metrics = PerformanceMetrics()

    # Sample resource usage
    sample = metrics.sample_resource_usage()

    if sample:
        print(f"{INFO} Memory: {sample['memory_mb']:.2f}MB")
        print(f"{INFO} CPU: {sample['cpu_percent']:.1f}%")
        print(f"{INFO} Threads: {sample['num_threads']}")
        print(f"{INFO} Disk Read: {sample['disk_read_mb']:.2f}MB")
        print(f"{INFO} Disk Write: {sample['disk_write_mb']:.2f}MB")
        print(f"{OK} Resource monitoring working")
        return True
    else:
        print(f"{FAIL} Resource monitoring failed")
        return False

def test_context_managers():
    """Test 5: Context managers"""
    print_section("Test 5: Context Managers")

    metrics = get_performance_metrics()
    metrics.reset()

    # Test request tracking
    with track_request_time("/api/v1/test", "GET"):
        time.sleep(0.05)

    print(f"{INFO} Tracked request with context manager")

    # Test query tracking
    with track_query_time("SELECT", "SELECT * FROM test"):
        time.sleep(0.02)

    print(f"{INFO} Tracked query with context manager")

    stats = metrics.get_statistics()

    if stats['requests']['total_count'] == 1 and stats['queries']['total_count'] == 1:
        print(f"{OK} Context managers working correctly")
        return True
    else:
        print(f"{FAIL} Context managers failed")
        return False

def test_decorators():
    """Test 6: Performance decorators"""
    print_section("Test 6: Performance Decorators")

    metrics = get_performance_metrics()
    metrics.reset()

    # Test synchronous decorator
    @monitor_performance("/api/v1/sync_test")
    def sync_function():
        time.sleep(0.03)
        return "done"

    result = sync_function()
    print(f"{INFO} Sync function result: {result}")

    # Test async decorator
    @monitor_performance("/api/v1/async_test")
    async def async_function():
        await asyncio.sleep(0.02)
        return "done"

    result = asyncio.run(async_function())
    print(f"{INFO} Async function result: {result}")

    stats = metrics.get_statistics()

    if stats['requests']['total_count'] == 2:
        print(f"{OK} Decorators working correctly")
        return True
    else:
        print(f"{FAIL} Decorators failed")
        return False

def test_endpoint_statistics():
    """Test 7: Endpoint-specific statistics"""
    print_section("Test 7: Endpoint Statistics")

    metrics = PerformanceMetrics()

    # Record multiple requests to same endpoint
    endpoint = "/api/v1/events"
    for i in range(5):
        duration = 0.05 + (i * 0.01)  # Varying durations
        metrics.record_request(endpoint, "GET", duration, 200)

    # One error
    metrics.record_request(endpoint, "GET", 0.1, 500, error=True)

    stats = metrics.get_statistics()

    if 'GET /api/v1/events' in stats['endpoints']:
        endpoint_stats = stats['endpoints']['GET /api/v1/events']
        print(f"{INFO} Endpoint count: {endpoint_stats['count']}")
        print(f"{INFO} Avg duration: {endpoint_stats['avg_duration_ms']:.2f}ms")
        print(f"{INFO} Min duration: {endpoint_stats['min_duration_ms']:.2f}ms")
        print(f"{INFO} Max duration: {endpoint_stats['max_duration_ms']:.2f}ms")
        print(f"{INFO} Error rate: {endpoint_stats['error_rate']:.2%}")

        if endpoint_stats['count'] == 6 and endpoint_stats['error_rate'] > 0:
            print(f"{OK} Endpoint statistics working correctly")
            return True
        else:
            print(f"{FAIL} Endpoint statistics incorrect")
            return False
    else:
        print(f"{FAIL} Endpoint statistics not found")
        return False

def test_performance_summary():
    """Test 8: Performance summary"""
    print_section("Test 8: Performance Summary")

    metrics = get_performance_metrics()
    metrics.reset()

    # Generate some activity
    metrics.record_request("/api/v1/events", "GET", 0.1, 200)
    metrics.record_request("/api/v1/users", "POST", 0.05, 201)
    metrics.record_query("SELECT", 0.02)
    metrics.record_websocket_connection(True)
    metrics.sample_resource_usage()

    # Log summary
    stats = log_performance_summary()

    if stats['requests']['total_count'] > 0:
        print(f"{OK} Performance summary generated")
        return True
    else:
        print(f"{FAIL} Performance summary failed")
        return False

def run_all_tests():
    """Run all performance monitoring tests"""
    print("\n" + "="*70)
    print("PHASE 6 TASK 6.3 - PERFORMANCE MONITORING TEST SUITE")
    print("="*70)

    tests = [
        ("Request Tracking", test_request_tracking),
        ("Query Tracking", test_query_tracking),
        ("WebSocket Metrics", test_websocket_metrics),
        ("Resource Monitoring", test_resource_monitoring),
        ("Context Managers", test_context_managers),
        ("Decorators", test_decorators),
        ("Endpoint Statistics", test_endpoint_statistics),
        ("Performance Summary", test_performance_summary),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"{FAIL} Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = OK if result else FAIL
        print(f"{status} {name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print(f"\n{OK} All performance monitoring tests passed!")
        print("\nPerformance Features Verified:")
        print("  [OK] Request duration tracking")
        print("  [OK] Database query metrics")
        print("  [OK] WebSocket metrics")
        print("  [OK] Resource monitoring (CPU, memory, disk)")
        print("  [OK] Endpoint-specific statistics")
        print("  [OK] Context managers and decorators")
        print("  [OK] Slow request/query detection")
    else:
        print(f"\n{FAIL} Some tests failed. Please review.")

    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
