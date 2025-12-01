"""
Monitoring Blueprint
API-Endpoints für Health-Checks und System-Status
"""
from flask import Blueprint, jsonify
import logging
import psutil
import time
from typing import Dict, Any

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/monitoring')
logger = logging.getLogger(__name__)

@monitoring_bp.route('/health', methods=['GET'])
def health_check() -> tuple[Dict[str, Any], int]:
    """
    GET /api/monitoring/health
    Detaillierter Health-Check aller Komponenten
    """
    status = {
        'status': 'ok',
        'timestamp': time.time(),
        'components': {}
    }
    
    # Check Database
    try:
        from app.database import Database
        db = Database()
        # Simple query to check connection
        db.get_overview_stats()
        db.close()
        status['components']['database'] = {'status': 'ok'}
    except Exception as e:
        status['status'] = 'degraded'
        status['components']['database'] = {'status': 'error', 'message': str(e)}
    
    # Check Ollama
    try:
        from app.ollama_client import OllamaClient
        ollama = OllamaClient()
        status['components']['ollama'] = {
            'status': 'ok' if ollama.available else 'unavailable',
            'url': ollama.url
        }
    except Exception as e:
        status['components']['ollama'] = {'status': 'error', 'message': str(e)}

    # Check Redis
    try:
        from app.redis_client import RedisClient
        redis_client = RedisClient()
        status['components']['redis'] = {
            'status': 'ok' if redis_client.enabled else 'unavailable',
            'host': redis_client.host
        }
    except Exception as e:
        status['components']['redis'] = {'status': 'error', 'message': str(e)}
        
    # Check Disk Space
    try:
        disk = psutil.disk_usage('/')
        status['components']['disk'] = {
            'status': 'ok' if disk.percent < 90 else 'warning',
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }
    except Exception as e:
        status['components']['disk'] = {'status': 'error', 'message': str(e)}
        
    return jsonify(status), 200 if status['status'] == 'ok' else 503

@monitoring_bp.route('/system', methods=['GET'])
def system_stats() -> tuple[Dict[str, Any], int]:
    """
    GET /api/monitoring/system
    System-Ressourcen (CPU, RAM)
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        stats = {
            'cpu': {
                'percent': cpu_percent,
                'count': psutil.cpu_count()
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent
            },
            'swap': {
                'total': swap.total,
                'used': swap.used,
                'percent': swap.percent
            },
            'boot_time': psutil.boot_time()
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return jsonify({'error': str(e)}), 500
