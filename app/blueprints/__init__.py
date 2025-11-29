"""
Blueprints Package
Enthält alle API-Blueprints für modulare Route-Organisation
"""
from flask import Flask


def register_blueprints(app: Flask) -> None:
    """
    Registriert alle Blueprints bei der Flask-App
    
    Args:
        app: Flask-App-Instanz
    """
    from .documents import documents_bp
    from .search import search_bp
    from .stats import stats_bp
    from .tags import tags_bp
    from .export import export_bp
    from .chat import chat_bp
    
    # Registriere alle Blueprints
    app.register_blueprint(documents_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(chat_bp)
