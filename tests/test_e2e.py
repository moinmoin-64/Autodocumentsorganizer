"""
End-to-End Tests - Testet kompletten Dokumenten-Workflow
"""

import unittest
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
from PIL import Image, ImageDraw, ImageFont

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.document_processor import DocumentProcessor
from app.categorizer import DocumentCategorizer
from app.storage_manager import StorageManager
from app.data_extractor import DataExtractor
from app.database import Database


class TestEndToEnd(unittest.TestCase):
    """End-to-End Tests für kompletten Workflow"""
    
    @classmethod
    def setUpClass(cls):
        """Setup einmal für alle Tests"""
        # Temporäres Verzeichnis für Tests
        cls.test_dir = Path(tempfile.mkdtemp())
        
        print(f"\n=== E2E Test Setup ===")
        print(f"Test-Verzeichnis: {cls.test_dir}")
        
        # Erstelle Test-Config
        cls.create_test_config()
        
        # Initialisiere Komponenten
        # Force CPU for tests to avoid CUDA errors
        import os
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        
        cls.processor = DocumentProcessor('tests/test_config.yaml')
        cls.categorizer = DocumentCategorizer('tests/test_config.yaml') 
        cls.storage = StorageManager('tests/test_config.yaml')
        cls.extractor = DataExtractor('tests/test_config.yaml')
        cls.db = Database('tests/test_config.yaml')
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup nach allen Tests"""
        print(f"\n=== E2E Test Cleanup ===")
        
        # Lösche temporäres Verzeichnis mit Retry-Logik für Windows
        if cls.test_dir.exists():
            import time
            max_retries = 3
            for i in range(max_retries):
                try:
                    shutil.rmtree(cls.test_dir)
                    print("Cleanup erfolgreich.")
                    break
                except PermissionError:
                    if i < max_retries - 1:
                        print(f"Cleanup fehlgeschlagen (Versuch {i+1}/{max_retries}), warte kurz...")
                        time.sleep(1)
                    else:
                        print("Warnung: Konnte Test-Verzeichnis nicht vollständig löschen (Windows File Lock).")
                        # Ignoriere Fehler beim letzten Versuch, um Test-Status nicht zu gefährden
                        shutil.rmtree(cls.test_dir, ignore_errors=True)
    
    @classmethod
    def create_test_config(cls):
        """Erstellt Test-Konfiguration"""
        # Sanitize path for YAML (replace backslashes with forward slashes)
        test_dir_str = str(cls.test_dir).replace('\\', '/')
        
        config = f"""
system:
  storage:
    base_path: "{test_dir_str}/storage"
    data_path: "{test_dir_str}/data"
    structure_file: "{test_dir_str}/structure.json"

web:
  host: "0.0.0.0"
  port: 5000
  debug: true
  secret_key: "test_secret"

auth:
  enabled: true
  users:
    admin: "admin123"

database:
  path: "{test_dir_str}/test.db"

ocr:
  engine: "tesseract"
  languages: ["deu", "eng"]

ai:
  categorization:
    enabled: true  # AI aktiviert
    model: "paraphrase-multilingual-MiniLM-L12-v2"
    confidence_threshold: 0.6
    
categories:
  main:
    - Rechnungen
    - Versicherungen
    - Verträge
    - Sonstiges
  keywords:
    Rechnungen:
      - rechnung
      - invoice
      - strom
    Versicherungen:
      - versicherung
      - police
    Verträge:
      - vertrag
      - contract

data_extraction:
  Rechnungen:
    fields:
      - name: "betrag"
        type: "currency"
        patterns:
          - 'Betrag:\\s*([\\d,.]+)\\s*EUR'
      - name: "rechnungsnummer"
        type: "text"
        patterns:
          - 'Rechnungs-Nr:\\s*([\\w-]+)'
  Versicherungen:
    fields:
      - name: "police_nr"
        type: "text"
        patterns:
          - 'Police-Nr:\\s*([\\w-]+)'
