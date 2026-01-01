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
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def db(app):
    """
    Database instance for tests, with automatic data cleanup.
    This fixture ensures a clean database for every test function.
    """
    # --- Cleanup before test ---
    # The 'app' fixture, which has session scope, has already created the tables.
    # We just need to delete the data from them.
    with engine.connect() as connection:
        transaction = connection.begin()
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
        transaction.commit()
        
    yield Database(app.config) # app.config an Database übergeben


@pytest.fixture
def sample_document():
    """Sample document data"""
    return {
        'filename': 'test.pdf',
        'filepath': '/tmp/test.pdf',
        'category': 'Invoice',
        'subcategory': 'Utilities',
        'summary': 'Test invoice',
        'keywords': ['test', 'invoice'],
        'full_text': 'This is a test document',
        'amount': 99.99,
        'currency': 'EUR'
    }
