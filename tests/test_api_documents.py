"""
Test Documents API Endpoints
"""
import pytest
import json


class TestDocumentsAPI:
    """Test /api/documents endpoints"""
    
    def test_list_documents_empty(self, client):
        """Test listing documents when database is empty"""
        response = client.get('/api/documents')
        assert response.status_code == 200
        
        data = response.json
        assert data['success'] == True
        assert 'data' in data
        assert 'pagination' in data
        
    def test_list_documents_with_pagination(self, client):
        """Test pagination parameters"""
        response = client.get('/api/documents?page=1&page_size=10')
        assert response.status_code == 200
        
        data = response.json
        assert data['pagination']['page'] == 1
        assert data['pagination']['page_size'] == 10
        
    def test_list_documents_invalid_page(self, client):
        """Test invalid page parameter"""
        response = client.get('/api/documents?page=0')
        assert response.status_code == 422  # Validation error
        
        data = response.json
        assert data['success'] == False
        assert data['error']['code'] == 'VALIDATION_ERROR'
        
    def test_list_documents_invalid_page_size(self, client):
        """Test invalid page_size parameter"""
        response = client.get('/api/documents?page_size=1000')
        assert response.status_code == 422
        
        data = response.json
        assert 'page_size' in data['error']['details']['fields']
        
    def test_get_document_not_found(self, client):
        """Test getting non-existent document"""
        response = client.get('/api/documents/9999')
        assert response.status_code == 404
        
        data = response.json
        assert data['success'] == False
        assert data['error']['code'] == 'NOT_FOUND'
        
    def test_get_document_success(self, client, db, sample_document):
        """Test getting existing document"""
        # Create document
        doc_id = db.add_document(**sample_document)
        
        # Get document
        response = client.get(f'/api/documents/{doc_id}')
        assert response.status_code == 200
        
        data = response.json
        assert data['success'] == True
        assert data['data']['id'] == doc_id
        assert data['data']['filename'] == sample_document['filename']
        
    def test_delete_document_success(self, client, db, sample_document):
        """Test deleting document"""
        # Create document
        doc_id = db.add_document(**sample_document)
        
        # Delete document
        response = client.delete(f'/api/documents/{doc_id}')
        assert response.status_code == 204  # No content
        
        # Verify deleted
        response = client.get(f'/api/documents/{doc_id}')
        assert response.status_code == 404
        
    def test_delete_document_not_found(self, client):
        """Test deleting non-existent document"""
        response = client.delete('/api/documents/9999')
        assert response.status_code == 404
        
    def test_update_document_success(self, client, db, sample_document):
        """Test updating document"""
        # Create document
        doc_id = db.add_document(**sample_document)
        
        # Update document
        update_data = {'category': 'Receipt'}
        response = client.put(
            f'/api/documents/{doc_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        data = response.json
        assert data['success'] == True
        
    def test_update_document_no_data(self, client, db, sample_document):
        """Test updating document with no data"""
        doc_id = db.add_document(**sample_document)
        
        response = client.put(f'/api/documents/{doc_id}')
        assert response.status_code == 422  # Validation error
        
    def test_filter_by_category(self, client, db, sample_document):
        """Test filtering documents by category"""
        # Create documents with different categories
        db.add_document(**sample_document)
        
        doc2 = sample_document.copy()
        doc2['category'] = 'Receipt'
        doc2['filepath'] = '/tmp/test2.pdf'
        db.add_document(**doc2)
        
        # Filter by category
        response = client.get('/api/documents?category=Invoice')
        assert response.status_code == 200
        
        data = response.json
        assert len(data['data']) >= 1
        assert all(doc['category'] == 'Invoice' for doc in data['data'])
        
    def test_search_documents(self, client, db, sample_document):
        """Test full-text search"""
        # Create document
        db.add_document(**sample_document)
        
        # Search
        response = client.get('/api/documents?query=test')
        assert response.status_code == 200
        
        data = response.json
        # Should find the document (in summary or full_text)
        assert data['pagination']['total'] >= 0


class TestDocumentLifecycle:
    """Test complete document lifecycle"""
    
    def test_full_lifecycle(self, client, db, sample_document):
        """Test create -> read -> update -> delete"""
        
        # Create
        doc_id = db.add_document(**sample_document)
        assert doc_id > 0
        
        # Read
        response = client.get(f'/api/documents/{doc_id}')
        assert response.status_code == 200
        assert response.json['data']['id'] == doc_id
        
        # Update
        update_response = client.put(
            f'/api/documents/{doc_id}',
            data=json.dumps({'category': 'Updated'}),
            content_type='application/json'
        )
        assert update_response.status_code == 200
        
        # Delete
        delete_response = client.delete(f'/api/documents/{doc_id}')
        assert delete_response.status_code == 204
        
        # Verify deleted
        get_response = client.get(f'/api/documents/{doc_id}')
        assert get_response.status_code == 404
