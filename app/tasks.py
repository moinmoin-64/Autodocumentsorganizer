"""
Celery Tasks - Asynchrone Verarbeitung
"""

from app.celery_app import celery_app
from app.document_processor import DocumentProcessor
from app.database import Database
from app.data_extractor import DataExtractor
from app.upload_handler import process_uploaded_file_logic  # Muss refactored werden
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def process_document_async(self, file_path: str):
    """
    Verarbeitet ein Dokument asynchron
    """
    try:
        logger.info(f"Starte asynchrone Verarbeitung für: {file_path}")
        
        # Nutze die zentrale Logik
        from app.upload_handler import process_file_logic
        result = process_file_logic(file_path)
        
        if result.get('error'):
            logger.error(f"Async Verarbeitung fehlgeschlagen: {result['error']}")
            return {'status': 'error', 'error': result['error']}
            
        logger.info(f"Async Verarbeitung erfolgreich: {result}")
        return {'status': 'success', 'result': result}
        
    except Exception as e:
        logger.error(f"Async Task failed: {e}")
        return {'status': 'error', 'error': str(e)}
