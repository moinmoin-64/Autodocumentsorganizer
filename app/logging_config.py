"""
Logging Configuration
Rotating file handler mit strukturiertem Logging
"""
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path


def setup_logging(app):
    """
    Konfiguriert Logging für die Applikation
    
    Args:
        app: Flask Application
    """
    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Remove default handlers
    app.logger.handlers.clear()
    
    # Set log level from environment or default to INFO
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    app.logger.setLevel(getattr(logging, log_level))
    
    # Console Handler (for development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    console_formatter = logging.Formatter(
        '%(levelname)s - %(name)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File Handler with rotation (10MB max, keep 10 backups)
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    )
    file_handler.setFormatter(file_formatter)
    
    # Error File Handler (separate file for errors)
    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=10485760,
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # Add handlers
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    
    # Log application startup
    app.logger.info('='*50)
    app.logger.info('Application startup')
    app.logger.info(f'Environment: {"Development" if app.debug else "Production"}')
    app.logger.info(f'Log Level: {log_level}')
    app.logger.info('='*50)
    
    return app.logger


def log_request(request, response, duration):
    """
    Log HTTP request details
    
    Args:
        request: Flask request object
        response: Flask response object
        duration: Request duration in seconds
    """
    logger = logging.getLogger(__name__)
    
    log_message = (
        f'{request.method} {request.path} '
        f'Status: {response.status_code} '
        f'Duration: {duration:.3f}s '
        f'IP: {request.remote_addr}'
    )
    
    if response.status_code >= 500:
        logger.error(log_message)
    elif response.status_code >= 400:
        logger.warning(log_message)
    else:
        logger.info(log_message)
