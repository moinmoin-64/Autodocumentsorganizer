"""
Flask Web Server - REST API für Dokumentenverwaltung
Stellt API-Endpoints und Web-Dashboard bereit
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import yaml
from dotenv import load_dotenv

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Import eigener Module
import sys
sys.path.append(str(Path(__file__).parent.parent))

from app.database import Database
from app.search_engine import SearchEngine
from app.statistics_engine import StatisticsEngine
from app.data_extractor import DataExtractor
from app.storage_manager import StorageManager
from app.exporters import DataExporter
from app.email_receiver import EmailReceiver
from apscheduler.schedulers.background import BackgroundScheduler

from app.ollama_client import OllamaClient
from app.upload_handler import upload_bp
from app.auth import auth_bp, init_auth, login_required, current_user
from app.health import health_bp

import pandas as pd

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Flask App
app = Flask(__name__, static_folder='../static', static_url_path='')
CORS(app)

# Security Features
csrf = CSRFProtect(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Globale Objekte
db = None
search_engine = None
data_extractor = None
exporter = None
config = None

# Registriere Blueprints
app.register_blueprint(upload_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(health_bp)

# Metrics Endpoint
@app.route('/metrics')
def metrics():
    from app.metrics import MetricsManager
    return MetricsManager.get_metrics_response()



def init_app(config_path: str = 'config.yaml'):
    """Initialisiert App mit Konfiguration"""
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
    exporter = DataExporter()
    
    # Indexiere Dokumente
    _reindex_search()
    
    # Initiale Metriken
    try:
        from app.metrics import DB_DOCUMENT_COUNT
        count = len(db.search_documents(limit=100000))
        DB_DOCUMENT_COUNT.set(count)
    except:
        pass
    
    logger.info("Web Server initialisiert")


def _reindex_search():
    """Re-indexiert alle Dokumente für Suche"""
    global search_engine, db
    
    try:
        documents = db.search_documents(limit=10000)  # Alle
        search_engine.index_documents(documents)
        logger.info(f"Search-Index aktualisiert: {len(documents)} Dokumente")
    except Exception as e:
        logger.error(f"Fehler beim Indexieren: {e}")


# === API Endpoints ===

@app.route('/')
def index():
    """Serve Dashboard"""
    return send_file('static/index.html')


@app.route('/api/stats/overview', methods=['GET'])
def get_overview_stats():
    """
    Übersicht über alle Statistiken
    """
    try:
        stats = db.get_statistics()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Fehler bei Statistiken: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats/year/<int:year>', methods=['GET'])
def get_year_stats(year: int):
    """
    Statistiken für ein Jahr
    
    Args:
        year: Jahr
    """
    try:
        # Hole alle Dokumente für dieses Jahr
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)
        
        documents = db.search_documents(start_date=start_date, end_date=end_date, limit=10000)
        
        # Gruppiere nach Kategorien
        category_counts = {}
        for doc in documents:
            cat = doc.get('category', 'Sonstiges')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        return jsonify({
            'year': year,
            'total': len(documents),
            'categories': category_counts
        })
    except Exception as e:
        logger.error(f"Fehler bei Jahresstatistiken: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/documents', methods=['GET'])
@login_required
def list_documents():
    """
    Liste aller Dokumente (mit Filtern und Pagination)
    
    Query-Parameter:
        category: Kategorie-Filter
        year: Jahr-Filter
        page: Seite (default: 1)
        limit: Max. Anzahl (default: 50)
    """
    try:
        category = request.args.get('category')
        year_str = request.args.get('year')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit
        
        year = int(year_str) if year_str else None
        
        # Nutze paginierte Suche
        documents = db.search_documents_paginated(
            offset=offset,
            limit=limit,
            category=category,
            year=year
        )
        
        return jsonify({
            'documents': documents,
            'page': page,
            'limit': limit,
            'has_more': len(documents) == limit
        })
    except Exception as e:
        logger.error(f"Fehler beim Laden der Dokumente: {e}")
        return jsonify({'error': str(e)}), 500
@login_required
def advanced_search():
    """
    Erweiterte Suche mit Filtern
    
    Body (JSON):
        query: Text-Suchbegriff (optional)
        category: Kategorie (optional)
        start_date: Start-Datum YYYY-MM-DD (optional)
        end_date: End-Datum YYYY-MM-DD (optional)
        tags: Liste von Tags (optional)
        limit: Max. Ergebnisse (default: 100)
    """
    try:
        data = request.json or {}
        
        query = data.get('query')
        category = data.get('category')
        tags = data.get('tags')
        limit = int(data.get('limit', 100))
        
        # Parse Datumsangaben
        start_date = None
        end_date = None
        if data.get('start_date'):
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        if data.get('end_date'):
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        
        # Erweiterte Suche
        documents = db.search_documents_advanced(
            query=query,
            category=category,
            start_date=start_date,
            end_date=end_date,
            tags=tags,
            limit=limit
        )
        
        return jsonify({
            'count': len(documents),
            'documents': documents
        })
    except Exception as e:
        logger.error(f"Fehler bei erweiterter Suche: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tags', methods=['GET'])
@login_required
def get_all_tags():
    """Holt alle verwendeten Tags"""
    try:
        tags = db.get_all_tags()
        return jsonify({'tags': tags})
    except Exception as e:
        logger.error(f"Fehler beim Laden der Tags: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/documents/<int:doc_id>/tags', methods=['GET'])
@login_required
def get_document_tags(doc_id: int):
    """Holt Tags für ein Dokument"""
    try:
        tags = db.get_tags(doc_id)
        return jsonify({'tags': tags})
    except Exception as e:
        logger.error(f"Fehler beim Laden der Tags: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/documents/<int:doc_id>/tags', methods=['POST'])
@login_required
def add_document_tag(doc_id: int):
    """
    Fügt Tag zu Dokument hinzu
    
    Body (JSON):
        tag: Tag-Name
    """
    try:
        data = request.json
        tag_name = data.get('tag', '').strip()
        
        if not tag_name:
            return jsonify({'error': 'Tag name required'}), 400
        
        tag_id = db.add_tag(doc_id, tag_name)
        
        if tag_id:
            return jsonify({
                'success': True,
                'tag_id': tag_id,
                'tag_name': tag_name
            })
        else:
            return jsonify({'error': 'Failed to add tag'}), 500
            
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen von Tag: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tags/<int:tag_id>', methods=['DELETE'])
@login_required
def delete_tag(tag_id: int):
    """Entfernt Tag"""
    try:
        success = db.remove_tag(tag_id)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to remove tag'}), 500
            
    except Exception as e:
        logger.error(f"Fehler beim Entfernen von Tag: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/searches/saved', methods=['GET'])
@login_required
def get_saved_searches():
    """Holt gespeicherte Suchen"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else 'default'
        searches = db.get_saved_searches(user_id)
        return jsonify({'searches': searches})
    except Exception as e:
        logger.error(f"Fehler beim Laden der gespeicherten Suchen: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/searches/saved', methods=['POST'])
@login_required
def save_search():
    """
    Speichert eine Suche
    
    Body (JSON):
        name: Name der Suche
        filters: Filter-Objekt
    """
    try:
        data = request.json
        name = data.get('name', '').strip()
        filters = data.get('filters', {})
        
        if not name:
            return jsonify({'error': 'Search name required'}), 400
        
        user_id = current_user.id if hasattr(current_user, 'id') else 'default'
        search_id = db.save_search(name, filters, user_id)
        
        if search_id:
            return jsonify({
                'success': True,
                'search_id': search_id
            })
        else:
            return jsonify({'error': 'Failed to save search'}), 500
            
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Suche: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/searches/saved/<int:search_id>', methods=['DELETE'])
@login_required
def delete_saved_search_endpoint(search_id: int):
    """Löscht gespeicherte Suche"""
    try:
        success = db.delete_saved_search(search_id)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to delete search'}), 500
            
    except Exception as e:
        logger.error(f"Fehler beim Löschen der Suche: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/documents/search', methods=['GET'])
def search_documents():
    """
    Sucht Dokumente mit BM25
    
    Query-Parameter:
        q: Suchbegriff (erforderlich)
        limit: Max. Ergebnisse (default: 20)
    """
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 20))
        
        if not query:
            return jsonify({'error': 'Query parameter q required'}), 400
        
        # Suche
        results = search_engine.search(query, top_k=limit)
        
        # Hole Dokumente
        doc_ids = [doc_id for doc_id, score in results]
        documents = search_engine.get_documents_by_ids(doc_ids)
        
        # Füge Scores hinzu
        for i, (doc_id, score) in enumerate(results):
            if i < len(documents):
                documents[i]['search_score'] = score
        
        return jsonify({
            'query': query,
            'count': len(documents),
            'results': documents
        })
    except Exception as e:
        logger.error(f"Fehler bei Suche: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/documents/<int:doc_id>', methods=['GET'])
def get_document(doc_id: int):
    """
    Holt einzelnes Dokument
    
    Args:
        doc_id: Dokument-ID
    """
    try:
        doc = db.get_document_by_id(doc_id)
        
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        
        return jsonify(doc)
    except Exception as e:
        logger.error(f"Fehler beim Laden des Dokuments: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/documents/<int:doc_id>/download', methods=['GET'])
def download_document(doc_id: int):
    """
    Download eines Dokuments
    
    Args:
        doc_id: Dokument-ID
    """
    try:
        doc = db.get_document_by_id(doc_id)
        
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        
        filepath = doc.get('filepath')
        
        if not filepath or not Path(filepath).exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=doc.get('filename')
        )
    except Exception as e:
        logger.error(f"Fehler beim Download: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/insurance/list', methods=['GET'])
def list_insurances():
    """
    Liste aller Versicherungen
    """
    try:
        # Hole alle Versicherungs-CSVs
        all_data = []
        
        # Alle Jahre
        for year_dir in Path(config['system']['storage']['data_path']).iterdir():
            if year_dir.is_dir() and year_dir.name.isdigit():
                csv_path = year_dir / 'versicherungen_data.csv'
                
                if csv_path.exists():
                    try:
                        df = pd.read_csv(csv_path)
                        df['jahr'] = int(year_dir.name)
                        all_data.append(df)
                    except Exception as e:
                        logger.warning(f"Fehler beim Laden von {csv_path}: {e}")
        
        if not all_data:
            return jsonify({'insurances': []})
        
        # Kombiniere
        combined = pd.concat(all_data, ignore_index=True)
        
        # Konvertiere zu JSON
        insurances = combined.to_dict('records')
        
        return jsonify({
            'count': len(insurances),
            'insurances': insurances
        })
    except Exception as e:
        logger.error(f"Fehler beim Laden der Versicherungen: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/expenses/analysis', methods=['GET'])
def get_expenses_analysis():
    """
    Ausgaben-Analyse (für Tortendiagramm)
    
    Query-Parameter:
        year: Jahr (default: aktuelles Jahr)
    """
    try:
        year_str = request.args.get('year', str(datetime.now().year))
        year = int(year_str)
        
        # Lade Rechnungs-Daten
        csv_path = Path(config['system']['storage']['data_path']) / str(year) / 'rechnungen_data.csv'
        
        if not csv_path.exists():
            return jsonify({
                'year': year,
                'categories': {},
                'total': 0
            })
        
        df = pd.read_csv(csv_path)
        
        # Gruppiere nach Kategorie
        category_sums = df.groupby('kategorie')['betrag'].sum().to_dict()
        total = df['betrag'].sum()
        
        return jsonify({
            'year': year,
            'categories': category_sums,
            'total': float(total)
        })
    except Exception as e:
        logger.error(f"Fehler bei Ausgaben-Analyse: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/expenses/compare', methods=['GET'])
def compare_expenses():
    """
    Vergleicht Ausgaben zwischen Jahren
    
    Query-Parameter:
        year1: Jahr 1 (default: letztes Jahr)
        year2: Jahr 2 (default: aktuelles Jahr)
    """
    try:
        current_year = datetime.now().year
        year1 = int(request.args.get('year1', current_year - 1))
        year2 = int(request.args.get('year2', current_year))
        
        data_path = Path(config['system']['storage']['data_path'])
        
        # Daten für beide Jahre
        def get_year_data(year):
            csv_path = data_path / str(year) / 'rechnungen_data.csv'
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                return df.groupby('kategorie')['betrag'].sum().to_dict()
            return {}
        
        year1_data = get_year_data(year1)
        year2_data = get_year_data(year2)
        
        # Alle Kategorien
        all_categories = set(year1_data.keys()) | set(year2_data.keys())
        
        comparison = {}
        for cat in all_categories:
            comparison[cat] = {
                'year1': year1_data.get(cat, 0),
                'year2': year2_data.get(cat, 0),
                'change': year2_data.get(cat, 0) - year1_data.get(cat, 0)
            }
        
        return jsonify({
            'year1': year1,
            'year2': year2,
            'comparison': comparison
        })
    except Exception as e:
        logger.error(f"Fehler beim Vergleich: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chatbot-Endpoint (für Ollama)
    
    Body:
        message: Benutzernachricht
        context: Optional, Kontext-Daten
    """
    try:
        from app.ollama_client import OllamaClient
        
        data = request.json
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        # Initialisiere Ollama Client
        ollama = OllamaClient()
        
        # Hole Kontext-Daten
        context = {}
        
        # Aktuelle Statistiken als Kontext
        try:
            stats = db.get_statistics()
            context['total_documents'] = stats.get('total_documents', 0)
            context['categories'] = stats.get('categories', {})
        except Exception as e:
            logger.warning(f"Konnte Statistiken für Chatbot-Kontext nicht laden: {e}")
            context['total_documents'] = 0
            context['categories'] = {}
        
        # Generiere Antwort
        response_text = ollama.chat(message, context=context)
        
        response = {
            'message': message,
            'response': response_text,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Fehler beim Chat: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health Check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if db else 'disconnected'
    })


# === Fehler-Handler ===

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500



# --- Statistics API ---

@app.route('/api/stats/monthly/<int:year>', methods=['GET'])
@login_required
def get_monthly_trends(year):
    """Holt monatliche Trends"""
    try:
        engine = StatisticsEngine(db=db)
        trends = engine.get_monthly_trends(year)
        return jsonify(trends)
    except Exception as e:
        logger.error(f"Fehler bei Trends: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/budgets', methods=['POST'])
@login_required
def set_budget():
    """Setzt Budget"""
    try:
        data = request.json
        category = data.get('category')
        month = data.get('month') # YYYY-MM
        amount = float(data.get('amount', 0))
        
        if not all([category, month]):
            return jsonify({'error': 'Missing data'}), 400
            
        success = db.set_budget(category, month, amount)
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Fehler bei Budget: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/budgets/<category>/<month>', methods=['GET'])
@login_required
def get_budget_status(category, month):
    """Holt Budget Status"""
    try:
        year, m = map(int, month.split('-'))
        engine = StatisticsEngine(db=db)
        status = engine.calculate_budget_status(category, year, m)
        return jsonify(status)
    except Exception as e:
        logger.error(f"Fehler bei Budget Status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats/predictions/<category>', methods=['GET'])
@login_required
def get_prediction(category):
    """Holt Prognose"""
    try:
        months = int(request.args.get('months', 3))
        engine = StatisticsEngine(db=db)
        prediction = engine.predict_expenses(category, months)
        return jsonify(prediction)
    except Exception as e:
        logger.error(f"Fehler bei Prognose: {e}")
        return jsonify({'error': str(e)}), 500

        return jsonify({'error': str(e)}), 500


@app.route('/api/export/excel', methods=['GET'])
@login_required
def export_excel():
    """Exportiert Dokumente als Excel"""
    try:
        # Filter Parameter übernehmen
        category = request.args.get('category')
        year_str = request.args.get('year')
        year = int(year_str) if year_str else None
        
        # Dokumente laden (ohne Limit für Export)
        documents = db.search_documents(category=category, year=year, limit=10000)
        
        output = exporter.export_to_excel(documents)
        
        filename = f"export_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Fehler bei Excel Export: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/pdf', methods=['GET'])
@login_required
def export_pdf():
    """Exportiert Dokumente als PDF"""
    try:
        # Filter Parameter übernehmen
        category = request.args.get('category')
        year_str = request.args.get('year')
        year = int(year_str) if year_str else None
        
        # Dokumente laden
        documents = db.search_documents(category=category, year=year, limit=1000)
        
        title = f"Dokumenten-Bericht {year if year else ''} {category if category else ''}"
        output = exporter.export_to_pdf(documents, title=title)
        
        filename = f"report_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Fehler bei PDF Export: {e}")
        return jsonify({'error': str(e)}), 500


def run_server(host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
    """
    Startet Web Server
    
    Args:
        host: Host-Adresse
        port: Port
        debug: Debug-Mode
    """
    app.run(host=host, port=port, debug=debug)


def init_scheduler():
    """Startet Hintergrund-Tasks"""
    try:
        scheduler = BackgroundScheduler()
        email_receiver = EmailReceiver()
        
        # Check email interval (default 5 min)
        interval = config.get('email', {}).get('check_interval', 300)
        
        def check_emails():
            logger.info("Prüfe Emails...")
            files = email_receiver.fetch_attachments()
            for f in files:
                try:
                    # Import hier um Zyklen zu vermeiden
                    from app.upload_handler import process_file_logic
                    logger.info(f"Verarbeite Email-Anhang: {f}")
                    process_file_logic(f)
                except Exception as e:
                    logger.error(f"Fehler bei Email-Verarbeitung: {e}")
            
        if config.get('email', {}).get('enabled', False):
            scheduler.add_job(check_emails, 'interval', seconds=interval)
            scheduler.start()
            logger.info(f"Email Scheduler gestartet (Intervall: {interval}s)")
            
    except Exception as e:
        logger.error(f"Fehler beim Starten des Schedulers: {e}")


if __name__ == '__main__':
    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialisiere
    init_app()
    
    # Starte Scheduler
    init_scheduler()
    
    # Starte Server
    run_server(
        host=config['web']['host'],
        port=config['web']['port'],
        debug=config['web']['debug']
    )
