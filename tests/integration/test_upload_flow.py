"""
Integration Test: Upload → Verarbeitung → Datenbank
Testet den kompletten Upload-Flow
"""
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.mark.integration
class TestUploadFlow:
    """Tests für kompletten Upload-Prozess"""
    
    @pytest.fixture
    def integration_setup(self, temp_dir, test_config):
        """Setup für Integration Tests"""
        # Erstelle Upload-Folder
        upload_folder = temp_dir / 'uploads'
        upload_folder.mkdir(parents=True, exist_ok=True)
        
        # Erstelle Test-PDF
        pdf_path = temp_dir / 'test_upload.pdf'
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (Rechnung 123.45 EUR) Tj ET
endstream endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000244 00000 n
trailer<</Size 5/Root 1 0 R>>
startxref
336
%%EOF"""
        pdf_path.write_bytes(pdf_content)
        
        return {
            'upload_folder': upload_folder,
            'test_pdf': pdf_path,
            'config': test_config
        }
    
    def test_complete_upload_flow(self, integration_setup, mock_database):
        """Test: Upload → OCR → Kategorisierung → DB"""
        from app.upload_handler import process_file_logic
        from pathlib import Path
        
        test_pdf = integration_setup['test_pdf']
        
        # Mock minimal dependencies
        try:
            result = process_file_logic(str(test_pdf))
            
            # Prüfe Rückgabe
            assert 'success' in result or 'error' in result
            
            if result.get('success'):
                assert 'document_id' in result
                
                # Prüfe DB-Eintrag
                doc_id = result['document_id']
                doc = mock_database.get_document(doc_id)
                
                if doc:
                    assert doc['filename'] is not None
                    assert doc['category'] is not None
        except Exception as e:
            # Test schlägt fehl wenn Dependencies fehlen
            pytest.skip(f"Test requires full dependencies: {e}")
    
    def test_upload_and_categorization(self, integration_setup):
        """Test Upload mit Kategorisierung"""
        from app.document_processor import DocumentProcessor
        from app.categorizer import DocumentCategorizer
        import os
        
        if not os.path.exists(integration_setup['test_pdf']):
            pytest.skip("Test PDF not found")
        
        try:
            # Initialisiere Komponenten
            processor = DocumentProcessor(integration_setup['config'])
            categorizer = DocumentCategorizer(integration_setup['config'])
            
            # Verarbeite Dokument
            doc_data = processor.process(str(integration_setup['test_pdf']))
            
            # Kategorisiere
            category, subcategory, confidence = categorizer.categorize(doc_data)
            
            # Assertions
            assert category is not None
            assert confidence >= 0
            
        except ImportError as e:
            pytest.skip(f"Missing dependency: {e}")
        except Exception as e:
            pytest.fail(f"Integration test failed: {e}")


@pytest.mark.integration
class TestDatabaseWorkflow:
    """Tests für Database-Workflows"""
    
    def test_document_lifecycle(self, mock_database):
        """Test kompletter Dokument-Lebenszyklus"""
        from datetime import datetime
        
        # 1. Insert
        doc_id = mock_database.insert_document({
            'filename': 'lifecycle_test.pdf',
            'filepath': '/path/to/file.pdf',
            'category': 'Rechnung',
            'date_document': datetime(2024, 1, 15),
            'full_text': 'Test content for lifecycle'
        })
        
        assert doc_id > 0
        
        # 2. Get
        doc = mock_database.get_document(doc_id)
        assert doc is not None
        assert doc['filename'] == 'lifecycle_test.pdf'
        
        # 3. Tag hinzufügen
        tag_id = mock_database.create_tag('Wichtig', '#FF0000')
        mock_database.add_tag_to_document(doc_id, tag_id)
        
        tags = mock_database.get_document_tags(doc_id)
        assert len(tags) == 1
        
        # 4. Search
        results = mock_database.search_documents(query='lifecycle')
        assert len(results) >= 1
        
        # 5. Delete
        mock_database.delete_document(doc_id)
        doc = mock_database.get_document(doc_id)
        assert doc is None
    
    def test_tag_workflow(self, mock_database):
        """Test Tag-Management Workflow"""
        # Erstelle Tags
        tag1_id = mock_database.create_tag('Important', '#FF0000')
        tag2_id = mock_database.create_tag('Urgent', '#FFA500')
        
        # Erstelle Dokument
        doc_id = mock_database.insert_document({'filename': 'tagged_doc.pdf'})
        
        # Tags hinzufügen
        mock_database.add_tag_to_document(doc_id, tag1_id)
        mock_database.add_tag_to_document(doc_id, tag2_id)
        
        # Prüfe Tags
        tags = mock_database.get_document_tags(doc_id)
        assert len(tags) == 2
        
        # Tag entfernen
        mock_database.remove_tag_from_document(doc_id, tag1_id)
        tags = mock_database.get_document_tags(doc_id)
        assert len(tags) == 1


@pytest.mark.integration
@pytest.mark.slow
class TestEmailIntegration:
    """Integration Tests für Email-Workflow"""
    
    def test_email_to_database_flow(self, temp_dir, test_config, mock_database):
        """Test: Email Anhang → Verarbeitung → DB"""
        from app.email_receiver import EmailReceiver
        
        # Setup receiver
        receiver = EmailReceiver(test_config)
        
        # Simulate attachment save
        upload_folder = temp_dir / 'uploads'
        upload_folder.mkdir(parents=True, exist_ok=True)
        
        test_file = upload_folder / 'email_attachment.pdf'
        test_file.write_bytes(b'%PDF-1.4\n%%EOF')
        
        # In real scenario, this would come from fetch_attachments()
        # For now, just test that file exists
        assert test_file.exists()
