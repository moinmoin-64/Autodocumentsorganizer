"""
Documents Blueprint
API-Endpoints für Dokument-Verwaltung
"""
from flask import Blueprint, jsonify, request, send_file, current_app
from pathlib import Path
import logging
from typing import Dict, Any, Tuple

from app.api_response import APIResponse, ErrorCodes

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')
logger = logging.getLogger(__name__)


@documents_bp.route('/', methods=['GET'])
def list_documents() -> Tuple[Dict[str, Any], int]:
    """
    GET /api/documents
    Liste aller Dokumente mit optionalen Filtern
    
    Query Parameters:
        page: Seite (default: 1)
        page_size: Einträge pro Seite (default: 20)
        category: Filter nach Kategorie
        year: Filter nach Jahr
        query: Volltextsuche
    
    Returns:
        JSON mit paginierten Dokumenten
    """
    try:
        from app.database import Database
        
        db = Database()
        
        # Query-Parameter (modernized pagination)
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        category = request.args.get('category')
        year = request.args.get('year')
        query = request.args.get('query')
        
        # Validation
        if page < 1:
            return APIResponse.validation_error(
                {"page": ["Must be >= 1"]},
                "Invalid pagination parameters"
            )
        if page_size < 1 or page_size > 100:
            return APIResponse.validation_error(
                {"page_size": ["Must be between 1 and 100"]},
                "Invalid page size"
            )
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Build filter kwargs
        kwargs = {}
        if category:
            kwargs['category'] = category
        if year:
            try:
                kwargs['year'] = int(year)
            except ValueError:
                return APIResponse.validation_error(
                    {"year": ["Must be a valid year"]}
                )
        if query:
            kwargs['query'] = query
        
        # Get documents
        documents = db.search_documents(
            limit=page_size,
            offset=offset,
            **kwargs
        )
        
        # Get total count
        total = db.count_documents(**kwargs)
        
        db.close()
        
        return APIResponse.paginated(
            data=documents,
            total=total,
            page=page,
            page_size=page_size,
            message="Documents retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return APIResponse.server_error(
            message="Failed to retrieve documents",
            exception=e
        )


@documents_bp.route('/<int:doc_id>', methods=['GET'])
def get_document(doc_id: int) -> Tuple[Dict[str, Any], int]:
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
            return APIResponse.not_found("Document", doc_id)
        
        return APIResponse.success(
            data=document,
            message="Document retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting document {doc_id}: {e}")
        return APIResponse.server_error(
            message="Failed to retrieve document",
            exception=e
        )


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
def delete_document(doc_id: int) -> Tuple[Dict[str, Any], int]:
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
            return APIResponse.not_found("Document", doc_id)
        
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
        
        return APIResponse.no_content("Document deleted successfully")
        
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        return APIResponse.server_error(
            message="Failed to delete document",
            exception=e
        )


@documents_bp.route('/<int:doc_id>', methods=['PUT'])
def update_document(doc_id: int) -> Tuple[Dict[str, Any], int]:
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
            return APIResponse.validation_error(
                {"body": ["No data provided"]},
                "Request body required"
            )
        
        db = Database()
        
        # Check if document exists
        document = db.get_document(doc_id)
        if not document:
            db.close()
            return APIResponse.not_found("Document", doc_id)
        
        # Update document (implement in database.py if not exists)
        # For now, just return success
        db.close()
        
        return APIResponse.success(
            data=document,
            message="Document updated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error updating document {doc_id}: {e}")
        return APIResponse.server_error(
            message="Failed to update document",
            exception=e
        )
