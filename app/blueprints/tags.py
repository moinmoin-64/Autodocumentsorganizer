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
    Tag zu Dokument hinzufügen
    
    Args:
        doc_id: Dokument-ID
    
    Request Body:
        tag_id: Tag-ID
    
    Returns:
        JSON mit Erfolgs-Status
    """
    try:
        from app.database import Database
        
        data = request.json
        if not data or not data.get('tag_id'):
            return jsonify({'error': 'tag_id required'}), 400
        
        db = Database()
        db.add_tag_to_document(doc_id, data['tag_id'])
        db.close()
        
        return jsonify({'success': True}), 200
        
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
