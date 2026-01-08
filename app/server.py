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
import time

from flask import Flask, send_from_directory
from flask_wtf.csrf import CSRFProtect

# Import eigener Module
import sys
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__) # Globalen Logger definieren

from app.database import Database
from app.search_engine import SearchEngine
from app.data_extractor import DataExtractor
from app.exporters import DataExporter
from app.email_receiver import EmailReceiver
from app.upload_handler import upload_bp
from app.auth import auth_bp, init_auth
from app.health import health_bp
from app.logging_config import setup_logging, log_request
from app.monitoring import record_request_metrics
from app.security_config import setup_security, add_security_headers

from apscheduler.schedulers.background import BackgroundScheduler

# Load environment variables
load_dotenv()

# Globale Objekte (mit Type Hints)
db: Optional[Database] = None
search_engine: Optional[SearchEngine] = None
data_extractor: Optional[DataExtractor] = None
global_config: Optional[Dict[str, Any]] = None # Umbenannt von 'config' zu 'global_config'

def create_app() -> Flask: # config_path als Argument entfernt
    """
    Erstellt und konfiguriert die Flask-Anwendung.
    Dies ist eine Fabrikfunktion, die eine saubere App-Instanz für Tests oder die eigentliche Anwendung liefert.
    """
    global global_config
    
    app = Flask(__name__, static_folder='static', static_url_path='')

    # Flask-Login Manager Initialisierung
    from app.auth import login_manager
    if not app.extensions.get('login', {}).get('login_manager'):
        login_manager.init_app(app)

    # Setup Logging (early!)
    setup_logging(app) # Logger an App binden

    # Lade Config falls noch nicht geladen
    if global_config is None:
        try:
            with open('config.yaml', 'r', encoding='utf-8') as f:
                global_config = yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning("config.yaml not found, using empty config. Some features may not work.")
            global_config = {}
        except (yaml.YAMLError, IOError) as e:
            logger.error(f"Error loading config: {e}")
            global_config = {}
    
    # PRODUCTION: Config Validierung
    environment = os.getenv('FLASK_ENV', 'development')
    if environment == 'production':
        from app.config_validator import validate_production_config
        logger.info("Validiere Production-Konfiguration...")
        if not validate_production_config(global_config):
            logger.critical("Production-Konfiguration ungültig! App wird nicht gestartet.")
            raise RuntimeError("Production-Konfiguration nicht sicher - siehe Errors oben")
    
    # Setup Security (includes CORS & rate limiting)
    limiter = setup_security(app)

    # Security Features
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 
        global_config.get('web', {}).get('secret_key', 'dev-key-change-me-in-production'))
    
    # Warnung für Standard-Secret-Key
    if app.config['SECRET_KEY'] == 'dev-key-change-me-in-production':
        if environment == 'production':
            raise RuntimeError("SECRET_KEY nicht geändert! Für Production nicht geeignet.")
        else:
            logger.warning("[WARNING] Standard SECRET_KEY wird verwendet. Nicht für Production geeignet!")
    
    csrf = CSRFProtect(app)
    
    # Init Auth (Setzt app.config['AUTH_USERS'] und registriert Handler)
    from app.auth import init_auth
    init_auth(app, global_config) 

    # Register Blueprints
    from app.blueprints import register_blueprints
    register_blueprints(app)

    # Register existing blueprints
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(health_bp)

    from app.blueprints.monitoring import monitoring_bp
    app.register_blueprint(monitoring_bp)
    
    # Metrics Endpoint
    @app.route('/metrics')
    def metrics():
        """Prometheus-kompatible Metriken"""
        from app.monitoring import get_metrics
        return get_metrics()

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

    # Request/Response Middleware
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
        
        # Record Prometheus metrics
        record_request_metrics(response)
        
        # Log request
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            log_request(request, response, duration)
        
        return response
    
    return app


# Globale Objekte (mit Type Hints) - NEU: `app` ist nicht mehr global

