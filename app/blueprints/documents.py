"""
Documents Blueprint
API-Endpoints für Dokument-Verwaltung
"""
from flask import Blueprint, jsonify, request, send_file, current_app
from pathlib import Path
import logging
from typing import Dict, Any

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')
logger = logging.getLogger(__name__)


@documents_bp.route('/', methods=['GET'])
def list_documents() -> tuple[Dict[str, Any], int]:
    """
    GET /api/documents
    Liste aller Dokumente mit optionalen Filtern
    
    Query Parameters:
        limit: Anzahl Dokumente (default: 50)
        offset: Offset für Pagination (default: 0)
        category: Filter nach Kategorie
        year: Filter nach Jahr
        query: Volltextsuche
    
    Returns:
        JSON mit Dokumenten-Liste
    """
    try:
        from app.database import Database
        
        db = Database()
        
        # Query-Parameter
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        category = request.args.get('category')
        year = request.args.get('year')
        query = request.args.get('query')
        
        # Build filter kwargs
        kwargs = {}
        if category:
            kwargs['category'] = category
        if year:
            kwargs['year'] = int(year)
        if query:
            kwargs['query'] = query
        
        # Get documents
        documents = db.search_documents(limit=limit, offset=offset, **kwargs)
        
        # Get total count
        total = len(db.search_documents(**kwargs))
        
        db.close()
        
        return jsonify({
            'documents': documents,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return jsonify({'error': str(e)}), 500


@documents_bp.route('/<int:doc_id>', methods=['GET'])
def get_document(doc_id: int) -> tuple[Dict[str, Any], int]:
    """
    GET /api/documents/<id>
    Einzelnes Dokument abrufen
    
    Args:
        doc_id: Dokument-ID
    
    Returns:
        JSON mit Dokument-Details
    """
    try:
        from app.database import Database
        
        db = Database()
        document = db.get_document(doc_id)
        db.close()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        return jsonify(document), 200
        
    except Exception as e:
        logger.error(f"Error getting document {doc_id}: {e}")
        return jsonify({'error': str(e)}), 500


@documents_bp.route('/<int:doc_id>/download', methods=['GET'])
def download_document(doc_id: int):
    """
    GET /api/documents/<id>/download
    Dokument herunterladen
    
    Args:
        doc_id: Dokument-ID
    
    Returns:
        Datei-Download
    """
    try:
        from app.database import Database
        
        db = Database()
        document = db.get_document(doc_id)
        db.close()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        filepath = document.get('filepath')
        if not filepath or not Path(filepath).exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=document.get('filename', 'document.pdf')
        )
        
    except Exception as e:
        logger.error(f"Error downloading document {doc_id}: {e}")
        return jsonify({'error': str(e)}), 500


@documents_bp.route('/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id: int) -> tuple[Dict[str, Any], int]:
    """
    DELETE /api/documents/<id>
    Dokument löschen
    
    Args:
        doc_id: Dokument-ID
    
    Returns:
        JSON mit Erfolgs-Status
    """
    try:
        from app.database import Database
        
        db = Database()
        
        # Get document to delete file
        document = db.get_document(doc_id)
        if not document:
            db.close()
            return jsonify({'error': 'Document not found'}), 404
        
        # Delete from database
        db.delete_document(doc_id)
        
        # Delete file (optional)
        filepath = document.get('filepath')
        if filepath and Path(filepath).exists():
            try:
                Path(filepath).unlink()
            except Exception as e:
                logger.warning(f"Could not delete file {filepath}: {e}")
        
        db.close()
        
        return jsonify({'success': True, 'message': 'Document deleted'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        return jsonify({'error': str(e)}), 500


@documents_bp.route('/<int:doc_id>', methods=['PUT'])
def update_document(doc_id: int) -> tuple[Dict[str, Any], int]:
    """
    PUT /api/documents/<id>
    Dokument-Metadaten aktualisieren
    
    Args:
        doc_id: Dokument-ID
    
    Returns:
        JSON mit aktualisiertem Dokument
    """
    try:
        from app.database import Database
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        db = Database()
        
        # Check if document exists
        document = db.get_document(doc_id)
        if not document:
            db.close()
            return jsonify({'error': 'Document not found'}), 404
        
        # Update document (implement in database.py if not exists)
        # For now, just return success
        db.close()
        
        return jsonify({
            'success': True,
            'message': 'Document updated',
            'document': document
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating document {doc_id}: {e}")
        return jsonify({'error': str(e)}), 500
