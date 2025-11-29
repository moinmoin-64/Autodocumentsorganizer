"""
Search Blueprint
API-Endpoints für Suche und gespeicherte Suchen
"""
from flask import Blueprint, jsonify, request, current_app
import logging
from typing import Dict, Any

search_bp = Blueprint('search', __name__, url_prefix='/api/search')
logger = logging.getLogger(__name__)


@search_bp.route('/', methods=['POST'])
def search_documents() -> tuple[Dict[str, Any], int]:
    """
    POST /api/search
    Erweiterte Dokumentensuche
    
    Request Body:
        query: Suchbegriff
        category: Kategorie-Filter
        year: Jahr-Filter
        tags: Tag-Filter (Liste)
        date_from: Datum von
        date_to: Datum bis
    
    Returns:
        JSON mit Suchergebnissen
    """
    try:
        from app.database import Database
        from app.search_engine import SearchEngine
        
        data = request.json or {}
        
        # Initialize search engine
        search_engine = SearchEngine()
        
        # Perform search
        results = search_engine.search(
            query=data.get('query', ''),
            category=data.get('category'),
            year=data.get('year'),
            tags=data.get('tags', []),
            date_from=data.get('date_from'),
            date_to=data.get('date_to')
        )
        
        return jsonify({
            'results': results,
            'total': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500


@search_bp.route('/advanced', methods=['POST'])
def advanced_search() -> tuple[Dict[str, Any], int]:
    """
    POST /api/search/advanced
    Semantische Suche mit AI
    
    Returns:
        JSON mit AI-basierten Suchergebnissen
    """
    try:
        from app.search_engine import SearchEngine
        
        data = request.json or {}
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query required'}), 400
        
        search_engine = SearchEngine()
        results = search_engine.semantic_search(query, limit=data.get('limit', 10))
        
        return jsonify({
            'results': results,
            'query': query
        }), 200
        
    except Exception as e:
        logger.error(f"Advanced search error: {e}")
        return jsonify({'error': str(e)}), 500


@search_bp.route('/saved', methods=['GET'])
def get_saved_searches() -> tuple[Dict[str, Any], int]:
    """
    GET /api/search/saved
    Gespeicherte Suchen abrufen
    
    Returns:
        JSON mit gespeicherten Suchen
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
def save_search() -> tuple[Dict[str, Any], int]:
    """
    POST /api/search/saved
    Suche speichern
    
    Request Body:
        name: Name der Suche
        query: Suchbegriff
        filters: Filter-Objekt
    
    Returns:
        JSON mit gespeicherter Suche
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
def delete_saved_search(search_id: int) -> tuple[Dict[str, Any], int]:
    """
    DELETE /api/search/saved/<id>
    Gespeicherte Suche löschen
    
    Args:
        search_id: ID der gespeicherten Suche
    
    Returns:
        JSON mit Erfolgs-Status
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
