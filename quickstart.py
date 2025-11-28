#!/usr/bin/env python3
"""
Quick Start Script - Für schnellen Start ohne Installation
Testet Komponenten einzeln
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Prüft ob wichtige Dependencies installiert sind"""
    logger.info("Prüfe Dependencies...")
    
    missing = []
    
    try:
        import flask
        logger.info(f"✓ Flask {flask.__version__}")
    except ImportError:
        missing.append("flask")
    
    try:
        import yaml
        logger.info("✓ PyYAML")
    except ImportError:
        missing.append("pyyaml")
    
    try:
        import pandas
        logger.info(f"✓ Pandas {pandas.__version__}")
    except ImportError:
        missing.append("pandas")
    
    try:
        import PIL
        logger.info(f"✓ Pillow {PIL.__version__}")
    except ImportError:
        missing.append("pillow")
    
    try:
        import pytesseract
        logger.info("✓ pytesseract")
    except ImportError:
        missing.append("pytesseract")
    
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("✓ sentence-transformers")
    except ImportError:
        missing.append("sentence-transformers")
    
    if missing:
        logger.error(f"\n✗ Fehlende Packages: {', '.join(missing)}")
        logger.error("Install mit: pip install -r requirements.txt")
        return False
    
    logger.info("\n✓ Alle Dependencies installiert!")
    return True

def test_config():
    """Testet ob config.yaml geladen werden kann"""
    logger.info("\nPrüfe config.yaml...")
    
    try:
        import yaml
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info("✓ config.yaml erfolgreich geladen")
        logger.info(f"  - Scanner: {config['system']['scanner']['device']}")
        logger.info(f"  - Web Port: {config['web']['port']}")
        logger.info(f"  - OCR Sprachen: {config['ocr']['languages']}")
        return True
    except Exception as e:
        logger.error(f"✗ Fehler beim Laden von config.yaml: {e}")
        return False

def test_database():
    """Testet Datenbank-Erstellung"""
    logger.info("\nPrüfe Datenbank...")
    
    try:
        from app.database import Database
        
        db = Database()
        stats = db.get_statistics()
        
        logger.info("✓ Datenbank erfolgreich initialisiert")
        logger.info(f"  - Dokumente: {stats['total_documents']}")
        logger.info(f"  - Kategorien: {len(stats.get('categories', {}))}")
        return True
    except Exception as e:
        logger.error(f"✗ Datenbank-Fehler: {e}")
        return False

def test_categorizer():
    """Testet AI-Kategorisierung"""
    logger.info("\nPrüfe AI-Categorizer (dauert etwas beim ersten Mal)...")
    
    try:
        from app.categorizer import DocumentCategorizer
        
        categorizer = DocumentCategorizer()
        
        # Test-Dokument
        test_doc = {
            'text': 'Rechnung für Stromverbrauch Januar 2024. Betrag: 45 EUR.',
            'keywords': ['rechnung', 'strom', 'betrag']
        }
        
        category, subcategory, confidence = categorizer.categorize(test_doc)
        
        logger.info("✓ Categorizer funktioniert")
        logger.info(f"  - Test kategorisiert als: {category}/{subcategory}")
        logger.info(f"  - Confidence: {confidence:.2f}")
        return True
    except Exception as e:
        logger.error(f"✗ Categorizer-Fehler: {e}")
        return False

def quick_start():
    """Führt Quick Start durch"""
    print("=" * 60)
    print("  Dokumentenverwaltungssystem - Quick Start")
    print("=" * 60)
    print()
    
    all_ok = True
    
    # 1. Dependencies
    if not check_dependencies():
        all_ok = False
    
    # 2. Config
    if not test_config():
        all_ok = False
    
    # 3. Database
    if not test_database():
        all_ok = False
    
    # 4. Categorizer (optional, dauert länger)
    print()
    test_ai = input("AI-Categorizer testen? (lädt Model herunter, dauert bei erstem Mal) [j/N]: ")
    if test_ai.lower() in ['j', 'ja', 'y', 'yes']:
        if not test_categorizer():
            all_ok = False
    
    print()
    print("=" * 60)
    
    if all_ok:
        logger.info("✓ Alles bereit!")
        logger.info("\nStarte Server mit: python main.py")
        logger.info("Dashboard: http://localhost:5000")
    else:
        logger.error("✗ Einige Tests fehlgeschlagen")
        logger.error("Prüfe die Fehler oben und behebe sie")
        sys.exit(1)

if __name__ == "__main__":
    quick_start()
