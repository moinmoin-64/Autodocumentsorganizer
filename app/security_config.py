"""
Security Configuration
CORS, Rate Limiting, Input Sanitization
"""
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from markupsafe import escape
import re


def setup_security(app):
    """
    Konfiguriert Security-Features
    
    Args:
        app: Flask Application
    """
    
    # CORS Configuration (Restrictive)
    allowed_origins = [
        'http://localhost:3000',  # Development
        'http://localhost:5001',  # Local Backend
        'http://127.0.0.1:5001',
        # Add production domains here
    ]
    
    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Range", "X-Total-Count"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })
    
    # Rate Limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",  # Use Redis in production!
        strategy="fixed-window"
    )
    
    # Specific rate limits
    @app.route('/api/upload', methods=['POST'])
    @limiter.limit("10 per minute")
    def rate_limited_upload():
        pass  # Placeholder
    
    @app.route('/api/search', methods=['GET'])
    @limiter.limit("30 per minute")
    def rate_limited_search():
        pass  # Placeholder
    
    app.logger.info('Security features configured')
    return limiter


class InputSanitizer:
    """Helper class for input sanitization"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = filename.split('/')[-1].split('\\')[-1]
        
        # Remove dangerous characters
        filename = re.sub(r'[^\w\s\-\.]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')
        
        return filename
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Sanitize user text input (prevent XSS)
        
        Args:
            text: User input text
            
        Returns:
            Sanitized text
        """
        return str(escape(text))
    
    @staticmethod
    def validate_category(category: str) -> bool:
        """
        Validate category name
        
        Args:
            category: Category name
            
        Returns:
            True if valid
        """
        # Only alphanumeric, spaces, hyphens, underscores
        return bool(re.match(r'^[\w\s\-]+$', category)) and len(category) <= 100
    
    @staticmethod
    def validate_year(year: int) -> bool:
        """
        Validate year parameter
        
        Args:
            year: Year to validate
            
        Returns:
            True if valid
        """
        return 1900 <= year <= 2100


# Security Headers Middleware
def add_security_headers(response):
    """
    Add security headers to all responses
    
    Args:
        response: Flask response object
        
    Returns:
        Modified response
    """
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # CSP (Content Security Policy)
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'"
    )
    
    return response
