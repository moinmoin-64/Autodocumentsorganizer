"""
OAuth2 & API Key Management
Authentication via OAuth2, API Keys, and JWT tokens
"""

import os
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from authlib.integrations.flask_client import OAuth
from authlib.integrations.flask_oauth2 import current_token
from authlib.oauth2.rfc6749 import ClientSecretBasic
import secrets
import hashlib
from app.database import db
from app.models import User
import jwt

logger = logging.getLogger(__name__)


# ============================================================================
# OAuth2 Configuration
# ============================================================================

class OAuth2Config:
    """OAuth2 Konfiguration für externe Providers"""
    
    # Google OAuth2
    GOOGLE = {
        'name': 'Google',
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
        'token_url': 'https://accounts.google.com/o/oauth2/token',
        'userinfo_url': 'https://www.googleapis.com/oauth2/v1/userinfo',
    }
    
    # Microsoft OAuth2
    MICROSOFT = {
        'name': 'Microsoft',
        'client_id': os.getenv('MICROSOFT_CLIENT_ID'),
        'client_secret': os.getenv('MICROSOFT_CLIENT_SECRET'),
        'authorize_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
        'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
        'userinfo_url': 'https://graph.microsoft.com/v1.0/me',
    }
    
    # GitHub OAuth2
    GITHUB = {
        'name': 'GitHub',
        'client_id': os.getenv('GITHUB_CLIENT_ID'),
        'client_secret': os.getenv('GITHUB_CLIENT_SECRET'),
        'authorize_url': 'https://github.com/login/oauth/authorize',
        'token_url': 'https://github.com/login/oauth/access_token',
        'userinfo_url': 'https://api.github.com/user',
    }


# ============================================================================
# API Key Management
# ============================================================================

class APIKey:
    """API Key Model"""
    
    def __init__(self, user_id: int, name: str, permissions: list = None):
        self.user_id = user_id
        self.name = name
        self.permissions = permissions or ['read', 'write']
        self.created_at = datetime.utcnow()
        self.last_used = None
        self.is_active = True
        
        # Generate key
        key_bytes = secrets.token_bytes(32)
        self.key_hash = hashlib.sha256(key_bytes).hexdigest()
        self.key_display = self._format_key(key_bytes)
    
    @staticmethod
    def _format_key(key_bytes: bytes) -> str:
        """Formatiert Key für Anzeige (nur Anfang und Ende sichtbar)"""
        key_hex = key_bytes.hex()
        return f"{key_hex[:8]}...{key_hex[-8:]}"
    
    @staticmethod
    def generate() -> Tuple[str, str]:
        """
        Generiert neuen API Key
        
        Returns:
            Tuple (display_key, full_key)
        """
        key_bytes = secrets.token_bytes(32)
        key_hex = key_bytes.hex()
        key_hash = hashlib.sha256(key_bytes).hexdigest()
        
        display_key = f"{key_hex[:8]}...{key_hex[-8:]}"
        
        return display_key, key_hex
    
    @staticmethod
    def hash_key(key: str) -> str:
        """Hashed API Key"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    @staticmethod
    def verify(key: str, key_hash: str) -> bool:
        """Verifiziert API Key gegen Hash"""
        return APIKey.hash_key(key) == key_hash


# ============================================================================
# JWT Token Management
# ============================================================================

class JWTTokenManager:
    """Verwaltet JWT Tokens"""
    
    SECRET_KEY = os.getenv('SECRET_KEY')
    ALGORITHM = 'HS256'
    EXPIRATION_HOURS = 24
    REFRESH_EXPIRATION_DAYS = 30
    
    @classmethod
    def create_access_token(cls, user_id: int, scopes: list = None) -> str:
        """
        Erstellt Access Token
        
        Args:
            user_id: User ID
            scopes: Liste von Scopes
        
        Returns:
            JWT Token
        """
        scopes = scopes or ['read', 'write']
        
        payload = {
            'user_id': user_id,
            'scopes': scopes,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=cls.EXPIRATION_HOURS),
            'type': 'access',
        }
        
        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return token
    
    @classmethod
    def create_refresh_token(cls, user_id: int) -> str:
        """
        Erstellt Refresh Token
        
        Args:
            user_id: User ID
        
        Returns:
            JWT Token
        """
        payload = {
            'user_id': user_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=cls.REFRESH_EXPIRATION_DAYS),
            'type': 'refresh',
        }
        
        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return token
    
    @classmethod
    def verify_token(cls, token: str) -> Optional[Dict]:
        """
        Verifiziert JWT Token
        
        Args:
            token: JWT Token
        
        Returns:
            Decoded payload oder None
        """
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            return None


# ============================================================================
# Authentication Decorators
# ============================================================================

def require_api_key(f):
    """Decorator für API Key Authentifizierung"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API Key from header
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Verify API Key
        from app.models import APIKeyModel
        
        try:
            key_model = db.session.query(APIKeyModel).filter_by(
                key_hash=APIKey.hash_key(api_key)
            ).first()
            
            if not key_model or not key_model.is_active:
                return jsonify({'error': 'Invalid API key'}), 401
            
            # Update last used
            key_model.last_used = datetime.utcnow()
            db.session.commit()
            
            # Set user in g
            g.user = key_model.user
            g.api_key = key_model
            
            return f(*args, **kwargs)
        
        except Exception as e:
            logger.error(f"API key verification failed: {e}")
            return jsonify({'error': 'Authentication failed'}), 500
    
    return decorated_function


