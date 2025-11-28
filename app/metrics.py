"""
Prometheus Metrics - System Monitoring
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
import psutil
from functools import wraps
from flask import Response

# --- Metrics Definitions ---

# Counters
DOCUMENT_PROCESSED_TOTAL = Counter(
    'document_processed_total',
    'Total number of processed documents',
    ['status', 'category']
)

OCR_REQUESTS_TOTAL = Counter(
    'ocr_requests_total',
    'Total number of OCR requests',
    ['engine', 'language']
)

LLM_REQUESTS_TOTAL = Counter(
    'llm_requests_total',
    'Total number of LLM requests',
    ['model', 'status']
)

# Histograms (Latency)
PROCESSING_DURATION_SECONDS = Histogram(
    'processing_duration_seconds',
    'Time spent processing a document',
    ['stage'],
    buckets=(1, 5, 10, 30, 60, 120, 300)
)

OCR_DURATION_SECONDS = Histogram(
    'ocr_duration_seconds',
    'Time spent on OCR',
    buckets=(0.5, 1, 2.5, 5, 10, 20, 40)
)

LLM_DURATION_SECONDS = Histogram(
    'llm_duration_seconds',
    'Time spent on LLM inference',
    buckets=(0.5, 1, 2, 5, 10, 20, 40)
)

# Gauges (Current State)
SYSTEM_MEMORY_USAGE_BYTES = Gauge(
    'system_memory_usage_bytes',
    'Current memory usage in bytes'
)

SYSTEM_CPU_USAGE_PERCENT = Gauge(
    'system_cpu_usage_percent',
    'Current CPU usage percent'
)

DB_DOCUMENT_COUNT = Gauge(
    'db_document_count',
    'Total documents in database'
)


class MetricsManager:
    """Verwaltet Prometheus Metriken"""
    
    @staticmethod
    def update_system_metrics():
        """Aktualisiert System-Metriken (CPU/RAM)"""
        mem = psutil.virtual_memory()
        SYSTEM_MEMORY_USAGE_BYTES.set(mem.used)
        SYSTEM_CPU_USAGE_PERCENT.set(psutil.cpu_percent())

    @staticmethod
    def track_time(metric, **labels):
        """Decorator für Zeitmessung"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    metric.labels(**labels).observe(duration)
                    return result
                except Exception as e:
                    # Auch bei Fehler Zeit messen
                    duration = time.time() - start_time
                    metric.labels(**labels).observe(duration)
                    raise e
            return wrapper
        return decorator

    @staticmethod
    def get_metrics_response():
        """Gibt Metriken für Flask Response zurück"""
        MetricsManager.update_system_metrics()
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
