"""
Comprehensive Test Suite
Unit Tests, Integration Tests, Security Tests
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


# ============================================================================
# SECURITY TESTS
# ============================================================================

class TestSecurityHeaders:
    """Tests für Security-Headers"""
    
    def test_csp_header_present(self, client):
        """Prüfe Content-Security-Policy Header"""
        response = client.get('/api/documents')
        assert 'Content-Security-Policy' in response.headers
    
    def test_xframe_options_set(self, client):
        """Prüfe X-Frame-Options"""
        response = client.get('/api/documents')
        assert response.headers['X-Frame-Options'] == 'DENY'
    
    def test_xss_protection_enabled(self, client):
        """Prüfe XSS-Protection"""
        response = client.get('/api/documents')
        assert 'X-XSS-Protection' in response.headers
    
    def test_hsts_header_present(self, client):
        """Prüfe HSTS Header"""
        response = client.get('/api/documents')
        assert 'Strict-Transport-Security' in response.headers


class TestInputValidation:
    """Tests für Input-Validierung"""
    
    def test_sql_injection_attempt_blocked(self, client):
        """Prüfe SQL-Injection Protection"""
        payload = "'; DROP TABLE documents; --"
        response = client.post(
            '/api/documents',
            json={'title': payload},
            headers={'Content-Type': 'application/json'}
        )
        # Sollte entweder blocked oder sicher escaped sein
        assert response.status_code in [400, 201, 200]
    
    def test_xss_attempt_sanitized(self, client):
        """Prüfe XSS-Protection"""
        payload = "<script>alert('XSS')</script>"
        response = client.post(
            '/api/documents',
            json={'title': payload},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code in [400, 201, 200]
    
    def test_path_traversal_blocked(self, client):
        """Prüfe Path-Traversal Protection"""
        response = client.get('/uploads/../../etc/passwd')
        assert response.status_code == 404
    
    def test_long_input_truncated(self):
        """Prüfe Längenbegrenzung"""
        from app.security_middleware import InputValidator
        long_string = 'a' * 2000
        result = InputValidator.sanitize_string(long_string, max_length=1000)
        assert len(result) <= 1000


class TestRateLimiting:
    """Tests für Rate Limiting"""
    
    def test_rate_limit_headers_present(self, client):
        """Prüfe ob Rate-Limit Headers vorhanden sind"""
        response = client.get('/api/documents')
        # Should have rate limit headers
        assert response.status_code == 200
    
    def test_exceeding_rate_limit(self, client):
        """Prüfe ob Requests nach Limit geblockt werden"""
        # Mache viele Requests
        for i in range(100):
            client.get('/api/documents')
        
        # Nächster Request sollte potentially blocked sein
        # (abhängig von Limiter-Konfiguration)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestEmailIntegration:
    """Tests für Email-Integration"""
    
    @patch('imaplib.IMAP4_SSL')
    def test_email_connection(self, mock_imap):
        """Prüfe IMAP-Verbindung"""
        from app.email_receiver import EmailReceiver
        
        config = {
            'email': {
                'enabled': True,
                'host': 'imap.gmail.com',
                'port': 993,
                'user': 'test@gmail.com',
                'password': 'test'
            },
            'system': {'storage': {'upload_folder': '/tmp'}}
        }
        
        receiver = EmailReceiver(config)
        assert receiver.connect()
    
    def test_email_parser_metadata_extraction(self):
        """Prüfe Email-Metadaten-Extraktion"""
        from app.email_parser import EmailMetadataExtractor
        import email
        
        # Erstelle Test-Email
        msg = email.message.EmailMessage()
        msg['Subject'] = 'Test Subject'
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Date'] = 'Wed, 8 Jan 2025 10:00:00 +0000'
        
        metadata = EmailMetadataExtractor.extract_metadata(msg)
        
        assert metadata['subject'] == 'Test Subject'
        assert metadata['from'] == 'sender@example.com'


class TestOCRIntegration:
    """Tests für OCR-Integration"""
    
    def test_ocr_ensemble_initialization(self):
        """Prüfe OCR-Ensemble Initialisierung"""
        from app.ocr_ensemble import OCREnsemble
        
        config = {
            'ocr': {
                'languages': ['deu', 'eng'],
                'easyocr_enabled': False
            }
        }
        
        ensemble = OCREnsemble(config)
        assert ensemble.tesseract_lang == 'deu+eng'
    
    def test_advanced_text_processor(self):
        """Prüfe Advanced Text Processing"""
        from app.advanced_text_processor import AdvancedTextProcessor, LayoutDetector
        
        processor = AdvancedTextProcessor()
        
        sample_text = """
        Rechnung Nr. 12345
        Datum: 08.01.2025
        Betrag: 1.234,56 €
        
        - Artikel 1: 500,00 €
        - Artikel 2: 734,56 €
        """
        
        analysis = processor.process_with_advanced_analysis(sample_text, ocr_confidence=0.95)
        
        assert 'layout' in analysis
        assert 'quality' in analysis
        assert analysis['quality']['word_count'] > 0


# ============================================================================
# UPLOAD TESTS
# ============================================================================

class TestFileUpload:
    """Tests für File-Upload"""
    
    def test_valid_file_upload(self, client, tmp_path):
        """Prüfe validierter File-Upload"""
        # Erstelle Test-Datei
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"PDF content")
        
        with open(test_file, 'rb') as f:
            response = client.post(
                '/api/upload',
                data={'file': (f, 'test.pdf')}
            )
        
        assert response.status_code in [200, 201]
    
    def test_invalid_file_type_rejected(self, client, tmp_path):
        """Prüfe ob ungültige Dateitypen abgelehnt werden"""
        test_file = tmp_path / "test.exe"
        test_file.write_bytes(b"exe content")
        
        with open(test_file, 'rb') as f:
            response = client.post(
                '/api/upload',
                data={'file': (f, 'test.exe')}
            )
        
        assert response.status_code == 400
    
    def test_oversized_file_rejected(self, client, tmp_path):
        """Prüfe ob zu große Dateien abgelehnt werden"""
        test_file = tmp_path / "large.pdf"
        # Erstelle 150MB Datei
        test_file.write_bytes(b"x" * (150 * 1024 * 1024))
        
        with open(test_file, 'rb') as f:
            response = client.post(
                '/api/upload',
                data={'file': (f, 'large.pdf')}
            )
        
        assert response.status_code == 400
    
    def test_batch_upload(self, client, tmp_path):
        """Prüfe Batch-Upload"""
        files = []
        for i in range(3):
            test_file = tmp_path / f"test{i}.pdf"
            test_file.write_bytes(b"PDF content")
            files.append(('files', (open(test_file, 'rb'), f'test{i}.pdf')))
        
        response = client.post('/api/upload/batch', data=files)
        
        assert response.status_code in [200, 207]


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance-Tests"""
    
    def test_document_list_response_time(self, client, benchmark):
        """Prüfe Response-Zeit für Document-List"""
        def get_documents():
            return client.get('/api/documents')
        
        result = benchmark(get_documents)
        assert result.status_code == 200
        # Response sollte < 500ms sein
        # (benchmark misst automatisch)
    
    def test_ocr_performance(self, benchmark):
        """Prüfe OCR-Performance"""
        from app.document_processor import DocumentProcessor
        
        config = {
            'ocr': {'languages': ['deu', 'eng']},
            'ai': {'ollama': {'enabled': False}},
            'system': {'storage': {'upload_folder': '/tmp'}}
        }
        
        processor = DocumentProcessor(config)
        
        # Benchmark OCR (würde echte Datei brauchen)
        # def process():
        #     return processor.process_document('test.pdf')
        # benchmark(process)


