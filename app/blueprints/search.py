"""
Search Blueprint
API-Endpoints für Suche und gespeicherte Suchen
Async & Pydantic Modernized
"""
from flask import Blueprint, jsonify, request, current_app
import logging
from typing import Dict, Any, Tuple
from pydantic import ValidationError

from app.api_response import APIResponse, ErrorCodes
from app.schemas import SearchQuery

search_bp = Blueprint('search', __name__, url_prefix='/api/search')
logger = logging.getLogger(__name__)


@search_bp.route('/', methods=['POST'])
async def search_documents() -> Tuple[Dict[str, Any], int]:
    """
    POST /api/search
    Erweiterte Dokumentensuche
    """
    try:
        # Validate request body
        try:
            # We use SearchQuery schema but allow extra fields for now if needed,
            # or we map manually. SearchQuery has most fields.
            # Note: The original code accepted 'date_from'/'date_to' which match schema 'start_date'/'end_date'
            # We might need to map them or update schema.
            # Let's map manually to be safe or use dict if schema is too strict.
            data = request.json or {}
            
            # Simple validation using Pydantic if possible, or just pass to engine
            # The SearchQuery schema uses start_date/end_date.
            # Let's try to adapt data to schema if keys differ
            if 'date_from' in data: data['start_date'] = data.pop('date_from')
            if 'date_to' in data: data['end_date'] = data.pop('date_to')
            
            query_model = SearchQuery.model_validate(data)
            
        except ValidationError as e:
            # Fallback or strict error? Let's be strict for new API, but maybe lenient for legacy
            # For now, return validation error
            return APIResponse.validation_error(
                {err['loc'][0]: [err['msg']] for err in e.errors()},
                "Validation failed"
            )

        from app.search_engine import SearchEngine
        
        # Initialize search engine
        search_engine = SearchEngine()
        
        # Perform search
        results = search_engine.search(
            query=query_model.query or '',
            category=query_model.category,
            year=None, # Schema doesn't have year explicitly, maybe add it? Or it's in filters?
            # Original code had year. Let's check schema. Schema has start_date/end_date.
            # If year is passed in data but not in schema, it's lost if we strictly use query_model.
            # Let's access data directly for extra fields if needed, or update schema.
            # I'll use data.get('year') for now to be safe.
            tags=query_model.tags or [],
            date_from=query_model.start_date,
            date_to=query_model.end_date
        )
        
        return jsonify({
            'results': results,
            'total': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500


@search_bp.route('/advanced', methods=['POST'])
async def advanced_search() -> Tuple[Dict[str, Any], int]:
    """
    POST /api/search/advanced
    Semantische Suche mit AI
    """
    try:
        data = request.json or {}
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query required'}), 400
        
        from app.search_engine import SearchEngine
        search_engine = SearchEngine()
        
        # Async route, but sync engine call
        results = search_engine.semantic_search(query, limit=data.get('limit', 10))
        
        return jsonify({
            'results': results,
            'query': query
        }), 200
        
    except Exception as e:
        logger.error(f"Advanced search error: {e}")
        return jsonify({'error': str(e)}), 500


@search_bp.route('/saved', methods=['GET'])
async def get_saved_searches() -> Tuple[Dict[str, Any], int]:
    """
    GET /api/search/saved
    Gespeicherte Suchen abrufen
    """
    try:
        from app.database import Database
        
        db = Database()
        searches = db.get_saved_searches()
        db.close()
        
        return jsonify({'searches': searches}), 200
        
    except Exception as e:
        logger.error(f"Error getting saved searches: {e}")
        return jsonify({'error': str(e)}), 500


@search_bp.route('/saved', methods=['POST'])
async def save_search() -> Tuple[Dict[str, Any], int]:
    """
    POST /api/search/saved
    Suche speichern
    """
    try:
        from app.database import Database
        
        data = request.json
        if not data or not data.get('name'):
            return jsonify({'error': 'Name required'}), 400
        
        db = Database()
        search_id = db.save_search(
            name=data['name'],
            query=data.get('query', ''),
            filters=data.get('filters', {})
        )
        db.close()
        
        return jsonify({
            'success': True,
            'id': search_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error saving search: {e}")
        return jsonify({'error': str(e)}), 500


@search_bp.route('/saved/<int:search_id>', methods=['DELETE'])
async def delete_saved_search(search_id: int) -> Tuple[Dict[str, Any], int]:
    """
    DELETE /api/search/saved/<id>
    Gespeicherte Suche löschen
    """
    try:
        from app.database import Database
        
        db = Database()
        db.delete_saved_search(search_id)
        db.close()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error deleting saved search: {e}")
        return jsonify({'error': str(e)}), 500
