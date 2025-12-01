"""
Flask Web Server - REST API für Dokumentenverwaltung
Modular refactored mit Blueprints
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import yaml

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Import eigener Module
import sys
sys.path.append(str(Path(__file__).parent.parent))

from app.database import Database


def init_app(config_path: str = 'config.yaml') -> None:
    """
    Initialisiert App mit Konfiguration
    
    Args:
        config_path: Pfad zur Konfigurationsdatei
        
    Raises:
        FileNotFoundError: Wenn Config-Datei nicht gefunden
        yaml.YAMLError: Wenn Config ungültig
    """
    global db, search_engine, data_extractor, config
    
    # Lade Config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Init Auth
    init_auth(app, config_path)
    
    # Initialisiere Komponenten
    db = Database(config_path)
    search_engine = SearchEngine()
    data_extractor = DataExtractor(config_path)
    
    # Indexiere Dokumente
    _reindex_search()
    
    # Initiale Metriken
    try:
        from app.metrics import DB_DOCUMENT_COUNT
        if db:
            stats = db.get_overview_stats()
            DB_DOCUMENT_COUNT.set(stats.get('total_documents', 0))
    except Exception as e:
        logger.warning(f"Could not set initial metrics: {e}")
    
    logger.info("✅ App initialisiert")


def _reindex_search():
    """Reindexiert alle Dokumente im Search-Engine"""
    global db, search_engine
    
    if not db or not search_engine:
        return
    
    try:
        documents = db.search_documents(limit=10000)
        search_engine.index_documents(documents)
        logger.info(f"✅ {len(documents)} Dokumente indexiert")
    except Exception as e:
        logger.error(f"Fehler beim Indexieren: {e}")


def init_scheduler() -> BackgroundScheduler:
    """
    Initialisiert Hintergrund-Scheduler für Email-Polling
    
    Returns:
        BackgroundScheduler-Instanz
    """
    scheduler = BackgroundScheduler()
    
    try:
        # Email-Polling Task
        email_receiver = EmailReceiver()
        if email_receiver.email_config.get('enabled'):
            interval = email_receiver.email_config.get('poll_interval', 300)
            scheduler.add_job(
                func=email_receiver.check_new_emails,
                trigger="interval",
                seconds=interval,
                id='email_polling'
            )
            logger.info(f"📧 Email-Polling aktiviert (alle {interval}s)")
    
    except Exception as e:
        logger.error(f"Scheduler-Error: {e}")
    
    scheduler.start()
    return scheduler


# Register Blueprints
from app.blueprints import register_blueprints
register_blueprints(app)

# Register existing blueprints
app.register_blueprint(upload_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(health_bp)


# Metrics Endpoint
@app.route('/metrics')
def metrics():
    """Prometheus-kompatible Metriken"""
    from app.metrics import MetricsManager
    return MetricsManager.get_metrics_response()


# Static Files
@app.route('/')
def index():
    """Hauptseite"""
    return send_from_directory('static', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Statische Dateien ausliefern"""
    return send_from_directory('static', path)


# Error Handlers
@app.errorhandler(404)
def not_found(error):
    """404 Handler"""
    from flask import jsonify
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 Handler"""
    from flask import jsonify
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


def run_server(host: str = '0.0.0.0', port: int = 5001, debug: bool = False):
    """
    Startet den Flask-Server
    
    Args:
        host: Host-Adresse
        port: Port
        debug: Debug-Modus
    """
    # Initialisiere App
    init_app()
    
    # Starte Scheduler
    scheduler = init_scheduler()
    
    # Starte Server
    try:
        logger.info(f"🚀 Server läuft auf http://{host}:{port}")
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        logger.info("⏹️  Server gestoppt")
        scheduler.shutdown()


# === Request/Response Middleware ===

@app.before_request
def before_request_handler():
    """Track request start time"""
    from flask import request
    request.start_time = time.time()


@app.after_request
def after_request_handler(response):
    """Add security headers and log requests"""
    from flask import request
    
    # Add security headers
    response = add_security_headers(response)
    
    # Log request
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        log_request(request, response, duration)
    
    return response


# === Main ===

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='OrganisationsAI Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host address')
    parser.add_argument('--port', type=int, default=5001, help='Port number')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, debug=args.debug)
