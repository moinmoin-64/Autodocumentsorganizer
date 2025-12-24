"""
Test Configuration
"""
import pytest
import sys
from pathlib import Path
import prometheus_client

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

from app.server import app as flask_app
from app.database import Database
from app.db_config import engine
from app.models import Base


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for tests
    flask_app.config['DATABASE_PATH'] = ':memory:'  # In-memory DB for tests
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield flask_app
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


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
        
    yield Database()


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