def require_jwt_token(f):
    """Decorator für JWT Token Authentifizierung"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'JWT token required'}), 401
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Verify token
        payload = JWTTokenManager.verify_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Get user
        user = User.query.get(payload['user_id'])
        
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        # Set user in g
        g.user = user
        g.token_payload = payload
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_oauth2(f):
    """Decorator für OAuth2 Authentifizierung"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_token:
            return jsonify({'error': 'OAuth2 token required'}), 401
        
        g.user = current_token.user
        
        return f(*args, **kwargs)
    
    return decorated_function


# ============================================================================
# OAuth2 Provider Setup
# ============================================================================

class OAuth2Provider:
    """OAuth2 Provider Integration"""
    
    def __init__(self, app=None):
        self.app = app
        self.oauth = OAuth()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialisiert OAuth2 für Flask App"""
        self.oauth.init_app(app)
        
        # Google
        if OAuth2Config.GOOGLE['client_id']:
            self.google = self.oauth.register(
                name='google',
                client_id=OAuth2Config.GOOGLE['client_id'],
                client_secret=OAuth2Config.GOOGLE['client_secret'],
                server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                client_kwargs={'scope': 'openid email profile'}
            )
        
        # Microsoft
        if OAuth2Config.MICROSOFT['client_id']:
            self.microsoft = self.oauth.register(
                name='microsoft',
                client_id=OAuth2Config.MICROSOFT['client_id'],
                client_secret=OAuth2Config.MICROSOFT['client_secret'],
                server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
                client_kwargs={'scope': 'openid email profile'}
            )
        
        # GitHub
        if OAuth2Config.GITHUB['client_id']:
            self.github = self.oauth.register(
                name='github',
                client_id=OAuth2Config.GITHUB['client_id'],
                client_secret=OAuth2Config.GITHUB['client_secret'],
                access_token_url='https://github.com/login/oauth/access_token',
                access_token_params=None,
                authorize_url='https://github.com/login/oauth/authorize',
                authorize_params=None,
                api_base_url='https://api.github.com/',
                client_kwargs={'scope': 'user:email'},
            )


# ============================================================================
# OAuth2 Routes
# ============================================================================

def setup_oauth2_routes(app, oauth2_provider):
    """Initialisiert OAuth2 Routes"""
    
    @app.route('/auth/oauth/<provider>/login')
    def oauth_login(provider: str):
        """OAuth2 Login Redirect"""
        oauth = getattr(oauth2_provider, provider, None)
        
        if not oauth:
            return jsonify({'error': f'Provider {provider} not configured'}), 400
        
        redirect_uri = request.host_url.rstrip('/') + f'/auth/oauth/{provider}/callback'
        
        return oauth.authorize_redirect(redirect_uri)
    
    @app.route('/auth/oauth/<provider>/callback')
    def oauth_callback(provider: str):
        """OAuth2 Callback Handler"""
        oauth = getattr(oauth2_provider, provider, None)
        
        if not oauth:
            return jsonify({'error': f'Provider {provider} not configured'}), 400
        
        try:
            token = oauth.authorize_access_token()
            
            # Get user info
            if provider == 'google':
                user_info = token.get('userinfo')
            elif provider == 'microsoft':
                resp = oauth.get('me', token=token)
                user_info = resp.json()
            elif provider == 'github':
                resp = oauth.get('user', token=token)
                user_info = resp.json()
            else:
                return jsonify({'error': 'Unknown provider'}), 400
            
            # Create or update user
            email = user_info.get('email') or user_info.get('login')
            
            user = User.query.filter_by(email=email).first()
            
            if not user:
                user = User(
                    email=email,
                    name=user_info.get('name') or user_info.get('login'),
                    oauth_provider=provider,
                    oauth_id=user_info.get('id'),
                )
                db.session.add(user)
            else:
                user.oauth_provider = provider
                user.oauth_id = user_info.get('id')
            
            db.session.commit()
            
            # Create JWT token
            access_token = JWTTokenManager.create_access_token(user.id)
            refresh_token = JWTTokenManager.create_refresh_token(user.id)
            
            # Return tokens
            return jsonify({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
            }), 200
        
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return jsonify({'error': 'Authentication failed'}), 500
    
    @app.route('/auth/refresh', methods=['POST'])
    def refresh_token():
        """Refresh Access Token"""
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token required'}), 400
        
        payload = JWTTokenManager.verify_token(refresh_token)
        
        if not payload or payload.get('type') != 'refresh':
            return jsonify({'error': 'Invalid refresh token'}), 401
        
        # Create new access token
        access_token = JWTTokenManager.create_access_token(payload['user_id'])
        
        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer',
        }), 200
    
    logger.info("✅ OAuth2 routes setup complete")


# ============================================================================
# API Key Management Routes
# ============================================================================

def setup_api_key_routes(app):
    """Initialisiert API Key Management Routes"""
    
    @app.route('/api/keys', methods=['GET'])
    @require_jwt_token
    def list_api_keys():
        """Listet API Keys des Users"""
        from app.models import APIKeyModel
        
        keys = db.session.query(APIKeyModel).filter_by(
            user_id=g.user.id
        ).all()
        
        return jsonify([
            {
                'id': k.id,
                'name': k.name,
                'key': k.key_display,
                'created_at': k.created_at.isoformat(),
                'last_used': k.last_used.isoformat() if k.last_used else None,
                'is_active': k.is_active,
            }
            for k in keys
        ]), 200
    
    @app.route('/api/keys', methods=['POST'])
    @require_jwt_token
    def create_api_key():
        """Erstellt neuen API Key"""
        from app.models import APIKeyModel
        
        data = request.get_json()
        name = data.get('name')
        permissions = data.get('permissions', ['read', 'write'])
        
        if not name:
            return jsonify({'error': 'Name required'}), 400
        
        display_key, full_key = APIKey.generate()
        
        api_key = APIKeyModel(
            user_id=g.user.id,
            name=name,
            key_hash=APIKey.hash_key(full_key),
            permissions=permissions,
            key_display=display_key,
        )
        
        db.session.add(api_key)
        db.session.commit()
        
        # Only return full key once
        return jsonify({
            'id': api_key.id,
            'name': api_key.name,
            'key': full_key,  # Nur beim ersten Mal sichtbar!
            'key_display': display_key,
            'created_at': api_key.created_at.isoformat(),
            'message': '⚠️ Speichere den Key sofort - er wird nicht wieder angezeigt!'
        }), 201
    
    @app.route('/api/keys/<int:key_id>', methods=['DELETE'])
    @require_jwt_token
    def delete_api_key(key_id: int):
        """Löscht API Key"""
        from app.models import APIKeyModel
        
        api_key = db.session.query(APIKeyModel).filter_by(
            id=key_id,
            user_id=g.user.id
        ).first()
        
        if not api_key:
            return jsonify({'error': 'Key not found'}), 404
        
        db.session.delete(api_key)
        db.session.commit()
        
        return jsonify({'message': 'Key deleted'}), 200
    
    logger.info("✅ API Key routes setup complete")


# ============================================================================
# Authentication Setup
# ============================================================================

def setup_authentication(app):
    """Initialisiert komplettes Auth-System"""
    logger.info("🔐 Setting up authentication...")
    
    # OAuth2
    oauth2_provider = OAuth2Provider(app)
    setup_oauth2_routes(app, oauth2_provider)
    
    # API Keys
    setup_api_key_routes(app)
    
    logger.info("✅ Authentication setup complete")
