"""
Tags Blueprint
API-Endpoints für Tag-Verwaltung
Async & Pydantic Modernized
"""
from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any, Tuple
from pydantic import ValidationError

from app.api_response import APIResponse, ErrorCodes
from app.schemas import TagCreate, TagResponse

tags_bp = Blueprint('tags', __name__, url_prefix='/api/tags')
logger = logging.getLogger(__name__)


@tags_bp.route('/', methods=['GET'])
async def get_all_tags() -> Tuple[Dict[str, Any], int]:
    """
    GET /api/tags
    Alle Tags abrufen
    """
    try:
        from app.database import Database
        
        db = Database()
        tags = db.get_all_tags()
        db.close()
        
        # Validate with Pydantic (optional, but good for consistency)
        # Note: tags is a list of dicts
        validated_tags = [TagResponse.model_validate(t).model_dump() for t in tags]
        
        return jsonify({'tags': validated_tags}), 200
        
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        return jsonify({'error': str(e)}), 500


@tags_bp.route('/', methods=['POST'])
async def create_tag() -> Tuple[Dict[str, Any], int]:
    """
    POST /api/tags
    Neuen Tag erstellen
    """
    try:
        # Validate request body
        try:
            tag_data = TagCreate.model_validate(request.json)
        except ValidationError as e:
            return APIResponse.validation_error(
                {err['loc'][0]: [err['msg']] for err in e.errors()},
                "Validation failed"
            )

        from app.database import Database
        
        db = Database()
        tag_id = db.create_tag(
            name=tag_data.name,
            color=tag_data.color
        )
        db.close()
        
        return jsonify({
            'success': True,
            'id': tag_id,
            'name': tag_data.name,
            'color': tag_data.color
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating tag: {e}")
        return jsonify({'error': str(e)}), 500


@tags_bp.route('/<int:tag_id>', methods=['DELETE'])
async def delete_tag(tag_id: int) -> Tuple[Dict[str, Any], int]:
    """
    DELETE /api/tags/<id>
    Tag löschen
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
async def get_document_tags(doc_id: int) -> Tuple[Dict[str, Any], int]:
    """
    GET /api/tags/document/<id>
    Tags eines Dokuments abrufen
    """
    try:
        from app.database import Database
        
        db = Database()
        tags = db.get_document_tags(doc_id)
        db.close()
        
        # Validate
        validated_tags = [TagResponse.model_validate(t).model_dump() for t in tags]
        
        return jsonify({'tags': validated_tags}), 200
        
    except Exception as e:
        logger.error(f"Error getting document tags: {e}")
        return jsonify({'error': str(e)}), 500


@tags_bp.route('/document/<int:doc_id>', methods=['POST'])
async def add_document_tag(doc_id: int) -> Tuple[Dict[str, Any], int]:
    """
    POST /api/tags/document/<id>
    Tag zu Dokument hinzufügen (per ID oder Name)
    """
    try:
        from app.database import Database
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        tag_id = data.get('tag_id')
        tag_name = data.get('tag_name') or data.get('tag')
        
        if not tag_id and not tag_name:
            return jsonify({'error': 'tag_id or tag_name required'}), 400
        
        db = Database()
        
        # If tag_name provided, find or create tag
        if not tag_id and tag_name:
            all_tags = db.get_all_tags()
            existing_tag = next((t for t in all_tags if t['name'].lower() == tag_name.lower()), None)
            
            if existing_tag:
                tag_id = existing_tag['id']
            else:
                # Validate new tag creation
                try:
                    # Default color if creating by name
                    new_tag = TagCreate(name=tag_name, color='#808080')
                    tag_id = db.create_tag(new_tag.name, new_tag.color)
                except ValidationError as e:
                     return APIResponse.validation_error(
                        {err['loc'][0]: [err['msg']] for err in e.errors()},
                        "Invalid tag name"
                    )

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
async def remove_document_tag(doc_id: int, tag_id: int) -> Tuple[Dict[str, Any], int]:
    """
    DELETE /api/tags/document/<doc_id>/tag/<tag_id>
    Tag von Dokument entfernen
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
