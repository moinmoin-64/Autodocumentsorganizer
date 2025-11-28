"""
Test für Document Processor
Testet OCR und Text-Extraktion
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.document_processor import DocumentProcessor


class TestDocumentProcessor(unittest.TestCase):
    """Tests für DocumentProcessor"""
    
    @classmethod
    def setUpClass(cls):
        """Initialisiere Processor einmal für alle Tests"""
        cls.processor = DocumentProcessor()
    
    def test_initialization(self):
        """Test: Processor wird korrekt initialisiert"""
        self.assertIsNotNone(self.processor)
        self.assertIn('deu', self.processor.ocr_config['languages'])
    
    def test_extract_dates(self):
        """Test: Datum-Extraktion"""
        text = "Rechnung vom 15.01.2024 für Januar 2024"
        dates = self.processor._extract_dates(text)
        
        self.assertGreater(len(dates), 0)
        self.assertEqual(dates[0].day, 15)
        self.assertEqual(dates[0].month, 1)
        self.assertEqual(dates[0].year, 2024)
    
    def test_extract_amounts(self):
        """Test: Geldbetrags-Extraktion"""
        text = "Gesamtbetrag: 1.234,56 EUR"
        amounts = self.processor._extract_amounts(text)
        
        self.assertGreater(len(amounts), 0)
        self.assertAlmostEqual(amounts[0], 1234.56, places=2)
    
    def test_extract_keywords(self):
        """Test: Keyword-Extraktion"""
        text = "Stromrechnung für Januar. Stadtwerke München. Verbrauch: 150 kWh"
        keywords = self.processor._extract_keywords(text)
        
        self.assertGreater(len(keywords), 0)
        self.assertIn('stromrechnung', [kw.lower() for kw in keywords])
    
    def test_confidence_calculation(self):
        """Test: Confidence-Berechnung"""
        result = {
            'text': 'Test text with more than 50 characters to pass the threshold',
            'dates': [None],
            'amounts': [100.0],
            'keywords': ['test', 'rechnung', 'betrag', 'firma', 'datum']
        }
        
        confidence = self.processor._calculate_confidence(result)
        
        self.assertGreater(confidence, 0)
        self.assertLessEqual(confidence, 100)


if __name__ == '__main__':
    unittest.main()