"""
        
        config_path = Path('tests/test_config.yaml')
        config_path.parent.mkdir(exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config)
    
    def create_test_image(self, filename: str, text: str) -> Path:
        """Erstellt Test-Bild mit Text"""
        img = Image.new('RGB', (800, 1000), color='white')
        d = ImageDraw.Draw(img)
        d.text((10, 10), text, fill='black')
        
        path = self.test_dir / filename
        img.save(path)
        return path
    
    @patch('app.document_processor.pytesseract.image_to_string')
    def test_complete_workflow_rechnung(self, mock_ocr):
        """Test: Kompletter Workflow für Rechnung"""
        print("\n--- Test: Workflow Rechnung ---")
        
        # Mock OCR result
        mock_ocr.return_value = """
        RECHNUNG
        Rechnungs-Nr: R-2024-001
        Datum: 15.01.2024
        
        Firma Beispiel GmbH
        Musterstraße 1
        12345 Berlin
        
        Leistungen:
        - Beratung: 100.00 EUR
        - Service: 50.00 EUR
        
        Gesamtbetrag: 150.00 EUR
        Bitte überweisen Sie den Betrag bis zum 30.01.2024.
        """
        
        # 1. Erstelle Test-Dokument
        text = "Rechnung Strom 2024"  # Dummy text for image
        img_path = self.create_test_image("rechnung.jpg", text)
        
        # 2. OCR & Verarbeitung
        print("Schritt 1: OCR...")
        doc_data = self.processor.process_document(str(img_path))
        
        self.assertIsNotNone(doc_data)
        self.assertIn('text', doc_data)
        print(f"  ✓ Text extrahiert: {len(doc_data['text'])} Zeichen")
        
        # 3. Kategorisierung
        print("Schritt 2: Kategorisierung...")
        category, subcategory, confidence = self.categorizer.categorize(doc_data)
        
        self.assertEqual(category, 'Rechnungen')
        print(f"  ✓ Kategorisiert: {category}/{subcategory} ({confidence:.2f})")
        
        # 4. Datum-Extraktion
        print("Schritt 3: Datum-Extraktion...")
        doc_date = doc_data['dates'][0] if doc_data.get('dates') else datetime.now()
        print(f"  ✓ Datum: {doc_date}")
        
        # 5. Speichern
        print("Schritt 4: Speichern...")
        saved_path = self.storage.store_document(
            source_file=str(img_path),
            category=category,
            subcategory=subcategory,
            document_date=doc_date,
            summary="Stromrechnung Test"
        )
        
        self.assertIsNotNone(saved_path)
        self.assertTrue(Path(saved_path).exists())
        print(f"  ✓ Gespeichert: {saved_path}")
        
        # 6. Datenbank
        print("Schritt 5: Datenbank...")
        doc_id = self.db.add_document(
            filepath=saved_path,
            category=category,
            subcategory=subcategory,
            document_data=doc_data,
            date_document=doc_date
        )
        
        self.assertIsNotNone(doc_id)
        print(f"  ✓ DB-Eintrag: ID {doc_id}")
        
        # 7. Suche
        print("Schritt 6: Suche...")
        results = self.db.search_documents("strom", limit=10)
        
        # Hinweis: Suche könnte leer sein, wenn Keywords nicht im Mock-Text sind
        # Aber "Rechnung" ist drin.
        # Wir suchen nach "strom", das ist NICHT im Mock-Text oben.
        # Mock-Text hat "Beratung", "Service".
        # Ich ändere die Suche auf "Beratung"
        results = self.db.search_documents("beratung", limit=10)
        
        self.assertGreater(len(results), 0)
        print(f"  ✓ Suche findet: {len(results)} Dokument(e)")
        
        print("✅ Workflow erfolgreich!")

    @patch('app.document_processor.pytesseract.image_to_string')
    def test_complete_workflow_versicherung(self, mock_ocr):
        """Test: Kompletter Workflow für Versicherung"""
        print("\n--- Test: Workflow Versicherung ---")
        
        # Mock OCR result
        mock_ocr.return_value = """
        VERSICHERUNGSPOLICE
        Police-Nr: V-998877
        Versicherungsnehmer: Max Mustermann
        
        Haftpflichtversicherung
        Beitrag: 12.50 EUR monatlich
        Laufzeit: 01.01.2024 bis 31.12.2024
        
        Allianz Versicherung AG
        """
        
        # 1. Erstelle Test-Dokument
        text = "Versicherungspolice Haftpflicht"
        img_path = self.create_test_image("police.jpg", text)
        
        # Verarbeitung
        doc_data = self.processor.process_document(str(img_path))
        category, subcategory, _ = self.categorizer.categorize(doc_data)
        
        # Assertions
        self.assertEqual(category, 'Versicherungen')
        print(f"✓ Kategorisiert als: {category}/{subcategory}")
        
        print("✅ Versicherung-Workflow erfolgreich!")
    
    def test_statistics(self):
        """Test: Statistik-Generierung"""
        print("\n--- Test: Statistiken ---")
        
        stats = self.db.get_statistics()
        
        self.assertIn('total_documents', stats)
        self.assertIn('categories', stats)
        
        print(f"  Dokumente gesamt: {stats['total_documents']}")
        print(f"  Kategorien: {stats['categories']}")
        
        print("✅ Statistiken erfolgreich!")

    def test_api_auth(self):
        """Test: API Authentifizierung"""
        print("\n--- Test: API Authentifizierung ---")
        
        # Importiere App hier, um Zirkelbezüge zu vermeiden
        from app.server import app, init_app
        
        # Init App mit Test-Config
        init_app('tests/test_config.yaml')
        app.config['TESTING'] = True
        client = app.test_client()
        
        # 1. Unautorisierter Zugriff
        print("Schritt 1: Unautorisierter Zugriff...")
        response = client.get('/api/documents')
        self.assertEqual(response.status_code, 401)
        print("  ✓ Zugriff verweigert (401)")
        
        # 2. Login
        print("Schritt 2: Login...")
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = client.post('/auth/login', json=login_data)
        self.assertEqual(response.status_code, 200)
        print("  ✓ Login erfolgreich")
        
        # 3. Autorisierter Zugriff
        print("Schritt 3: Autorisierter Zugriff...")
        response = client.get('/api/documents')
        self.assertEqual(response.status_code, 200)
        print("  ✓ Zugriff erlaubt (200)")
        
        print("✅ API Auth erfolgreich!")


if __name__ == '__main__':
    # Run tests mit verbose output
    unittest.main(verbosity=2)
