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
    """
    try:
        if not Path(filepath).exists():
            return jsonify({'error': 'File not found'}), 404

        # Prüfe auf Async-Flag (optional via Query Param oder Config)
        use_async = request.args.get('async', 'false').lower() == 'true'
        
        # Versuche Async (Celery)
        if use_async:
            try:
                from app.tasks import process_document_async
                task = process_document_async.delay(filepath)
                return jsonify({
                    'success': True,
                    'status': 'processing_async',
                    'task_id': task.id,
                    'message': 'Verarbeitung im Hintergrund gestartet'
                })
            except ImportError:
                logger.warning("Celery nicht verfügbar, Fallback auf synchron")
            except Exception as e:
                logger.error(f"Async Start fehlgeschlagen: {e}")

        # Synchron (Fallback oder Default)
        result = process_file_logic(filepath)
        
        if result.get('error'):
            return jsonify(result), 500
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Fehler bei Verarbeitung: {e}")
        return jsonify({'error': str(e)}), 500


def process_file_logic(filepath: str) -> dict:
    """
    Zentrale Verarbeitungslogik (wird auch von Celery genutzt)
    """
    try:
        from app.document_processor import DocumentProcessor
        from app.categorizer import DocumentCategorizer
        from app.storage_manager import StorageManager
        from app.data_extractor import DataExtractor
        from app.database import Database
        
        # Initialisiere Komponenten
        processor = DocumentProcessor()
        categorizer = DocumentCategorizer()
        storage = StorageManager()
        extractor = DataExtractor()
        db = Database()
        
        logger.info(f"Verarbeite Datei (Logic): {filepath}")
        
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
            try:
                Path(filepath).unlink()
            except Exception as e:
                logger.warning(f"Konnte Temp-Datei nicht löschen {filepath}: {e}")
            return {
                'success': True,
                'duplicate': True,
                'document_id': existing_id,
                'message': 'Dokument existiert bereits'
            }
        
        # 1. OCR
        document_data = processor.process_document(filepath)
        document_data['content_hash'] = content_hash
        
        if not document_data or not document_data.get('text'):
            return {'error': 'Could not extract text from document'}
        
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
            return {'error': 'Failed to store document'}
        
        # 6. Datenbank
        doc_id = db.add_document(
            filepath=saved_path,
            category=main_category,
            subcategory=sub_category,
            document_data=document_data,
            date_document=document_date
        )
        
        # Audit Log
        try:
            from app.audit import log_action
            log_action(db, "upload_document", str(doc_id), {
                'filename': Path(filepath).name, 
                'category': main_category
            })
        except Exception as e:
            logger.warning(f"Audit Log fehlgeschlagen: {e}")
        
        # Metrics update
        try:
            from app.metrics import DOCUMENT_PROCESSED_TOTAL
            DOCUMENT_PROCESSED_TOTAL.labels(status='success', category=main_category).inc()
        except:
            pass
        
        # 7. CSV-Extraktion
        year = document_date.year if document_date else datetime.now().year
        extractor.extract_and_save(
            document_data=document_data,
            category=main_category,
            year=year,
            file_path=saved_path
        )
        
        # 8. Auto-Tagging
        try:
            from app.auto_tagger import AutoTagger
            auto_tagger = AutoTagger()
            
            auto_tags = auto_tagger.generate_tags(
                text=document_data.get('text', ''),
                category=main_category,
                metadata={
                    'date_document': document_date,
                    'amount': document_data.get('amounts', [None])[0]
                }
            )
            
            for tag in auto_tags:
                db.add_tag(doc_id, tag)
            
            logger.info(f"Auto-Tagging: {len(auto_tags)} Tags generiert für Dokument {doc_id}")
            
        except Exception as e:
            logger.warning(f"Auto-Tagging fehlgeschlagen: {e}")

        # 9. Semantic Search & Duplicates
        try:
            from app.semantic_search import SemanticSearch
            semantic = SemanticSearch()
            
            if semantic.enabled and document_data.get('text'):
                # Embedding generieren
                embedding = semantic.generate_embedding(document_data['text'])
                
                if embedding:
                    # Check auf semantische Duplikate
                    all_embeddings = db.get_all_embeddings()
                    duplicates = semantic.find_duplicates(embedding, all_embeddings)
                    
                    if duplicates:
                        best_match_id, score = duplicates[0]
                        logger.warning(f"Semantisches Duplikat gefunden! Ähnlichkeit: {score:.2f} mit Doc ID {best_match_id}")
                        # Wir speichern es trotzdem, aber loggen es. 
                        # Man könnte hier auch ein Flag in der DB setzen.
                        db.add_tag(doc_id, "duplicate_candidate")
                    
                    # Embedding speichern
                    db.save_embedding(doc_id, embedding)
                    
        except Exception as e:
            logger.warning(f"Semantic Search fehlgeschlagen: {e}")
        
        # Lösche temporäre Datei
        try:
            Path(filepath).unlink()
        except Exception as e:
            logger.warning(f"Konnte Temp-Datei nicht löschen {filepath}: {e}")
        
        return {
            'success': True,
            'document_id': doc_id,
            'category': main_category,
            'subcategory': sub_category,
            'confidence': confidence,
            'filepath': saved_path
        }
        
    except Exception as e:
        logger.error(f"Logic Error: {e}")
        return {'error': str(e)}
