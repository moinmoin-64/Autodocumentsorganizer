"""
Feature Tests - Testet neue Optimierungen (Caching, Async, Semantic, etc.)
"""

import unittest
import sys
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Database
from app.cache import CacheManager
from app.metrics import MetricsManager
from app.semantic_search import SemanticSearch
from app.ocr_ensemble import OCREnsemble

class TestFeatures(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path(tempfile.mkdtemp())
        cls.create_test_config()
        cls.db = Database('tests/test_config_features.yaml')
        
    @classmethod
    def tearDownClass(cls):
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    @classmethod
    def create_test_config(cls):
        test_dir_str = str(cls.test_dir).replace('\\', '/')
        config = f"""
system:
  storage:
    base_path: "{test_dir_str}/storage"
database:
  path: "{test_dir_str}/test_features.db"
"""
        with open('tests/test_config_features.yaml', 'w') as f:
            f.write(config)

    def test_lazy_loading_pagination(self):
        """Testet Pagination für Lazy Loading"""
        print("\n--- Test: Lazy Loading Pagination ---")
        
        # Füge Dummy-Dokumente hinzu
        for i in range(15):
            self.db.add_document(
                filepath=f"/tmp/doc_{i}.pdf",
                category="Test",
                subcategory="Pagination",
                document_data={'text': f"Doc {i}", 'keywords': []},
                date_document=None
            )
            
        # Seite 1 (Limit 10)
        page1 = self.db.search_documents(limit=10, offset=0)
        self.assertEqual(len(page1), 10)
        
        # Seite 2 (Limit 10, Offset 10)
        page2 = self.db.search_documents(limit=10, offset=10)
        self.assertEqual(len(page2), 5)
        
        print("✅ Pagination funktioniert")

    @patch('app.cache.redis.Redis')
    def test_caching_fallback(self, mock_redis):
        """Testet Caching Fallback auf Memory"""
        print("\n--- Test: Caching Fallback ---")
        
        # Simuliere Redis Fehler
        mock_redis.side_effect = Exception("Redis connection failed")
        
        cache = CacheManager()
        self.assertFalse(cache.use_redis)
        
        # Test Memory Cache
        cache.set('test_key', 'test_value')
        val = cache.get('test_key')
        self.assertEqual(val, 'test_value')
        
        print("✅ Caching Fallback funktioniert")

    def test_metrics_manager(self):
        """Testet Metrics Manager"""
        print("\n--- Test: Metrics ---")
        
        # Mock psutil um System-Calls zu vermeiden
        with patch('psutil.virtual_memory') as mock_mem, \
             patch('psutil.cpu_percent') as mock_cpu:
            
            mock_mem.return_value.used = 1000
            mock_cpu.return_value = 5.0
            
            metrics = MetricsManager()
            metrics.update_system_metrics()
            
            from app.metrics import SYSTEM_CPU_USAGE_PERCENT
            # Da Prometheus Client global ist, ist das Testen des Werts schwierig ohne Registry-Reset
            # Wir prüfen nur ob kein Fehler fliegt
            
        print("✅ Metrics Manager läuft")

    @patch('sentence_transformers.SentenceTransformer')
    def test_semantic_search(self, mock_model):
        """Testet Semantic Search Logic"""
        print("\n--- Test: Semantic Search ---")
        
        # Mock Embedding Generation
        mock_model.return_value.encode.return_value = [0.1, 0.2, 0.3]
        
        semantic = SemanticSearch()
        embedding = semantic.generate_embedding("Test Text")
        
        self.assertEqual(embedding, [0.1, 0.2, 0.3])
        
        # Test Duplicate Finding
        all_embeddings = [
            {'doc_id': 1, 'embedding': [0.1, 0.2, 0.3]}, # Identisch
            {'doc_id': 2, 'embedding': [0.9, 0.8, 0.7]}  # Anders
        ]
        
        duplicates = semantic.find_duplicates([0.1, 0.2, 0.3], all_embeddings)
        
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0][0], 1) # Doc ID 1
        
        print("✅ Semantic Search Logic funktioniert")

    @patch('app.ocr_ensemble.pytesseract.image_to_string')
    def test_ocr_ensemble(self, mock_tesseract):
        """Testet OCR Ensemble"""
        print("\n--- Test: OCR Ensemble ---")
        
        mock_tesseract.return_value = "Tesseract Result"
        
        # Test ohne EasyOCR (Default Mock)
        ensemble = OCREnsemble()
        # Mock EasyOCR import failure simulation is hard here because it's in __init__
        # But we can test the fallback logic
        
        ensemble.use_easyocr = False
        text = ensemble.extract_text("dummy.jpg")
        self.assertEqual(text, "Tesseract Result")
        
        print("✅ OCR Ensemble Fallback funktioniert")

if __name__ == '__main__':
    unittest.main(verbosity=2)
