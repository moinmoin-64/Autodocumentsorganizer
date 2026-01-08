"""
Test Configuration
"""
import pytest
import sys
from pathlib import Path
import prometheus_client
import tempfile # Hinzugefügt
import os # Hinzugefügt

# --- Prometheus Patch for duplicate metrics in tests ---
# This is a workaround for a common issue when using prometheus-client in a test
# environment where modules that define metrics might be imported multiple times.

original_register = prometheus_client.registry.CollectorRegistry.register

def patched_register(self, collector):
    """Patched register method to ignore duplicate metric registration errors."""
    if hasattr(collector, '_name') and collector._name in self._names_to_collectors:
        # If the metric name is already registered, simply ignore the new registration.
        return
    # Otherwise, proceed with the original registration logic.
    original_register(self, collector)

# Apply the patch globally at the start of the test session.
prometheus_client.registry.CollectorRegistry.register = patched_register
# --- End of Patch ---

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.server import create_app, init_app # init_app importieren

@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    # Use actual test config file
    test_config_path = Path(__file__).parent / 'test_config.yaml'
    
    _app = create_app() # create_app ohne Argumente aufrufen
    init_app(_app, str(test_config_path)) # init_app mit App-Instanz und config_path aufrufen
    _app.config['TESTING'] = True
    _app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for tests
    
    yield _app


@pytest.fixture
def test_config(app):
    """Get test configuration from app"""
    from app.server import global_config
    return global_config


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def db(app):
    """
    Database instance for tests, with automatic data cleanup.
    This fixture ensures a clean database for every test function.
    """
    # Use the database from the app context
    from app.database import Database
    import sqlite3
    
    # Create fresh database instance for test
    db_instance = Database(app.config)
    
    # Get database path from config
    db_path = app.config.get('DATABASE_PATH', 'data/database.db')
    
    # Return the database for the test
    yield db_instance
    
    # Cleanup after test - delete all records to ensure isolation
    try:
        # Delete all documents to clear test data
        try:
            db_instance.db.execute("DELETE FROM documents")
            db_instance.db.commit()
        except:
            pass
        
        # Close connection
        db_instance.close()
    except Exception as e:
        pass  # Silently fail cleanup


@pytest.fixture
def sample_document(db):
    """Sample document data - unique per test"""
    import uuid
    import time
    
    # Generate unique filepath to avoid UNIQUE constraint conflicts
    unique_id = str(uuid.uuid4())[:8]
    timestamp = int(time.time() * 1000)
    
    return {
        'filename': f'test_{unique_id}.pdf',
        'filepath': f'/tmp/test_{timestamp}_{unique_id}.pdf',
        'category': 'Invoice',
        'subcategory': 'Utilities',
        'summary': f'Test invoice {unique_id}',
        'keywords': ['test', 'invoice', unique_id],
        'full_text': f'This is a test document {unique_id}',
        'amount': 99.99,
        'currency': 'EUR'
    }

