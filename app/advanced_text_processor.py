"""
Advanced Text Extraction Module
Erweiterte Textextraktion mit Layout-Detection, Table-Recognition, und Barcode-Detection
"""

import logging
from typing import Dict, List, Optional, Tuple
import re
from pathlib import Path
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class LayoutDetector:
    """Erkennt Layout-Elemente in Dokumenten"""
    
    @staticmethod
    def detect_layout(text: str) -> Dict:
        """
        Erkennt Layout-Struktur im Text
        
        Args:
            text: Extrahierter Text
            
        Returns:
            Dictionary mit Layout-Informationen
        """
        lines = text.split('\n')
        
        layout = {
            'has_headers': LayoutDetector._detect_headers(lines),
            'has_footer': LayoutDetector._detect_footer(lines),
            'has_table': LayoutDetector._detect_table(text),
            'paragraph_count': LayoutDetector._count_paragraphs(lines),
            'list_count': LayoutDetector._count_lists(lines),
            'indent_levels': LayoutDetector._detect_indentation(lines),
        }
        
        return layout
    
    @staticmethod
    def _detect_headers(lines: List[str]) -> bool:
        """Prüft auf Header"""
        for i, line in enumerate(lines[:5]):  # Erste 5 Zeilen
            if line.isupper() and len(line.strip()) > 5:
                return True
        return False
    
    @staticmethod
    def _detect_footer(lines: List[str]) -> bool:
        """Prüft auf Footer"""
        for line in lines[-3:]:  # Letzte 3 Zeilen
            if 'seite' in line.lower() or 'page' in line.lower():
                return True
        return False
    
    @staticmethod
    def _detect_table(text: str) -> bool:
        """Prüft auf Tabellen-Struktur"""
        # Tabellen haben typischerweise mehrere | oder regelmäßige Abstände
        lines = text.split('\n')
        
        pipe_count = sum(1 for line in lines if '|' in line)
        if pipe_count > len(lines) * 0.2:
            return True
        
        # Prüfe auf andere Tabellen-Indikatoren
        for line in lines:
            if re.match(r'^[\s]*-+[\s]*-+', line):  # Tabellen-Trennzeichen
                return True
        
        return False
    
    @staticmethod
    def _count_paragraphs(lines: List[str]) -> int:
        """Zählt Absätze"""
        paragraphs = 0
        in_paragraph = False
        
        for line in lines:
            if line.strip():
                if not in_paragraph:
                    paragraphs += 1
                    in_paragraph = True
            else:
                in_paragraph = False
        
        return paragraphs
    
    @staticmethod
    def _count_lists(lines: List[str]) -> int:
        """Zählt Listen"""
        lists = 0
        in_list = False
        
        for line in lines:
            if re.match(r'^[\s]*[-•*]\s', line) or re.match(r'^[\s]*\d+[\.\)]\s', line):
                if not in_list:
                    lists += 1
                    in_list = True
            else:
                in_list = False
        
        return lists
    
    @staticmethod
    def _detect_indentation(lines: List[str]) -> int:
        """Erkennt Einrückungsstufen"""
        indent_levels = set()
        
        for line in lines:
            if not line.strip():
                continue
            
            spaces = len(line) - len(line.lstrip())
            if spaces > 0:
                indent_levels.add(spaces)
        
        return len(indent_levels)


class TableExtractor:
    """Extrahiert und strukturiert Tabellen aus Text"""
    
    @staticmethod
    def extract_tables(text: str) -> List[Dict]:
        """
        Extrahiert Tabellen aus Text
        
        Args:
            text: Extrahierter Text
            
        Returns:
            Liste von Tabellen
        """
        tables = []
        lines = text.split('\n')
        
        current_table = []
        in_table = False
        
        for line in lines:
            if '|' in line:
                if not in_table:
                    in_table = True
                    current_table = []
                
                # Parse Tabellen-Reihe
                cells = [cell.strip() for cell in line.split('|')]
                cells = [c for c in cells if c]  # Entferne leere
                
                if cells:
                    current_table.append(cells)
            
            else:
                if in_table and current_table:
                    # Tabelle endet
                    table_data = TableExtractor._normalize_table(current_table)
                    if table_data:
                        tables.append(table_data)
                    current_table = []
                    in_table = False
        
        # Letzte Tabelle
        if current_table:
            table_data = TableExtractor._normalize_table(current_table)
            if table_data:
                tables.append(table_data)
        
        return tables
    
    @staticmethod
    def _normalize_table(rows: List[List[str]]) -> Optional[Dict]:
        """Normalisiert und validiert Tabellen"""
        if not rows or len(rows) < 2:
            return None
        
        # Erste Reihe = Headers
        headers = rows[0]
        data_rows = rows[1:]
        
        # Alle Reihen sollten gleich viele Spalten haben
        col_count = len(headers)
        data_rows = [r for r in data_rows if len(r) == col_count]
        
        if not data_rows:
            return None
        
        return {
            'headers': headers,
            'rows': data_rows,
            'rows_count': len(data_rows),
            'cols_count': col_count,
        }


