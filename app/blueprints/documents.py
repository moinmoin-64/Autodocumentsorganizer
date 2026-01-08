"""
Documents Blueprint
API-Endpoints für Dokument-Verwaltung
Async & Pydantic Modernized
"""
from flask import Blueprint, jsonify, request, send_file, current_app
from pathlib import Path
import logging
from typing import Dict, Any, Tuple
from pydantic import ValidationError

from app.api_response import APIResponse, ErrorCodes
from app.schemas import DocumentResponse, DocumentUpdate

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')
logger = logging.getLogger(__name__)


@documents_bp.route('', methods=['GET'])
async def list_documents() -> Tuple[Dict[str, Any], int]:
    """
    GET /api/documents
    Liste aller Dokumente mit optionalen Filtern
    """
    try:
        from app.database import Database
        
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
        
        # Database operations (synchronous, but in async route)
        # Ideally, we would run this in an executor if it blocks significantly
        db = Database(current_app.config)
        
        documents = db.search_documents(
            limit=page_size,
            offset=offset,
            **kwargs
        )
        
        total = db.count_documents(**kwargs)
        
        db.close()
        
        # Convert to Pydantic models and back to dict for consistent serialization
        # (This ensures our response matches the schema, even if DB returns extra fields)
        # Note: search_documents returns dicts, so we validate them
        validated_docs = [DocumentResponse.model_validate(doc).model_dump() for doc in documents]
        
        return APIResponse.paginated(
            data=validated_docs,
            total=total,
            page=page,
            page_size=page_size,
            message="Documents retrieved successfully"
        )
        
    except ValidationError as e:
        return APIResponse.validation_error(
            {err['loc'][0]: [err['msg']] for err in e.errors()},
            "Response validation failed"
        )
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return APIResponse.server_error(
            message="Failed to retrieve documents",
            exception=e
        )


@documents_bp.route('/<int:doc_id>', methods=['GET'])
async def get_document(doc_id: int) -> Tuple[Dict[str, Any], int]:
    """
    GET /api/documents/<id>
    Einzelnes Dokument abrufen
    """
    try:
        from app.database import Database
        
        db = Database(current_app.config)
        document = db.get_document(doc_id)
        db.close()
        
        if not document:
            return APIResponse.not_found("Document", doc_id)
        
        # Validate with Pydantic
        validated_doc = DocumentResponse.model_validate(document).model_dump()
        
        return APIResponse.success(
            data=validated_doc,
            message="Document retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting document {doc_id}: {e}")
        return APIResponse.server_error(
            message="Failed to retrieve document",
            exception=e
        )


@documents_bp.route('/<int:doc_id>/download', methods=['GET'])
async def download_document(doc_id: int):
    """
    GET /api/documents/<id>/download
    Dokument herunterladen
    """
    try:
        from app.database import Database
        
        db = Database(current_app.config)
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
async def delete_document(doc_id: int) -> Tuple[Dict[str, Any], int]:
    """
    DELETE /api/documents/<id>
    Dokument löschen
    """
    try:
        from app.database import Database
        
        db = Database(current_app.config)
        
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
async def update_document(doc_id: int) -> Tuple[Dict[str, Any], int]:
    """
    PUT /api/documents/<id>
    Dokument-Metadaten aktualisieren
    """
    try:
        # Validate request body with Pydantic
        try:
            update_data = DocumentUpdate.model_validate(request.json)
        except ValidationError as e:
            return APIResponse.validation_error(
                {err['loc'][0]: [err['msg']] for err in e.errors()},
                "Validation failed"
            )

        # Ensure request is not empty
        if not update_data.model_dump(exclude_unset=True):
            return APIResponse.validation_error(
                {}, "Request body cannot be empty."
            )

        from app.database import Database
        
        db = Database(current_app.config)
        
        # Check if document exists
        document = db.get_document(doc_id)
        if not document:
            db.close()
            return APIResponse.not_found("Document", doc_id)
        
        # Update document in database
        try:
            # Prepare update data - only include fields that were provided
            update_data = {}
            if hasattr(data, 'filename') and data.filename:
                update_data['filename'] = data.filename
            if hasattr(data, 'category') and data.category:
                update_data['category'] = data.category
            if hasattr(data, 'date_document') and data.date_document:
                update_data['date_document'] = data.date_document
            if hasattr(data, 'summary') and data.summary:
                update_data['summary'] = data.summary
            
            # Update in database
            success = db.update_document(doc_id, update_data)
            
            if not success:
                logger.warning(f"Update failed for document {doc_id}")
                db.close()
                return APIResponse.server_error("Update failed")
            
            # Fetch updated document
            updated_doc = db.get_document(doc_id)
            db.close()
            
            return APIResponse.success(
                data=updated_doc,
                message="Document updated successfully"
            )
        except KeyError as e:
            logger.error(f"Missing required field: {e}")
            db.close()
            return APIResponse.validation_error({str(e): ["This field is required"]})
        
    except Exception as e:
        logger.error(f"Error updating document {doc_id}: {e}")
        return APIResponse.server_error(
            message="Failed to update document",
            exception=e
        )
