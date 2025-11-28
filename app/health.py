"""
Health Check - System Status Monitoring
"""

from flask import Blueprint, jsonify
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health_check():
    """
    System Health Check Endpoint
    
    Returns:
        JSON mit Status aller Systemkomponenten
    """
    checks = {
        'database': check_database(),
        'disk_space': check_disk_space(),
        'ollama': check_ollama(),
        'scanner': check_scanner()
    }
    
    # Overall status
    all_healthy = all(checks.values())
    status = 'healthy' if all_healthy else 'degraded'
    
    response = {
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'checks': checks
    }
    
    return jsonify(response), 200 if all_healthy else 503


def check_database():
    """Prüft Datenbank-Verbindung"""
    try:
        from app.database import Database
        db = Database()
        stats = db.get_statistics()
        return {
            'status': 'ok',
            'document_count': stats.get('total_documents', 0)
        }
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return {'status': 'failed', 'error': str(e)}


def check_disk_space():
    """Prüft verfügbaren Speicherplatz"""
    try:
        import psutil
        
        # Check /mnt/documents
        if os.path.exists('/mnt/documents'):
            usage = psutil.disk_usage('/mnt/documents')
        else:
            usage = psutil.disk_usage('/')
        
        percent_used = usage.percent
        free_gb = usage.free / (1024**3)
        
        status = 'ok' if percent_used < 90 else 'warning'
        
        return {
            'status': status,
            'percent_used': percent_used,
            'free_gb': round(free_gb, 2)
        }
    except Exception as e:
        logger.error(f"Disk space check failed: {e}")
        return {'status': 'unknown', 'error': str(e)}


def check_ollama():
    """Prüft Ollama-Verfügbarkeit"""
    try:
        from app.ollama_client import OllamaClient
        client = OllamaClient()
        available = client.is_available()
        
        return {
            'status': 'ok' if available else 'unavailable',
            'model': client.config.get('model', 'unknown')
        }
    except Exception as e:
        logger.warning(f"Ollama check failed: {e}")
        return {'status': 'unavailable', 'error': str(e)}


def check_scanner():
    """Prüft Scanner-Verfügbarkeit"""
    try:
        import subprocess
        result = subprocess.run(
            ['scanimage', '-L'],
            capture_output=True,
            timeout=5,
            text=True
        )
        
        if result.returncode == 0:
            devices = 'scanner' in result.stdout.lower()
            return {
                'status': 'ok' if devices else 'no_devices',
                'output': result.stdout[:200]
            }
        else:
            return {'status': 'failed', 'error': result.stderr[:200]}
            
    except subprocess.TimeoutExpired:
        return {'status': 'timeout'}
    except FileNotFoundError:
        return {'status': 'not_installed'}
    except Exception as e:
        logger.warning(f"Scanner check failed: {e}")
        return {'status': 'error', 'error': str(e)}
