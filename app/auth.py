"""
Authentication Module
Handhabt User-Login und Session-Management mit sicherem Passwort-Hashing
"""

import logging
import os
from flask import Blueprint, request, jsonify, session, current_app, redirect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import yaml

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()

# Einfache User-Klasse
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# User-Loader für Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def init_auth(app, config_path='config.yaml'):
    """Initialisiert Auth für die App"""
    logger.info("Initialisiere Authentifizierung...")
    
    # Lade Config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Secret Key aus ENV oder Config
    secret_key = os.getenv('SECRET_KEY') or config['web'].get('secret_key')
    if secret_key == 'change_this_to_something_secure':
        logger.warning("⚠️  WARNUNG: Standard Secret Key wird verwendet! Setze SECRET_KEY als Umgebungsvariable!")
    app.secret_key = secret_key
    
    # Lade User-Daten (unterstützt sowohl Klartext als auch gehashte Passwörter)
    app.config['AUTH_USERS'] = config.get('auth', {}).get('users', {})
    
    login_manager.init_app(app)

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Unauthorized'}), 401
        return redirect('/login.html')

def _check_password(stored_password: str, provided_password: str) -> bool:
    """
    Prüft Passwort - unterstützt sowohl Klartext (Legacy) als auch Hashes
    
    Args:
        stored_password: Gespeichertes Passwort (Klartext oder Hash)
        provided_password: Vom User eingegebenes Passwort
        
    Returns:
        True wenn Passwort korrekt
    """
    # Wenn gespeichertes Passwort mit werkzeug-Hash-Prefix beginnt
    if stored_password.startswith(('pbkdf2:', 'scrypt:', 'bcrypt:')):
        # Verwende sichere Hash-Prüfung
        return check_password_hash(stored_password, provided_password)
    else:
        # Legacy: Klartext-Vergleich
        logger.warning("⚠️  Legacy Klartext-Passwort verwendet! Bitte zu gehashten Passwörtern migrieren!")
        return stored_password == provided_password

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login Endpoint mit sicherem Passwort-Hashing"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username und Passwort erforderlich'}), 400
    
    users = current_app.config.get('AUTH_USERS', {})
    
    if username in users:
        stored_password = users[username]
        
        if _check_password(stored_password, password):
            user = User(username)
            login_user(user)
            logger.info(f"✅ Login erfolgreich: {username}")
            return jsonify({'success': True, 'message': 'Login erfolgreich'})
    
    logger.warning(f"Login fehlgeschlagen: {username}")
    return jsonify({'success': False, 'message': 'Ungültige Zugangsdaten'}), 401

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout Endpoint"""
    logout_user()
    return jsonify({'success': True, 'message': 'Logout erfolgreich'})

@auth_bp.route('/status', methods=['GET'])
def status():
    """Prüft Login-Status"""
    if current_user.is_authenticated:
        return jsonify({'authenticated': True, 'user': current_user.id})
    return jsonify({'authenticated': False}), 401
