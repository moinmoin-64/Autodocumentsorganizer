"""
Photos Blueprint
API-Endpoints für Foto-Verwaltung mit automatischer Ordner-Organisation
"""
from flask import Blueprint, jsonify, request, send_file, current_app
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, Any
import os
from werkzeug.utils import secure_filename
from PIL import Image
import io

photos_bp = Blueprint('photos', __name__, url_prefix='/api/photos')
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'heic', 'webp'}
PHOTOS_BASE_DIR = Path('data/Bilder')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_photo_path(year: int, month: int, day: int) -> Path:
    """Erstellt Pfad: data/Bilder/YYYY/MM/DD/"""
    path = PHOTOS_BASE_DIR / str(year) / f"{month:02d}" / f"{day:02d}"
    path.mkdir(parents=True, exist_ok=True)
    return path

def generate_thumbnail(image_path: Path, max_size: int = 300) -> bytes:
    """Generiert Thumbnail"""
    try:
        img = Image.open(image_path)
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Thumbnail error: {e}")
        return None

@photos_bp.route('/upload', methods=['POST'])
def upload_photo():
    """
    POST /api/photos/upload
    Lädt Foto hoch und speichert in Bilder/YYYY/MM/DD/
    
    Form Data:
        file: Foto-Datei
        date: Optional - Datum für Organisation (ISO format)
    
    Returns:
        JSON mit photo_id, path, url
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Datum bestimmen
        date_str = request.form.get('date')
        if date_str:
            photo_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            photo_date = datetime.now()
        
        # Sicherer Filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%H%M%S')
        filename = f"photo_{timestamp}_{filename}"
        
        # Speicherpfad
        save_dir = get_photo_path(photo_date.year, photo_date.month, photo_date.day)
        filepath = save_dir / filename
        
        # Speichern
        file.save(str(filepath))
        logger.info(f"Photo saved: {filepath}")
        
        # Relative URL
        relative_path = str(filepath.relative_to(PHOTOS_BASE_DIR))
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': str(filepath),
            'url': f"/api/photos/image/{relative_path}",
            'thumbnail_url': f"/api/photos/thumbnail/{relative_path}",
            'date': photo_date.isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@photos_bp.route('/', methods=['GET'])
def list_photos():
    """
    GET /api/photos
    Liste aller Fotos mit optionalen Filtern
    
    Query Parameters:
        year: Jahr (YYYY)
        month: Monat (MM)
        day: Tag (DD)
        limit: Anzahl (default: 100)
        offset: Offset für Pagination
    
    Returns:
        JSON Array with photo objects
    """
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        day = request.args.get('day', type=int)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        photos = []
        
        # Build search path
        search_path = PHOTOS_BASE_DIR
        if year:
            search_path = search_path / str(year)
            if month:
                search_path = search_path / f"{month:02d}"
                if day:
                    search_path = search_path / f"{day:02d}"
        
        if not search_path.exists():
            return jsonify({'photos': [], 'total': 0}), 200
        
        # Collect all photos
        for photo_path in search_path.rglob('*'):
            if photo_path.is_file() and allowed_file(photo_path.name):
                relative_path = str(photo_path.relative_to(PHOTOS_BASE_DIR))
                
                # Extract date from path
                parts = relative_path.split(os.sep)
                if len(parts) >= 3:
                    try:
                        photo_year = int(parts[0])
                        photo_month = int(parts[1])
                        photo_day = int(parts[2])
                        photo_date = datetime(photo_year, photo_month, photo_day)
                    except:
                        photo_date = datetime.fromtimestamp(photo_path.stat().st_mtime)
                else:
                    photo_date = datetime.fromtimestamp(photo_path.stat().st_mtime)
                
                photos.append({
                    'filename': photo_path.name,
                    'path': relative_path,
                    'url': f"/api/photos/image/{relative_path}",
                    'thumbnail_url': f"/api/photos/thumbnail/{relative_path}",
                    'date': photo_date.isoformat(),
                    'size': photo_path.stat().st_size
                })
        
        # Sort by date (newest first)
        photos.sort(key=lambda x: x['date'], reverse=True)
        
        # Pagination
        total = len(photos)
        photos = photos[offset:offset + limit]
        
        return jsonify({
            'photos': photos,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"List photos error: {e}")
        return jsonify({'error': str(e)}), 500

@photos_bp.route('/image/<path:photo_path>', methods=['GET'])
def get_photo(photo_path: str):
    """
    GET /api/photos/image/<path>
    Vollauflösungs-Foto
    """
    try:
        filepath = PHOTOS_BASE_DIR / photo_path
        
        if not filepath.exists() or not filepath.is_file():
            return jsonify({'error': 'Photo not found'}), 404
        
        return send_file(str(filepath), mimetype='image/jpeg')
        
    except Exception as e:
        logger.error(f"Get photo error: {e}")
        return jsonify({'error': str(e)}), 500

@photos_bp.route('/thumbnail/<path:photo_path>', methods=['GET'])
def get_thumbnail(photo_path: str):
    """
    GET /api/photos/thumbnail/<path>
    Thumbnail (300x300)
    """
    try:
        filepath = PHOTOS_BASE_DIR / photo_path
        
        if not filepath.exists():
            return jsonify({'error': 'Photo not found'}), 404
        
        # Generate thumbnail
        thumbnail_data = generate_thumbnail(filepath)
        
        if not thumbnail_data:
            # Fallback: return original
            return send_file(str(filepath), mimetype='image/jpeg')
        
        return send_file(
            io.BytesIO(thumbnail_data),
            mimetype='image/jpeg',
            as_attachment=False
        )
        
    except Exception as e:
        logger.error(f"Thumbnail error: {e}")
        return jsonify({'error': str(e)}), 500

@photos_bp.route('/<path:photo_path>', methods=['DELETE'])
def delete_photo(photo_path: str):
    """
    DELETE /api/photos/<path>
    Löscht Foto
    """
    try:
        filepath = PHOTOS_BASE_DIR / photo_path
        
        if not filepath.exists():
            return jsonify({'error': 'Photo not found'}), 404
        
        filepath.unlink()
        logger.info(f"Photo deleted: {filepath}")
        
        return jsonify({'success': True, 'message': 'Photo deleted'}), 200
        
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return jsonify({'error': str(e)}), 500
