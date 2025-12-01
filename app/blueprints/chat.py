"""
Chat Blueprint
API-Endpoints für Chatbot (Ollama Integration)
Async & Pydantic Modernized
"""
from flask import Blueprint, jsonify, request
import logging
import asyncio
from typing import Dict, Any, Tuple

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')
logger = logging.getLogger(__name__)


@chat_bp.route('/', methods=['POST'])
async def chat() -> Tuple[Dict[str, Any], int]:
    """
    POST /api/chat
    Chat mit Ollama LLM
    """
    try:
        from app.ollama_client import OllamaClient
        from app.database import Database
        from app.search_engine import SearchEngine
        
        data = request.json or {}
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        # Initialize Ollama client (fast, just config)
        ollama = OllamaClient()
        
        if not ollama.available:
            return jsonify({
                'error': 'Ollama not available',
                'response': 'Der Chatbot ist momentan nicht verfügbar. Bitte stelle sicher, dass Ollama läuft.'
            }), 503
        
        # Build context from database if requested
        context = ""
        if data.get('include_context', True):
            # Run search in thread to avoid blocking event loop
            try:
                def get_context():
                    db = Database()
                    search_engine = SearchEngine()
                    results = search_engine.semantic_search(message, limit=3)
                    db.close()
                    return results

                results = await asyncio.to_thread(get_context)
                
                if results:
                    context = "Relevante Dokumente:\n"
                    for i, doc in enumerate(results, 1):
                        context += f"{i}. {doc.get('filename', 'Unknown')}\n"
                        if doc.get('full_text'):
                            context += f"   {doc['full_text'][:200]}...\n"
            except Exception as e:
                logger.warning(f"Context search failed: {e}")
        
        # Get LLM response (blocking I/O)
        full_message = f"{context}\n\nFrage: {message}" if context else message
        
        # Run Ollama chat in thread
        response = await asyncio.to_thread(ollama.chat, full_message)
        
        return jsonify({
            'response': response,
            'context_used': bool(context)
        }), 200
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/status', methods=['GET'])
async def get_status() -> Tuple[Dict[str, Any], int]:
    """
    GET /api/chat/status
    Ollama-Status prüfen
    """
    try:
        from app.ollama_client import OllamaClient
        
        # Run in thread as it makes a request to Ollama
        def check_status():
            ollama = OllamaClient()
            return {
                'available': ollama.available,
                'url': ollama.url,
                'models': ollama.list_models() if ollama.available else []
            }
            
        status = await asyncio.to_thread(check_status)
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error getting Ollama status: {e}")
        return jsonify({'error': str(e)}), 500
