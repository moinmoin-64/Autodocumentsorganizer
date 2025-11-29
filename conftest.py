"""
pytest Configuration & Fixtures
Zentrale Test-Konfiguration für alle Tests
"""
import pytest
import tempfile
import shutil
from pathlib import Path
import yaml
import sqlite3
from datetime import datetime


@pytest.fixture
def temp_dir():
    """Temporäres Verzeichnis für Tests"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def test_config(temp_dir):
    """Test-Konfiguration mit allen erforderlichen Settings"""
    config = {
        'system': {
            'storage': {
                'upload_folder': str(temp_dir / 'uploads'),
                'export_folder': str(temp_dir / 'exports'),
                'data_folder': str(temp_dir / 'data')
            }
        },
        # Database config at root level (old structure for compatibility)
        'database': {
            'path': str(temp_dir / 'test.db')
        },
        # Categories with keywords nested (old structure)
        'categories': {
            'keywords': {
                'Bank': ['kontoauszug', 'überweisung', 'bank'],
                'Rechnung': ['rechnung', 'invoice'],
                'Versicherung': ['versicherung', 'police'],
                'Verträge': ['vertrag', 'contract'],
                'Steuer': ['finanzamt', 'steuerbescheid'],
                'Gesundheit': ['arzt', 'rezept'],
                'Behörden': ['amt', 'bescheid'],
                'Sonstiges': []
            }
        },
        # AI config (disabled for tests)
        'ai': {
            'categorization': {
                'enabled': False,
                'model': 'paraphrase-multilingual-MiniLM-L12-v2'
            }
        },
        'email': {
            'enabled': False,
            'host': 'imap.test.com',
            'port': 993,
            'user': 'test@test.com',
            'password': 'test123',
            'poll_interval': 300
        },
        'ocr': {
            'language': 'deu+eng',
            'dpi': 300
        }
    }
    
    # Erstelle Verzeichnisse
    (temp_dir / 'uploads').mkdir(parents=True, exist_ok=True)
    (temp_dir / 'exports').mkdir(parents=True, exist_ok=True)
    (temp_dir / 'data').mkdir(parents=True, exist_ok=True)
    
    # Speichere Config als YAML-Datei
    config_path = temp_dir / 'config.yaml'
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f)
    
    return str(config_path)


@pytest.fixture
def mock_database(test_config):
    """Mock-Datenbank für Tests"""
    from app.database import Database
    db = Database(test_config)
    yield db
    # Database doesn't have close() method - connections are auto-closed


@pytest.fixture
def sample_pdf(temp_dir):
    """Sample PDF für Tests"""
    pdf_path = temp_dir / 'sample.pdf'
    # Erstelle minimales gültiges PDF
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test Document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000315 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
407
%%EOF"""
    pdf_path.write_bytes(pdf_content)
    return pdf_path


@pytest.fixture
def sample_image(temp_dir):
    """Sample Image (PNG) für Tests"""
    from PIL import Image, ImageDraw, ImageFont
    
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Einfacher Text
    draw.text((100, 100), "Test Invoice\nAmount: 123.45 EUR\nDate: 2024-01-15", fill='black')
    
    img_path = temp_dir / 'sample.png'
    img.save(img_path)
    return img_path


@pytest.fixture
def mock_document_data():
    """Mock Document Data für Tests"""
    return {
        'filename': 'test_document.pdf',
        'filepath': '/path/to/test_document.pdf',
        'category': 'Rechnung',
        'subcategory': 'Internet',
        'date_document': datetime(2024, 1, 15),
        'full_text': 'Test Invoice\nAmount: 123.45 EUR\nDate: 15.01.2024\nInternet Provider',
        'keywords': ['rechnung', 'internet', '123.45'],
        'ocr_confidence': 0.95,
        'amounts': [123.45],
        'dates': [datetime(2024, 1, 15)]
    }


@pytest.fixture
def flask_app(test_config):
    """Flask Test App"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from app.server import app
    
    # Test configuration
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Initialize app with test config
    try:
        from app.server import init_app
        init_app(test_config)
    except Exception as e:
        # If init fails, continue with basic app
        pass
    
    return app


@pytest.fixture
def client(flask_app):
    """Flask Test Client"""
    return flask_app.test_client()


# Marker für verschiedene Test-Typen
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
