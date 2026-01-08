"""
Test für Categorizer
Testet AI-basierte Kategorisierung
"""

import unittest
import sys
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.categorizer import DocumentCategorizer


class TestCategorizer(unittest.TestCase):
    """Tests für DocumentCategorizer"""
    
    @classmethod
    def setUpClass(cls):
        """Initialisiere Categorizer einmal"""
        # Get config from pytest fixture - we'll use lazy initialization
        cls.categorizer = None
        cls.config = None
    
    @pytest.fixture(autouse=True)
    def setup_with_config(self, app):
        """Setup with actual app config"""
        if self.categorizer is None:
            self.__class__.config = app.config
            self.__class__.categorizer = DocumentCategorizer(app.config)
    
    def test_categorize_rechnung(self):
        """Test: Rechnung wird korrekt kategorisiert"""
        if self.categorizer is None:
            pytest.skip("Categorizer not initialized")
        doc = {
            'text': 'Rechnung für Stromverbrauch Januar 2024. Betrag: 45,50 EUR. Stadtwerke München.',
            'keywords': ['rechnung', 'strom', 'betrag', 'stadtwerke']
        }
        
        category, subcategory, confidence = self.categorizer.categorize(doc)
        
        self.assertEqual(category, 'Rechnungen')
        self.assertIn('Strom', subcategory)
        self.assertGreater(confidence, 0)
    
    def test_categorize_versicherung(self):
        """Test: Versicherung wird korrekt kategorisiert"""
        doc = {
            'text': 'Ihre KFZ-Versicherung. Police-Nr: 12345. Jahresbeitrag: 450 EUR.',
            'keywords': ['versicherung', 'kfz', 'police', 'beitrag']
        }
        
        category, subcategory, confidence = self.categorizer.categorize(doc)
        
        self.assertEqual(category, 'Versicherungen')
        self.assertIn('KFZ', subcategory)
    
    def test_categorize_vertrag(self):
        """Test: Vertrag wird korrekt kategorisiert"""
        doc = {
            'text': 'Mietvertrag für Wohnung in Berlin. Kaltmiete: 850 EUR monatlich.',
            'keywords': ['vertrag', 'miete', 'wohnung', 'berlin']
        }
        
        category, subcategory, confidence = self.categorizer.categorize(doc)
        
        self.assertEqual(category, 'Verträge')
        self.assertIn('Mietvertrag', subcategory)
    
    def test_subcategorize_rechnung(self):
        """Test: Rechnungs-Subkategorisierung"""
        text = "Ihre Stromrechnung von den Stadtwerken"
        subcategory = self.categorizer._subcategorize_rechnung(text, [])
        
        self.assertEqual(subcategory, 'Strom')
    
    def test_subcategorize_versicherung(self):
        """Test: Versicherungs-Subkategorisierung"""
        text = "Ihre Krankenversicherung bei der AOK"
        subcategory = self.categorizer._subcategorize_versicherung(text, [])
        
        self.assertEqual(subcategory, 'Krankenversicherung')


if __name__ == '__main__':
    unittest.main()
