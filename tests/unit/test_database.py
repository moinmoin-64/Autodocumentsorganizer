"""
Unit Tests für Database - SQLAlchemy
"""
import pytest
from app.database import Database
from app.models import Document
from datetime import datetime
from unittest.mock import MagicMock, patch

@pytest.mark.unit
class TestDatabaseInit:
    """Tests für Datenbank-Initialisierung"""
    
    def test_init_with_config(self, test_config):
        """Test dass Database initialisiert werden kann"""
        db = Database(test_config)
        assert db is not None
        # assert hasattr(db, 'db_path') # Removed as it's not in new implementation 

@pytest.mark.unit
class TestDocumentOperations:
    """Tests für Dokument-CRUD"""
    
    @patch('app.database.get_db')
    def test_add_document(self, mock_get_db, test_config):
        """Test Dokument hinzufügen"""
        # Setup mock session
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session
        
        db = Database(test_config)
        
        # Call
        doc_id = db.add_document(
            filepath='/path/to/test.pdf',
            category='Bank',
            subcategory='Kontoauszug',
            document_data={'text': 'Test document', 'filename': 'test.pdf'},
            date_document=datetime.now()
        )
        
        # Verify
        assert mock_session.add.called
        # In mock, ID won't be set automatically unless we side_effect, but method returns doc.id
        # We can simulate ID setting if needed, but for unit test verifying .add() is enough
        
    @patch('app.database.get_db')
    def test_get_document(self, mock_get_db, test_config):
        """Test Dokument abrufen"""
        # Setup mock
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session
        
        # Mock return value
        mock_doc = Document(id=1, filename='test.pdf', filepath='/path/test.pdf', category='Bank')
        # We need to mock attributes accessed in _doc_to_dict
        mock_doc.keywords = '[]'
        mock_doc.date_document = datetime.now()
        mock_doc.date_added = datetime.now()
        mock_doc.tags = []
        
        mock_session.get.return_value = mock_doc
        
        db = Database(test_config)
        doc = db.get_document(1)
        
        assert doc is not None
        assert doc['id'] == 1
        assert doc['filename'] == 'test.pdf'
    
    @patch('app.database.get_db')
    def test_get_nonexistent_document(self, mock_get_db, test_config):
        """Test Abruf von nicht-existentem Dokument"""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = None
        
        db = Database(test_config)
        doc = db.get_document(999)
        assert doc is None
    
    @patch('app.database.get_db')
    def test_search_documents(self, mock_get_db, test_config):
        """Test Suche"""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session
        
        # Mock query chain
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = []
        
        db = Database(test_config)
        results = db.search_documents(query="test")
        
        assert isinstance(results, list)
        assert mock_session.query.called

@pytest.mark.unit
class TestDatabaseMethods:
    """Tests für Database-Methoden"""
    
    def test_has_methods(self, test_config):
        """Test dass Methoden existieren"""
        db = Database(test_config)
        assert hasattr(db, 'add_document')
        assert hasattr(db, 'get_document')
        assert hasattr(db, 'search_documents')
        assert hasattr(db, 'delete_document')
        assert hasattr(db, 'update_document')
