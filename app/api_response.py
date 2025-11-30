"""
API Response Helper - Konsistente Antwort-Formate
"""
from flask import jsonify
from typing import Any, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class APIResponse:
    """
    Standardisierte API-Antworten mit konsistentem Format
    """
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200) -> Tuple[Dict, int]:
        """
        Erfolgreiche Antwort
        
        Args:
            data: Response-Daten
            message: Erfolgs-Nachricht
            status_code: HTTP Status Code
            
        Returns:
            Tuple (response_dict, status_code)
        """
        response = {
            "success": True,
            "message": message,
            "data": data
        }
        return jsonify(response), status_code
    
    @staticmethod
    def error(message: str, error_code: str = "UNKNOWN_ERROR", 
              status_code: int = 400, details: Optional[Dict] = None) -> Tuple[Dict, int]:
        """
        Fehler-Antwort
        
        Args:
            message: Benutzerfreundliche Fehlermeldung
            error_code: Maschinenlesbarer Error-Code
            status_code: HTTP Status Code
            details: Zusätzliche Fehler-Details
            
        Returns:
            Tuple (response_dict, status_code)
        """
        response = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message
            }
        }
        
        if details:
            response["error"]["details"] = details
            
        logger.error(f"API Error {error_code}: {message}")
        return jsonify(response), status_code
    
    @staticmethod
    def paginated(data: list, total: int, page: int = 1, 
                  page_size: int = 20, message: str = "Success") -> Tuple[Dict, int]:
        """
        Paginierte Antwort
        
        Args:
            data: Liste der Daten für aktuelle Seite
            total: Gesamtanzahl der Einträge
            page: Aktuelle Seite
            page_size: Einträge pro Seite
            message: Erfolgs-Nachricht
            
        Returns:
            Tuple (response_dict, status_code)
        """
        total_pages = (total + page_size - 1) // page_size
        
        response = {
            "success": True,
            "message": message,
            "data": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        return jsonify(response), 200
    
    @staticmethod
    def created(data: Any, message: str = "Resource created", 
                location: Optional[str] = None) -> Tuple[Dict, int]:
        """
        Resource erfolgreich erstellt (201 Created)
        
        Args:
            data: Erstellte Resource
            message: Erfolgs-Nachricht
            location: URL der neuen Resource
            
        Returns:
            Tuple (response_dict, status_code)
        """
        response, _ = APIResponse.success(data, message, 201)
        
        if location:
            response.headers['Location'] = location
            
        return response, 201
    
    @staticmethod
    def no_content(message: str = "Success") -> Tuple[str, int]:
        """
        Erfolgreiche Operation ohne Response-Body (204 No Content)
        
        Args:
            message: Log-Nachricht
            
        Returns:
            Tuple (empty_string, 204)
        """
        logger.info(message)
        return '', 204
    
    @staticmethod
    def not_found(resource: str = "Resource", resource_id: Any = None) -> Tuple[Dict, int]:
        """
        Resource nicht gefunden (404)
        
        Args:
            resource: Typ der Resource (z.B. "Document", "User")
            resource_id: ID der gesuchten Resource
            
        Returns:
            Tuple (response_dict, 404)
        """
        message = f"{resource} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
            
        return APIResponse.error(
            message=message,
            error_code="NOT_FOUND",
            status_code=404
        )
    
    @staticmethod
    def unauthorized(message: str = "Authentication required") -> Tuple[Dict, int]:
        """
        Nicht authentifiziert (401)
        """
        return APIResponse.error(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401
        )
    
    @staticmethod
    def forbidden(message: str = "Access denied") -> Tuple[Dict, int]:
        """
        Keine Berechtigung (403)
        """
        return APIResponse.error(
            message=message,
            error_code="FORBIDDEN",
            status_code=403
        )
    
    @staticmethod
    def validation_error(errors: Dict[str, list], 
                        message: str = "Validation failed") -> Tuple[Dict, int]:
        """
        Validierungs-Fehler (422)
        
        Args:
            errors: Dict von Feldnamen zu Fehlerlisten
            message: Haupt-Fehlermeldung
            
        Returns:
            Tuple (response_dict, 422)
        """
        return APIResponse.error(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details={"fields": errors}
        )
    
    @staticmethod
    def server_error(message: str = "Internal server error", 
                    exception: Optional[Exception] = None) -> Tuple[Dict, int]:
        """
        Server-Fehler (500)
        
        Args:
            message: Benutzerfreundliche Fehlermeldung
            exception: Original-Exception (für Logging)
            
        Returns:
            Tuple (response_dict, 500)
        """
        if exception:
            logger.exception(f"Server Error: {exception}")
            
        return APIResponse.error(
            message=message,
            error_code="SERVER_ERROR",
            status_code=500
        )


# Error Codes Konstanten
class ErrorCodes:
    """Maschinenlesbare Error-Codes"""
    
    # Client Errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    DUPLICATE = "DUPLICATE_RESOURCE"
    INVALID_REQUEST = "INVALID_REQUEST"
    
    # Server Errors (5xx)
    SERVER_ERROR = "SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