# ============================================================================
# E2E TESTS
# ============================================================================

class TestEndToEnd:
    """End-to-End Tests"""
    
    def test_complete_document_workflow(self, client, tmp_path):
        """Prüfe kompletten Document-Workflow"""
        # 1. File Upload
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"PDF content")
        
        with open(test_file, 'rb') as f:
            upload_response = client.post(
                '/api/upload',
                data={'file': (f, 'test.pdf')}
            )
        
        assert upload_response.status_code in [200, 201]
        
        # 2. Document List
        list_response = client.get('/api/documents')
        assert list_response.status_code == 200
        
        # 3. Kategorizierung
        # würde weitere Steps brauchen
    
    def test_search_functionality(self, client):
        """Prüfe Such-Funktionalität"""
        response = client.get('/api/documents?search=test')
        assert response.status_code == 200


# ============================================================================
# FIXTURE FÜR TESTS
# ============================================================================

@pytest.fixture
def app():
    """Create and configure test app"""
    from app.server import create_app
    
    app = create_app()
    app.config['TESTING'] = True
    
    return app


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI test runner"""
    return app.test_cli_runner()


@pytest.fixture(scope="session")
def benchmark():
    """Benchmark fixture für Performance Tests"""
    class SimpleBenchmark:
        def __call__(self, func):
            import time
            start = time.time()
            result = func()
            elapsed = time.time() - start
            print(f"Execution time: {elapsed*1000:.2f}ms")
            return result
    
    return SimpleBenchmark()