db: Optional[Database] = None
search_engine: Optional[SearchEngine] = None
data_extractor: Optional[DataExtractor] = None


def init_app(app_instance: Flask, config_path: str = 'config.yaml') -> None:
    """
    Initialisiert globale Komponenten (DB, SearchEngine, etc.) und verbindet sie mit der App-Instanz.
    
    Args:
        app_instance: Die Flask-Anwendungsinstanz, die initialisiert werden soll.
        config_path: Pfad zur Konfigurationsdatei
        
    Raises:
        FileNotFoundError: Wenn Config-Datei nicht gefunden
        yaml.YAMLError: Wenn Config ungültig
    """
    global db, search_engine, data_extractor, global_config # 'config' entfernt
    
    # Lade Config
    with open(config_path, 'r', encoding='utf-8') as f:
        global_config = yaml.safe_load(f) # global_config wird hier gesetzt
    
    # Initialisiere Komponenten
    db = Database(global_config)
    search_engine = SearchEngine()
    data_extractor = DataExtractor(global_config)
    
    # Init Redis
    from app.redis_client import RedisClient
    RedisClient() # Initialize singleton
    
    # Indexiere Dokumente
    _reindex_search()
    
    # Initiale Metriken
    try:
        from app.metrics import DB_DOCUMENT_COUNT
        if db:
            stats = db.get_overview_stats() # <- Hier könnte der Fehler sein
            DB_DOCUMENT_COUNT.set(stats.get('total_documents', 0))
    except Exception as e:
        logger.warning(f"Could not set initial metrics: {e}")
    
    logger.info("[OK] App initialisiert")


def _reindex_search():
    """Reindexiert alle Dokumente im Search-Engine"""
    global db, search_engine
    
    if not db or not search_engine:
        return
    
    try:
        documents = db.search_documents(limit=10000)
        search_engine.index_documents(documents)
        logger.info(f"[OK] {len(documents)} Dokumente indexiert")
    except Exception as e:
        logger.error(f"Fehler beim Indexieren: {e}")


def init_scheduler(app_instance: Flask) -> BackgroundScheduler: # App Instanz als Argument
    """
    Initialisiert Hintergrund-Scheduler für Email-Polling
    
    Returns:
        BackgroundScheduler-Instanz
    """
    scheduler = BackgroundScheduler()
    
    with app_instance.app_context(): # Scheduler muss App Kontext haben
            try:
                # Email-Polling Task
                email_receiver = EmailReceiver(global_config)
                if email_receiver.email_config.get('enabled'):
                    interval = email_receiver.email_config.get('poll_interval', 300)
                    scheduler.add_job(
                        func=email_receiver.check_new_emails,
                        trigger="interval",
                        seconds=interval,
                        id='email_polling'
                    )
                    logger.info(f"📧 Email-Polling aktiviert (alle {interval}s)")
            
            except Exception as e:            logger.error(f"Scheduler-Error: {e}")
    
    scheduler.start()
    return scheduler


# === Main ===

def run_server(host: str = '0.0.0.0', port: int = 5001, debug: bool = False):
    """
    Startet den Flask-Server
    
    Args:
        host: Host-Adresse
        port: Port
        debug: Debug-Modus
    """
    # Erstelle die Flask App Instanz
    app_instance = create_app() # create_app erstellt bereits die App
    
    # Initialisiere globale Komponenten und verbinde sie mit der App
    init_app(app_instance, 'config.yaml') # init_app akzeptiert jetzt die App Instanz
    
    # Starte Scheduler
    scheduler = init_scheduler(app_instance)
    
    # Starte Server
    try:
        logger.info(f"🚀 Server läuft auf http://{host}:{port}")
        app_instance.run(host=host, port=port, debug=debug) # app_instance verwenden
    except KeyboardInterrupt:
        logger.info("⏹️  Server gestoppt")
        scheduler.shutdown()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='OrganisationsAI Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host address')
    parser.add_argument('--port', type=int, default=5001, help='Port number')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, debug=args.debug)


