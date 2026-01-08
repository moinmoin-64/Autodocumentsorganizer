"""
Monitoring Module
Prometheus Metrics & System Stats
"""
import time
import psutil
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from flask import Response, request
import logging

logger = logging.getLogger(__name__)

# Metrics Definitions - with duplicate check
try:
    HTTP_REQUESTS_TOTAL = Counter(
        'http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status']
    )
except ValueError:
    HTTP_REQUESTS_TOTAL = REGISTRY._names_to_collectors.get('http_requests_total')

try:
    HTTP_REQUEST_DURATION_SECONDS = Histogram(
        'http_request_duration_seconds',
        'HTTP request duration in seconds',
        ['method', 'endpoint']
    )
except ValueError:
    HTTP_REQUEST_DURATION_SECONDS = REGISTRY._names_to_collectors.get('http_request_duration_seconds')

try:
    DB_QUERY_DURATION_SECONDS = Histogram(
        'db_query_duration_seconds',
        'Database query duration in seconds',
        ['operation', 'table']
    )
except ValueError:
    DB_QUERY_DURATION_SECONDS = REGISTRY._names_to_collectors.get('db_query_duration_seconds')

try:
    SYSTEM_MEMORY_USAGE_BYTES = Gauge(
        'system_memory_usage_bytes',
        'System memory usage in bytes'
    )
except ValueError:
    SYSTEM_MEMORY_USAGE_BYTES = REGISTRY._names_to_collectors.get('system_memory_usage_bytes')

try:
    SYSTEM_CPU_USAGE_PERCENT = Gauge(
        'system_cpu_usage_percent',
        'System CPU usage percent'
    )
except ValueError:
    SYSTEM_CPU_USAGE_PERCENT = REGISTRY._names_to_collectors.get('system_cpu_usage_percent')

# Helper to update system metrics
def update_system_metrics():
    try:
        mem = psutil.virtual_memory()
        SYSTEM_MEMORY_USAGE_BYTES.set(mem.used)
        SYSTEM_CPU_USAGE_PERCENT.set(psutil.cpu_percent())
    except Exception as e:
        logger.error(f"Error updating system metrics: {e}")

def get_metrics():
    """Returns Prometheus metrics response"""
    update_system_metrics()
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

def record_request_metrics(response):
    """Middleware to record request metrics"""
    try:
        # Skip metrics endpoint itself to avoid noise
        if request.path == '/metrics':
            return response
            
        endpoint = request.endpoint or 'unknown'
        status = str(response.status_code)
        method = request.method
        
        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        # Duration is tracked via before_request (start time) and after_request (end time)
        # We need to store start time in g or request context
        # This is handled in server.py integration
        
    except Exception as e:
        logger.error(f"Error recording metrics: {e}")
        
    return response
