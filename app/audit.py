"""
Audit Log Helper
"""
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)

def log_action(db, action: str, resource_id: str = None, details: dict = None):
    """
    Loggt eine Benutzeraktion
    """
    try:
        user_id = 'system'
        try:
            if current_user and current_user.is_authenticated:
                user_id = current_user.id
        except (AttributeError, RuntimeError) as e:
            logger.debug(f"Current user nicht verfügbar: {e}")
            pass
            
        if db:
            db.log_audit_event(user_id, action, resource_id, details)
            
    except Exception as e:
        logger.error(f"Fehler beim Audit-Logging: {e}")
