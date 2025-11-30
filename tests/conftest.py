"""
Test Configuration
"""
import pytest
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.server import app as flask_app
from app.database import Database
from app.db_config import engine, Base


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    flask_app.config['TESTING'] = True
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
def db():
    """Database instance for tests"""
    database = Database()
    yield database
    database.close()


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