class BarcodeDetector:
    """Erkennt und validiert Barcodes"""
    
    @staticmethod
    def detect_barcodes(image_path: str) -> List[Dict]:
        """
        Versucht Barcodes im Bild zu erkennen
        
        Args:
            image_path: Pfad zum Bild
            
        Returns:
            Liste von erkannten Barcodes
        """
        barcodes = []
        
        try:
            # Versuche pyzbar zu nutzen wenn verfügbar
            try:
                from pyzbar import pyzbar
                
                image = Image.open(image_path)
                detected = pyzbar.decode(image)
                
                for barcode in detected:
                    barcodes.append({
                        'type': barcode.type,
                        'data': barcode.data.decode('utf-8'),
                        'quality': 'high',
                    })
                
                if barcodes:
                    logger.info(f"✅ {len(barcodes)} Barcodes erkannt")
            
            except ImportError:
                logger.debug("pyzbar nicht verfügbar, überspringe Barcode-Detection")
        
        except Exception as e:
            logger.warning(f"Barcode-Detection fehlgeschlagen: {e}")
        
        return barcodes


class TextQualityAnalyzer:
    """Analysiert Qualität von extrahiertem Text"""
    
    @staticmethod
    def analyze_quality(text: str, ocr_confidence: float = 0.0) -> Dict:
        """
        Analysiert Qualität des extrahierten Texts
        
        Args:
            text: Extrahierter Text
            ocr_confidence: OCR Confidence-Score (0-100)
            
        Returns:
            Dictionary mit Qualitäts-Metriken
        """
        lines = text.split('\n')
        
        return {
            'text_length': len(text),
            'word_count': len(text.split()),
            'line_count': len(lines),
            'avg_line_length': np.mean([len(l) for l in lines if l]) if lines else 0,
            'has_numbers': TextQualityAnalyzer._has_numbers(text),
            'has_special_chars': TextQualityAnalyzer._has_special_chars(text),
            'language_detected': TextQualityAnalyzer._detect_language(text),
            'ocr_confidence': ocr_confidence,
            'quality_score': TextQualityAnalyzer._calculate_quality_score(text, ocr_confidence),
        }
    
    @staticmethod
    def _has_numbers(text: str) -> bool:
        """Prüft ob Text Zahlen enthält"""
        return bool(re.search(r'\d', text))
    
    @staticmethod
    def _has_special_chars(text: str) -> bool:
        """Prüft auf Sonderzeichen"""
        return bool(re.search(r'[€$¥£%©®™]', text))
    
    @staticmethod
    def _detect_language(text: str) -> str:
        """Erkennt Sprache"""
        try:
            from langdetect import detect
            return detect(text)
        except:
            return "unknown"
    
    @staticmethod
    def _calculate_quality_score(text: str, ocr_confidence: float) -> float:
        """Berechnet Overall-Quality-Score"""
        score = 0.0
        
        # Text-Länge
        word_count = len(text.split())
        if word_count > 100:
            score += 0.3
        elif word_count > 50:
            score += 0.2
        
        # OCR Confidence
        score += (ocr_confidence / 100) * 0.5
        
        # Hat wichtige Elemente
        if TextQualityAnalyzer._has_numbers(text):
            score += 0.1
        
        if TextQualityAnalyzer._has_special_chars(text):
            score += 0.1
        
        return min(score, 1.0)


class AdvancedTextProcessor:
    """Hauptklasse für erweiterte Textverarbeitung"""
    
    def __init__(self):
        """Initialisiert Processor"""
        self.layout_detector = LayoutDetector()
        self.table_extractor = TableExtractor()
        self.barcode_detector = BarcodeDetector()
        self.quality_analyzer = TextQualityAnalyzer()
    
    def process_with_advanced_analysis(
        self,
        text: str,
        image_path: Optional[str] = None,
        ocr_confidence: float = 0.0
    ) -> Dict:
        """
        Verarbeitet Text mit erweiterten Analysen
        
        Args:
            text: Extrahierter Text
            image_path: Optional Pfad zum Bild für Barcode-Detection
            ocr_confidence: OCR Confidence-Score
            
        Returns:
            Dictionary mit vollständigen Analyse-Ergebnissen
        """
        # Layout-Analyse
        layout = self.layout_detector.detect_layout(text)
        
        # Tabellen-Extraktion
        tables = self.table_extractor.extract_tables(text)
        
        # Barcode-Detection
        barcodes = []
        if image_path and Path(image_path).exists():
            barcodes = self.barcode_detector.detect_barcodes(image_path)
        
        # Qualitäts-Analyse
        quality = self.quality_analyzer.analyze_quality(text, ocr_confidence)
        
        return {
            'layout': layout,
            'tables': tables,
            'barcodes': barcodes,
            'quality': quality,
        }
