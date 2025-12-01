"""
Tags Blueprint
API-Endpoints für Tag-Verwaltung
"""
from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any

tags_bp = Blueprint('tags', __name__, url_prefix='/api/tags')
logger = logging.getLogger(__name__)


@tags_bp.route('/', methods=['GET'])
def get_all_tags() -> tuple[Dict[str, Any], int]:
    """
    GET /api/tags
    Alle Tags abrufen
    
    Returns:
        JSON mit Tag-Liste
    """
    try:
        from app.database import Database
        
        db = Database()
        tags = db.get_all_tags()
        db.close()
        
        return jsonify({'tags': tags}), 200
        
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        return jsonify({'error': str(e)}), 500


@tags_bp.route('/', methods=['POST'])
def create_tag() -> tuple[Dict[str, Any], int]:
    """
    POST /api/tags
    Neuen Tag erstellen
    
    Request Body:
        name: Tag-Name
        color: Farbe (Hex)
    
    Returns:
        JSON mit erstelltem Tag
    """
    try:
        from app.database import Database
        
        data = request.json
        if not data or not data.get('name'):
            return jsonify({'error': 'Name required'}), 400
        
        db = Database()
        tag_id = db.create_tag(
            name=data['name'],
            color=data.get('color', '#808080')
        )
        db.close()
        
        return jsonify({
            'success': True,
            'id': tag_id,
            'name': data['name'],
            'color': data.get('color', '#808080')
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating tag: {e}")
        return jsonify({'error': str(e)}), 500


@tags_bp.route('/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id: int) -> tuple[Dict[str, Any], int]:
    """
    DELETE /api/tags/<id>
    Tag löschen
    
    Args:
        tag_id: Tag-ID
    
    Returns:
        JSON mit Erfolgs-Status
    """
    try:
        from app.database import Database
        
        db = Database()
        db.delete_tag(tag_id)
        db.close()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error deleting tag: {e}")
        return jsonify({'error': str(e)}), 500


@tags_bp.route('/document/<int:doc_id>', methods=['GET'])
def get_document_tags(doc_id: int) -> tuple[Dict[str, Any], int]:
    """
    GET /api/tags/document/<id>
    Tags eines Dokuments abrufen
    
    Args:
        doc_id: Dokument-ID
    
    Returns:
        JSON mit Tag-Liste
    """
    try:
        from app.database import Database
        
        db = Database()
        tags = db.get_document_tags(doc_id)
        db.close()
        
        return jsonify({'tags': tags}), 200
        
    except Exception as e:
        logger.error(f"Error getting document tags: {e}")
        return jsonify({'error': str(e)}), 500


@tags_bp.route('/document/<int:doc_id>', methods=['POST'])
def add_document_tag(doc_id: int) -> tuple[Dict[str, Any], int]:
    """
    POST /api/tags/document/<id>
    Tag zu Dokument hinzufügen (per ID oder Name)
    
    Args:
        doc_id: Dokument-ID
    
    Request Body:
        tag_id: Tag-ID (optional)
        tag_name: Tag-Name (optional, wird erstellt falls nicht existiert)
    
    Returns:
        JSON mit Erfolgs-Status
    """
    try:
        from app.database import Database
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        tag_id = data.get('tag_id')
        tag_name = data.get('tag_name') or data.get('tag') # Support both
        
        if not tag_id and not tag_name:
            return jsonify({'error': 'tag_id or tag_name required'}), 400
        
        db = Database()
        
        # If tag_name provided, find or create tag
        if not tag_id and tag_name:
            # Check if tag exists (simple check, ideally db method)
            # For now, we assume create_tag handles duplicates or we check first
            # But Database class might not have get_tag_by_name
            # Let's try to create it, if it exists we might get an ID back or error
            # Actually, let's implement get_or_create_tag in database.py or here
            
            # Quick implementation: Try to create, if fails (duplicate), get by name
            # But create_tag implementation in database.py is needed to be checked.
            # Assuming create_tag returns id.
            
            # Better: Use a helper in database.py. But I can't modify database.py right now easily without checking it.
            # Let's assume create_tag handles it or we search first.
            
            # Let's try to find it first
            all_tags = db.get_all_tags()
            existing_tag = next((t for t in all_tags if t['name'].lower() == tag_name.lower()), None)
            
            if existing_tag:
                tag_id = existing_tag['id']
            else:
                tag_id = db.create_tag(tag_name, '#808080')

        if tag_id:
            db.add_tag_to_document(doc_id, tag_id)
            db.close()
            return jsonify({'success': True, 'tag_id': tag_id}), 200
        else:
            db.close()
            return jsonify({'error': 'Failed to get tag ID'}), 500
        
    except Exception as e:
        logger.error(f"Error adding tag to document: {e}")
        return jsonify({'error': str(e)}), 500


@tags_bp.route('/document/<int:doc_id>/tag/<int:tag_id>', methods=['DELETE'])
def remove_document_tag(doc_id: int, tag_id: int) -> tuple[Dict[str, Any], int]:
    """
    DELETE /api/tags/document/<doc_id>/tag/<tag_id>
    Tag von Dokument entfernen
    
    Args:
        doc_id: Dokument-ID
        tag_id: Tag-ID
    
    Returns:
        JSON mit Erfolgs-Status
    """
    try:
        from app.database import Database
        
        db = Database()
        db.remove_tag_from_document(doc_id, tag_id)
        db.close()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error removing tag from document: {e}")
        return jsonify({'error': str(e)}), 500
