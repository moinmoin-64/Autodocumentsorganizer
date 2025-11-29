"""
Chat Blueprint
API-Endpoints für Chatbot (Ollama Integration)
"""
from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')
logger = logging.getLogger(__name__)


@chat_bp.route('/', methods=['POST'])
def chat() -> tuple[Dict[str, Any], int]:
    """
    POST /api/chat
    Chat mit Ollama LLM
    
    Request Body:
        message: Benutzer-Nachricht
        context: Optional - Dokument-Kontext
    
    Returns:
        JSON mit LLM-Antwort
    """
    try:
        from app.ollama_client import OllamaClient
        from app.database import Database
        
        data = request.json or {}
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        # Initialize Ollama client
        ollama = OllamaClient()
        
        if not ollama.available:
            return jsonify({
                'error': 'Ollama not available',
                'response': 'Der Chatbot ist momentan nicht verfügbar. Bitte stelle sicher, dass Ollama läuft.'
            }), 503
        
        # Build context from database if requested
        context = ""
        if data.get('include_context', True):
            db = Database()
            
            # Search for relevant documents
            from app.search_engine import SearchEngine
            search_engine = SearchEngine()
            
            try:
                results = search_engine.semantic_search(message, limit=3)
                if results:
                    context = "Relevante Dokumente:\n"
                    for i, doc in enumerate(results, 1):
                        context += f"{i}. {doc.get('filename', 'Unknown')}\n"
                        if doc.get('full_text'):
                            context += f"   {doc['full_text'][:200]}...\n"
            except Exception as e:
                logger.warning(f"Context search failed: {e}")
            
            db.close()
        
        # Get LLM response
        full_message = f"{context}\n\nFrage: {message}" if context else message
        response = ollama.chat(full_message)
        
        return jsonify({
            'response': response,
            'context_used': bool(context)
        }), 200
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/status', methods=['GET'])
def get_status() -> tuple[Dict[str, Any], int]:
    """
    GET /api/chat/status
    Ollama-Status prüfen
    
    Returns:
        JSON mit Status-Informationen
    """
    try:
        from app.ollama_client import OllamaClient
        
        ollama = OllamaClient()
        
        return jsonify({
            'available': ollama.available,
            'url': ollama.url,
            'models': ollama.list_models() if ollama.available else []
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting Ollama status: {e}")
        return jsonify({'error': str(e)}), 500
