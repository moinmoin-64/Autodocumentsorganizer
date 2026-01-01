"""
API Versioning & Response Standardization
Implements versioned endpoints with consistent response format
"""

from flask import Blueprint, jsonify, request
from typing import Dict, Any, Optional, List, Tuple
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# API Version
API_VERSION = "v1"
API_VERSION_DEPRECATED = "v0"  # Legacy endpoints (gradual deprecation)


class APIVersioning:
    """
    API Versioning decorator and utilities
    Supports multiple API versions with deprecation warnings
    """
    
    @staticmethod
    def get_version_from_request() -> str:
        """Extract API version from request path"""
        path = request.path
        # Check for /api/v1/, /api/v2/, etc.
        if '/api/v' in path:
            parts = path.split('/api/')
            if len(parts) > 1:
                version_part = parts[1].split('/')[0]
                if version_part.startswith('v'):
                    return version_part
        return API_VERSION  # Default to latest
    
    @staticmethod
    def version_endpoint(min_version="v1", deprecated_in=None):
        """
        Decorator to specify API version for an endpoint
        
        Args:
            min_version: Minimum supported version
            deprecated_in: Version where this endpoint was deprecated
        """
        def decorator(f):
            @wraps(f)
            async def decorated_function(*args, **kwargs):
                current_version = APIVersioning.get_version_from_request()
                
                # Check version compatibility
                min_v = int(min_version[1:])
                current_v = int(current_version[1:])
                
                if current_v < min_v:
                    return jsonify({
                        "success": False,
                        "error": "INVALID_API_VERSION",
                        "message": f"API version {current_version} is not supported for this endpoint. Minimum: {min_version}",
                        "suggested_version": API_VERSION
                    }), 400
                
                # Add deprecation warning header if applicable
                response = await f(*args, **kwargs)
                if deprecated_in and current_version == deprecated_in:
                    if isinstance(response, tuple):
                        headers = response[1] if len(response) > 1 else {}
                        if isinstance(headers, dict):
                            headers['Deprecation'] = 'true'
                            headers['Sunset'] = 'Fri, 31 Dec 2026 23:59:59 GMT'
                
                return response
            
            return decorated_function
        return decorator


class StandardizedResponse:
    """
    Standardized API Response Format
    All endpoints return consistent JSON structure
    """
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        pagination: Optional[Dict] = None,
        meta: Optional[Dict] = None,
        status_code: int = 200
    ) -> Tuple[Dict, int]:
        """
        Success response with standard format
        
        Response format:
        {
            "success": true,
            "data": {...},
            "pagination": {...},
            "meta": {...},
            "timestamp": "2025-12-31T23:59:59Z"
        }
        """
        response = {
            "success": True,
            "data": data,
            "message": message,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat() + 'Z'
        }
        
        if pagination:
            response["pagination"] = pagination
        
        if meta:
            response["meta"] = meta
        
        return jsonify(response), status_code
    
    @staticmethod
    def error(
        error_code: str,
        message: str,
        details: Optional[Dict] = None,
        status_code: int = 400,
        suggestion: Optional[str] = None
    ) -> Tuple[Dict, int]:
        """
        Error response with standard format
        
        Response format:
        {
            "success": false,
            "error": "ERROR_CODE",
            "message": "User-friendly message",
            "details": {...},
            "suggestion": "What to do next"
        }
        """
        response = {
            "success": False,
            "error": error_code,
            "message": message,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat() + 'Z'
        }
        
        if details:
            response["details"] = details
        
        if suggestion:
            response["suggestion"] = suggestion
        
        logger.warning(f"API Error {status_code}: {error_code} - {message}")
        
        return jsonify(response), status_code
    
    @staticmethod
    def paginate(
        items: List[Dict],
        page: int = 1,
        page_size: int = 20,
        total: int = None
    ) -> Dict:
        """
        Generate pagination metadata
        
        Returns:
        {
            "current_page": 1,
            "page_size": 20,
            "total": 100,
            "total_pages": 5,
            "has_next": true,
            "has_previous": false
        }
        """
        total = total or len(items)
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "current_page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
            "from": (page - 1) * page_size + 1,
            "to": min(page * page_size, total)
        }


class APIErrorCodes:
    """Standardized error codes for API"""
    
    # Client Errors (4xx)
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    INVALID_API_VERSION = "INVALID_API_VERSION"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DUPLICATE = "DUPLICATE_RESOURCE"
    RATE_LIMITED = "RATE_LIMITED"
    
    # Server Errors (5xx)
    INTERNAL_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "REQUEST_TIMEOUT"


def create_versioned_blueprint(name: str, import_name: str, version: str = "v1"):
    """
    Create a versioned blueprint
    
    Usage:
        documents_bp = create_versioned_blueprint('documents', __name__, 'v1')
        
        @documents_bp.route('/list')
        def list_documents():
            return StandardizedResponse.success(data=[...])
    """
    bp = Blueprint(name, import_name, url_prefix=f'/api/{version}/{name}')
    bp.version = version
    return bp


# Migration Helper: v0 → v1 Response Adapter
class ResponseAdapter:
    """
    Adapts old API responses (v0) to new format (v1)
    Used during migration period
    """
    
    @staticmethod
    def adapt_list_response(old_response: Dict, endpoint: str) -> Dict:
        """
        Adapt legacy list endpoint response
        
        OLD:
        {
            "documents": [...],
            "total": 100
        }
        
        NEW:
        {
            "success": true,
            "data": [...],
            "pagination": {...}
        }
        """
        items = old_response.get('documents', old_response.get('data', []))
        total = old_response.get('total', len(items))
        
        return {
            "success": True,
            "data": items,
            "pagination": StandardizedResponse.paginate(
                items, 
                total=total
            ),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat() + 'Z'
        }


# Example usage documentation
"""
# OLD CODE (v0)
@app.route('/api/documents')
def list_documents():
    docs = db.get_documents()
    return jsonify({
        "documents": docs,
        "total": len(docs)
    })

# NEW CODE (v1)
documents_bp = create_versioned_blueprint('documents', __name__, 'v1')

@documents_bp.route('/list', methods=['GET'])
@APIVersioning.version_endpoint(min_version='v1')
async def list_documents():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    
    db = Database()
    docs = db.search_documents(limit=page_size, offset=(page-1)*page_size)
    total = db.count_documents()
    db.close()
    
    return StandardizedResponse.success(
        data=docs,
        pagination=StandardizedResponse.paginate(docs, page, page_size, total),
        status_code=200
    )

# Register versioned blueprint
app.register_blueprint(documents_bp)

# Result: GET /api/v1/documents/list
# Response:
# {
#     "success": true,
#     "data": [...],
#     "pagination": {
#         "current_page": 1,
#         "page_size": 20,
#         "total": 100,
#         "has_next": true
#     },
#     "timestamp": "2025-12-31T23:59:59Z"
# }
"""
