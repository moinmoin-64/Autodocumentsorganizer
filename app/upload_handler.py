"""
File Upload Handler - Manuelles Upload von Dokumenten
Ermöglicht Upload über Web-Interface
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify
import yaml

logger = logging.getLogger(__name__)

# Blueprint für Upload
upload_bp = Blueprint('upload', __name__)


ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'tiff', 'tif'}


def allowed_file(filename: str) -> bool:
    """Prüft ob Datei-Extension erlaubt ist"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@upload_bp.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Upload-Endpoint für manuelle Dokument-Uploads
    
    Form-Data:
        file: Die hochzuladene Datei
    """
    try:
        # Prüfe ob Datei vorhanden
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Sichere Dateinamen
        filename = secure_filename(file.filename)
        
        # Temp-Verzeichnis
        temp_dir = Path('/tmp/scans')
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Speichere temporär
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filename = f"upload_{timestamp}_{filename}"
        temp_path = temp_dir / temp_filename
        
        file.save(str(temp_path))
        
        logger.info(f"Datei hochgeladen: {temp_path}")
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'filename': filename,
            'temp_path': str(temp_path),
            'status': 'pending_processing'
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Upload: {e}")
        return jsonify({'error': str(e)}), 500


@upload_bp.route('/api/upload/process/<path:filepath>', methods=['POST'])
def process_uploaded_file(filepath: str):
    """
    Startet Verarbeitung einer hochgeladenen Datei
    
    Args:
        filepath: Pfad zur Datei
    """
    try:
        from app.document_processor import DocumentProcessor
        from app.categorizer import DocumentCategorizer
        from app.storage_manager import StorageManager
        from app.data_extractor import DataExtractor
        from app.database import Database
        
        if not Path(filepath).exists():
            return jsonify({'error': 'File not found'}), 404
        
        # Initialisiere Komponenten
        processor = DocumentProcessor()
        categorizer = DocumentCategorizer()
        storage = StorageManager()
        extractor = DataExtractor()
        db = Database()
        
        # Verarbeite
        logger.info(f"Verarbeite hochgeladene Datei: {filepath}")
        
        # 0. Duplikat-Check (Hash)
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        content_hash = sha256_hash.hexdigest()
        
        existing_id = db.check_duplicate(content_hash)
        if existing_id:
            logger.warning(f"Duplikat erkannt: {filepath} -> ID {existing_id}")
            # Lösche Temp-Datei
            try:
                Path(filepath).unlink()
            except Exception as e:
                logger.warning(f"Konnte Temp-Datei nicht löschen {filepath}: {e}")
            return jsonify({
                'success': True,
                'duplicate': True,
                'document_id': existing_id,
                'message': 'Dokument existiert bereits'
            })
        
        # 1. OCR
        document_data = processor.process_document(filepath)
        document_data['content_hash'] = content_hash
        
        if not document_data or not document_data.get('text'):
            return jsonify({'error': 'Could not extract text from document'}), 400
        
        # 2. Kategorisierung
        main_category, sub_category, confidence = categorizer.categorize(document_data)
        
        # 3. Datum
        document_date = document_data['dates'][0] if document_data.get('dates') else datetime.now()
        
        # 4. Summary
        summary = ' '.join(document_data.get('keywords', [])[:5])
        
        # 5. Speichern
        saved_path = storage.store_document(
            source_file=filepath,
            category=main_category,
            subcategory=sub_category,
            document_date=document_date,
            summary=summary
        )
        
        if not saved_path:
            return jsonify({'error': 'Failed to store document'}), 500
        
        # 6. Datenbank
        doc_id = db.add_document(
            filepath=saved_path,
            category=main_category,
            subcategory=sub_category,
            document_data=document_data,
            date_document=document_date
        )
        
        # 7. CSV-Extraktion
        year = document_date.year if document_date else datetime.now().year
        extractor.extract_and_save(
            document_data=document_data,
            category=main_category,
            year=year,
            file_path=saved_path
        )
        
        # Lösche temporäre Datei
        try:
            Path(filepath).unlink()
        except Exception as e:
            logger.warning(f"Konnte Temp-Datei nicht löschen {filepath}: {e}")
        
        return jsonify({
            'success': True,
            'document_id': doc_id,
            'category': main_category,
            'subcategory': sub_category,
            'confidence': confidence,
            'filepath': saved_path
        })
        
    except Exception as e:
        logger.error(f"Fehler bei Verarbeitung: {e}")
        return jsonify({'error': str(e)}), 500
