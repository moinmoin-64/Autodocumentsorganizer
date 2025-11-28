"""
Authentication Module
Handhabt User-Login und Session-Management
"""

import logging
from flask import Blueprint, request, jsonify, session, current_app, redirect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
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
    print(f"DEBUG: init_auth running for app {app}")
    
    # Lade Config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    app.secret_key = config['web'].get('secret_key', 'dev_key')
    app.config['AUTH_USERS'] = config.get('auth', {}).get('users', {})
    
    login_manager.init_app(app)
    # login_manager.login_view = 'auth.login' # Wir nutzen Custom Handler

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Unauthorized'}), 401
        return redirect('/login.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login Endpoint"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    users = current_app.config.get('AUTH_USERS', {})
    
    if username in users and users[username] == password:
        user = User(username)
        login_user(user)
        logger.info(f"Login erfolgreich: {username}")
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
