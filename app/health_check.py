"""
Health Check & System Monitoring
Comprehensive system status monitoring
"""

from flask import Blueprint, jsonify
from datetime import datetime, timedelta
from functools import wraps
import psutil
import logging
import os

from app.database import db
from app.redis_client import redis_client

logger = logging.getLogger(__name__)
health_bp = Blueprint('health', __name__, url_prefix='/api/health')


class HealthCheck:
    """System health status"""

    @staticmethod
    def get_database_status():
        """Check database connectivity"""
        try:
            result = db.session.execute('SELECT 1')
            return {
                'status': 'healthy',
                'type': 'PostgreSQL/SQLite',
                'responseTime': 0
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    @staticmethod
    def get_redis_status():
        """Check Redis connectivity"""
        try:
            redis_client.ping()
            return {
                'status': 'healthy',
                'type': 'Redis',
                'responseTime': 0
            }
        except Exception as e:
            logger.warning(f"Redis health check failed: {str(e)}")
            return {
                'status': 'degraded',
                'error': str(e)
            }

    @staticmethod
    def get_system_resources():
        """Get system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                'cpu': {
                    'percent': cpu_percent,
                    'cores': psutil.cpu_count()
                },
                'memory': {
                    'percent': memory.percent,
                    'used': memory.used // (1024 * 1024),  # MB
                    'total': memory.total // (1024 * 1024)  # MB
                },
                'disk': {
                    'percent': disk.percent,
                    'used': disk.used // (1024 * 1024 * 1024),  # GB
                    'total': disk.total // (1024 * 1024 * 1024)  # GB
                }
            }
        except Exception as e:
            logger.error(f"System resources check failed: {str(e)}")
            return {
                'status': 'unavailable',
                'error': str(e)
            }

    @staticmethod
    def get_process_status():
        """Get current process status"""
        try:
            process = psutil.Process()
            
            return {
                'pid': process.pid,
                'memory': {
                    'rss': process.memory_info().rss // (1024 * 1024),  # MB
                    'vms': process.memory_info().vms // (1024 * 1024)  # MB
                },
                'cpu_percent': process.cpu_percent(interval=1),
                'num_threads': process.num_threads(),
                'status': process.status()
            }
        except Exception as e:
            logger.error(f"Process status check failed: {str(e)}")
            return {
                'status': 'unavailable',
                'error': str(e)
            }


@health_bp.route('', methods=['GET'])
def health_check():
    """
    System health check
    GET /api/health
    """
    try:
        db_status = HealthCheck.get_database_status()
        redis_status = HealthCheck.get_redis_status()
        resources = HealthCheck.get_system_resources()
        process = HealthCheck.get_process_status()

        # Overall status
        critical_services = [db_status['status']]
        overall_status = 'healthy'

        if 'unhealthy' in critical_services:
            overall_status = 'unhealthy'
        elif redis_status['status'] == 'degraded':
            overall_status = 'degraded'

        # Check resource thresholds
        if resources.get('cpu', {}).get('percent', 0) > 80:
            overall_status = 'degraded'
        if resources.get('memory', {}).get('percent', 0) > 85:
            overall_status = 'degraded'
        if resources.get('disk', {}).get('percent', 0) > 90:
            overall_status = 'degraded'

        return jsonify({
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': 'N/A',  # Can be calculated from start time
            'services': {
                'database': db_status,
                'cache': redis_status
            },
            'resources': resources,
            'process': process
        }), 200

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@health_bp.route('/status', methods=['GET'])
def status():
    """
    Simplified status endpoint
    GET /api/health/status
    """
    try:
        db_status = HealthCheck.get_database_status()
        redis_status = HealthCheck.get_redis_status()

        is_healthy = (
            db_status['status'] == 'healthy' and
            redis_status['status'] != 'unhealthy'
        )

        return jsonify({
            'healthy': is_healthy,
            'timestamp': datetime.utcnow().isoformat()
        }), 200 if is_healthy else 503

    except Exception as e:
        return jsonify({
            'healthy': False,
            'error': str(e)
        }), 503


@health_bp.route('/database', methods=['GET'])
def database_health():
    """
    Database health check
    GET /api/health/database
    """
    status = HealthCheck.get_database_status()
    return jsonify(status), 200 if status['status'] == 'healthy' else 500


@health_bp.route('/cache', methods=['GET'])
def cache_health():
    """
    Cache (Redis) health check
    GET /api/health/cache
    """
    status = HealthCheck.get_redis_status()
    return jsonify(status), 200 if status['status'] == 'healthy' else 503


@health_bp.route('/resources', methods=['GET'])
def resources():
    """
    System resources
    GET /api/health/resources
    """
    return jsonify(HealthCheck.get_system_resources()), 200


@health_bp.route('/ready', methods=['GET'])
def readiness_probe():
    """
    Kubernetes readiness probe
    GET /api/health/ready
    Returns 200 if ready to serve traffic
    """
    try:
        # Check database
        HealthCheck.get_database_status()
        
        return jsonify({
            'ready': True,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Readiness probe failed: {str(e)}")
        return jsonify({
            'ready': False,
            'error': str(e)
        }), 503


@health_bp.route('/live', methods=['GET'])
def liveness_probe():
    """
    Kubernetes liveness probe
    GET /api/health/live
    Returns 200 if process is alive
    """
    try:
        # Simple check - if we can respond, we're alive
        return jsonify({
            'alive': True,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            'alive': False
        }), 500


class HealthMonitor:
    """Continuous health monitoring"""

    def __init__(self, check_interval=60):
        self.check_interval = check_interval
        self.history = {
            'cpu': [],
            'memory': [],
            'disk': [],
            'database': [],
            'cache': []
        }
        self.max_history = 1440  # 24 hours of minute-level data

    def check(self):
        """Run health checks and record"""
        try:
            resources = HealthCheck.get_system_resources()
            db_status = HealthCheck.get_database_status()
            cache_status = HealthCheck.get_redis_status()

            now = datetime.utcnow()

            # Record metrics
            self.history['cpu'].append({
                'timestamp': now,
                'value': resources['cpu']['percent']
            })

            self.history['memory'].append({
                'timestamp': now,
                'value': resources['memory']['percent']
            })

            self.history['disk'].append({
                'timestamp': now,
                'value': resources['disk']['percent']
            })

            self.history['database'].append({
                'timestamp': now,
                'status': db_status['status']
            })

            self.history['cache'].append({
                'timestamp': now,
                'status': cache_status['status']
            })

            # Trim history
            for key in self.history:
                if len(self.history[key]) > self.max_history:
                    self.history[key] = self.history[key][-self.max_history:]

        except Exception as e:
            logger.error(f"Health monitor check failed: {str(e)}")

    def get_trends(self, metric='memory', hours=1):
        """Get metric trends"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            entry for entry in self.history.get(metric, [])
            if entry['timestamp'] >= cutoff
        ]


# Global health monitor
health_monitor = HealthMonitor()
