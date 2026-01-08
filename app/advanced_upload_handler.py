"""
Advanced Upload Handler Blueprint
Ergänzt bestehenden upload_handler.py mit zusätzlichen Features
"""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path
from typing import Dict, List, Tuple
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Upload Blueprint
upload_bp = Blueprint('advanced_upload', __name__, url_prefix='/api')


class AdvancedUploadHandler:
    """Erweiterte Upload-Verarbeitung mit Validierung und Metadaten"""
    
    def __init__(self, upload_dir: str, max_file_size: int = 100 * 1024 * 1024):
        """
        Initialisiert Upload Handler
        
        Args:
            upload_dir: Verzeichnis für Uploads
            max_file_size: Maximale Dateigröße in Bytes (default 100MB)
        """
        self.upload_dir = Path(upload_dir)
        self.max_file_size = max_file_size
        self.allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'tiff', 'doc', 'docx', 'xls', 'xlsx'}
        
        # Stelle sicher Directory existiert
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_file(self, file) -> Tuple[bool, str]:
        """
        Validiert eine Datei vor dem Upload
        
        Args:
            file: Flask FileStorage Objekt
            
        Returns:
            Tuple (is_valid, error_message)
        """
        # Prüfe ob Datei vorhanden
        if not file or file.filename == '':
            return False, "Keine Datei ausgewählt"
        
        # Prüfe Dateigröße
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > self.max_file_size:
            return False, f"Datei zu groß (Max: {self.max_file_size / (1024*1024):.0f}MB)"
        
        # Prüfe Dateiendung
        filename = secure_filename(file.filename)
        if '.' not in filename:
            return False, "Dateiendung erforderlich"
        
        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in self.allowed_extensions:
            return False, f"Dateityp nicht erlaubt: .{ext}"
        
        return True, ""
    
    def process_file(self, file, category: str = "documents") -> Dict:
        """
        Verarbeitet und speichert eine Datei
        
        Args:
            file: Flask FileStorage Objekt
            category: Kategorie für Datei-Organisation
            
        Returns:
            Dictionary mit Upload-Ergebnissen
        """
        # Validiere
        is_valid, error = self.validate_file(file)
        if not is_valid:
            return {
                'success': False,
                'error': error,
                'filename': file.filename if file else None
            }
        
        # Sichere Dateiname
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        
        # Speichere in Kategorie-Verzeichnis
        category_dir = self.upload_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = category_dir / safe_filename
        
        try:
            file.save(str(filepath))
            
            # Berechne Datei-Hash für Duplikat-Erkennung
            file_hash = self._calculate_file_hash(filepath)
            
            logger.info(f"✅ Datei gespeichert: {filepath}")
            
            return {
                'success': True,
                'filename': safe_filename,
                'original_filename': filename,
                'filepath': str(filepath),
                'category': category,
                'size': filepath.stat().st_size,
                'hash': file_hash,
                'url': f'/uploads/{category}/{safe_filename}'
            }
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            return {
                'success': False,
                'error': f"Speicherfehler: {str(e)}",
                'filename': filename
            }
    
    def _calculate_file_hash(self, filepath: Path, algorithm: str = 'sha256') -> str:
        """
        Berechnet File-Hash für Duplikat-Erkennung
        
        Args:
            filepath: Pfad zur Datei
            algorithm: Hash-Algorithmus
            
        Returns:
            Hex-String des Hashes
        """
        import hashlib
        
        hash_obj = hashlib.new(algorithm)
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def check_duplicate(self, file_hash: str, exclude_file: str = None) -> Dict:
        """
        Prüft ob Datei bereits existiert
        
        Args:
            file_hash: SHA256 Hash der Datei
            exclude_file: Datei zum Ausschließen
            
        Returns:
            Dictionary mit Duplikat-Info
        """
        # Durchsuche alle Dateien nach Hash
        for filepath in self.upload_dir.rglob('*'):
            if filepath.is_file() and (not exclude_file or str(filepath) != exclude_file):
                try:
                    other_hash = self._calculate_file_hash(filepath)
                    if other_hash == file_hash:
                        return {
                            'is_duplicate': True,
                            'existing_file': str(filepath),
                            'created_at': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
                        }
                except:
                    pass  # Skip files that can't be hashed
        
        return {'is_duplicate': False}


# Globale Instanz
_upload_handler = None

def get_upload_handler(upload_dir: str = None, max_size: int = None) -> AdvancedUploadHandler:
    """Hole oder erstelle globale Upload-Handler-Instanz"""
    global _upload_handler
    
    if _upload_handler is None:
        upload_dir = upload_dir or 'data/uploads'
        max_size = max_size or (100 * 1024 * 1024)
        _upload_handler = AdvancedUploadHandler(upload_dir, max_size)
    
    return _upload_handler


# API Endpoints

@upload_bp.route('/upload', methods=['POST'])
def handle_upload():
    """
    Hauptupload-Endpoint
    
    Returns:
        JSON mit Upload-Ergebnissen
    """
    # Prüfe ob Datei im Request
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'Keine Datei im Request'
        }), 400
    
    file = request.files['file']
    category = request.form.get('category', 'documents')
    check_duplicates = request.form.get('check_duplicates', 'true').lower() == 'true'
    
    handler = get_upload_handler()
    
    # Verarbeite Datei
    result = handler.process_file(file, category)
    
    if not result['success']:
        return jsonify(result), 400
    
    # Prüfe auf Duplikate wenn gewünscht
    if check_duplicates:
        dup_check = handler.check_duplicate(result['hash'])
        result['duplicate_check'] = dup_check
        
        if dup_check['is_duplicate']:
            logger.warning(f"⚠️  Duplikat erkannt: {result['filename']}")
    
    return jsonify({
        'success': True,
        'message': 'Datei erfolgreich hochgeladen',
        'files': [result]
    }), 200


@upload_bp.route('/upload/batch', methods=['POST'])
def handle_batch_upload():
    """
    Batch-Upload für mehrere Dateien
    
    Returns:
        JSON mit allen Upload-Ergebnissen
    """
    files = request.files.getlist('files')
    category = request.form.get('category', 'documents')
    
    if not files:
        return jsonify({
            'success': False,
            'error': 'Keine Dateien im Request'
        }), 400
    
    handler = get_upload_handler()
    results = []
    errors = []
    
    for file in files:
        result = handler.process_file(file, category)
        
        if result['success']:
            results.append(result)
        else:
            errors.append({
                'filename': result.get('filename', 'unknown'),
                'error': result.get('error', 'Unknown error')
            })
    
    return jsonify({
        'success': len(errors) == 0,
        'message': f"{len(results)} Dateien hochgeladen",
        'files': results,
        'errors': errors if errors else None
    }), 200 if not errors else 207  # 207 = Multi-Status


@upload_bp.route('/check-duplicate', methods=['POST'])
def check_duplicate_endpoint():
    """
    Prüft ob eine Datei bereits existiert
    
    Returns:
        JSON mit Duplikat-Info
    """
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'Keine Datei im Request'
        }), 400
    
    file = request.files['file']
    handler = get_upload_handler()
    
    # Berechne Hash
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        file.save(tmp.name)
        file_hash = handler._calculate_file_hash(Path(tmp.name))
        os.unlink(tmp.name)
    
    dup_check = handler.check_duplicate(file_hash)
    
    return jsonify({
        'success': True,
        'filename': secure_filename(file.filename),
        **dup_check
    }), 200
