"""
Main Entry Point - Dokumentenverwaltungssystem
Startet alle Komponenten des Systems
"""

import logging
import sys
import time
import threading
from pathlib import Path
from datetime import datetime
import yaml

# Import eigener Module
from app.scanner_handler import ScannerHandler
from app.document_processor import DocumentProcessor
from app.categorizer import DocumentCategorizer
from app.storage_manager import StorageManager
from app.data_extractor import DataExtractor
from app.database import Database
from app.server import init_app, run_server
from app.queue_manager import get_global_queue

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('document_manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Konfiguration laden
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Globale Komponenten
scanner_handler = None
document_processor = None
categorizer = None
storage_manager = None
data_extractor = None
database = None
doc_queue = None


def init_components():
    """Initialisiert alle System-Komponenten"""
    global scanner_handler, document_processor, categorizer
    global storage_manager, data_extractor, database, doc_queue
    
    logger.info("=== Initialisiere Komponenten ===")
    
    # Scanner
    scanner_handler = ScannerHandler()
    
    # Document Processing
    document_processor = DocumentProcessor()
    categorizer = DocumentCategorizer()
    storage_manager = StorageManager()
    data_extractor = DataExtractor()
    
    # Database
    database = Database()
    
    # Async Queue
    logger.info("Initialisiere Async Processing Queue...")
    doc_queue = get_global_queue(worker_count=2)
    doc_queue.set_processing_callback(process_scanned_document)
    doc_queue.start()
    
    logger.info("✓ Alle Komponenten initialisiert")


def process_scanned_document(scan_path: str):
    """
    Verarbeitet ein gescanntes Dokument (wird von Queue aufgerufen)
    
    Args:
        scan_path: Pfad zum gescannten Dokument
    """
    logger.info(f"🔄 Verarbeite: {scan_path}")
    
    try:
        # 1. OCR & Text-Extraktion
        logger.info("  → OCR & Text-Extraktion...")
        document_data = document_processor.process_document(scan_path)
        
        if not document_data or not document_data.get('text'):
            logger.warning(f"  ⚠️  Kein Text extrahiert")
            return
        
        # 2. Kategorisierung
        logger.info("  → Kategorisierung...")
        main_category, sub_category, confidence = categorizer.categorize(document_data)
        logger.info(f"  → {main_category}/{sub_category} ({confidence:.2f})")
        
        # 3. Datum
        document_date = document_data['dates'][0] if document_data.get('dates') else None
        
        # 4. Summary
        summary = ' '.join(document_data.get('keywords', [])[:5])
        
        # 5. Speichern
        logger.info("  → Speichere...")
        saved_path = storage_manager.store_document(
            source_file=scan_path,
            category=main_category,
            subcategory=sub_category,
            document_date=document_date,
            summary=summary
        )
        
        if not saved_path:
            logger.error("  ✗ Speichern fehlgeschlagen")
            return
        
        # 6. Datenbank
        database.add_document(
            filepath=saved_path,
            category=main_category,
            subcategory=sub_category,
            document_data=document_data,
            date_document=document_date
        )
        
        # 7. CSV-Export
        year = document_date.year if document_date else datetime.now().year
        data_extractor.extract_and_save(
            document_data=document_data,
            category=main_category,
            year=year,
            file_path=saved_path
        )
        
        logger.info(f"  ✓ Fertig: {saved_path}")
        
    except Exception as e:
        logger.error(f"  ✗ Fehler: {e}")


def start_scanner_monitoring():
    """Startet Scanner-Überwachung"""
    logger.info("📷 Scanner-Monitoring aktiv")
    logger.info("   Nutze Web-Interface für Upload")
    
    # Future: Echte Scanner-Button-Überwachung
    while True:
        time.sleep(1)


def start_web_server():
    """Startet Web Server"""
    logger.info("🌐 Starte Web Server...")
    
    # Initialisiere Flask App
    init_app('config.yaml')
    
    # Starte Server
    host = config['web']['host']
    port = config['web']['port']
    debug = config['web']['debug']
    
    logger.info(f"✓ Server läuft: http://{host}:{port}")
    
    run_server(host=host, port=port, debug=debug)


def main():
    """Hauptfunktion"""
    try:
        logger.info("=== Dokumentenverwaltungssystem startet ===")
        
        # Init Components
        init_components()
        
        # Scanner-Thread
        scanner_thread = threading.Thread(
            target=start_scanner_monitoring,
            daemon=True
        )
        scanner_thread.start()
        
        # Web Server (Main Thread)
        start_web_server()
        
    except KeyboardInterrupt:
        logger.info("\n=== System wird beendet ===")
        if doc_queue:
            doc_queue.stop()
        sys.exit(0)
    except Exception as e:
        logger.error(f"✗ Kritischer Fehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
