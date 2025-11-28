"""
Document Processor - OCR und Text-Extraktion
Verarbeitet gescannte Dokumente und extrahiert Text
"""

import logging
import re
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import yaml

# OCR
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import pdfplumber

# Datum-Extraktion
import dateparser
from dateutil import parser as date_parser

# Text-Verarbeitung
from langdetect import detect

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Verarbeitet gescannte Dokumente mit OCR und Text-Extraktion"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialisiert Document Processor
        
        Args:
            config_path: Pfad zur Konfigurationsdatei
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.ocr_config = self.config['ocr']
        
        # Tesseract Sprachen
        self.tesseract_lang = '+'.join(self.ocr_config['languages'])
        
        # Image Preprocessor für bessere OCR-Genauigkeit
        try:
            from app.image_preprocessor import ImagePreprocessor
            self.preprocessor = ImagePreprocessor()
            self.use_preprocessing = True
            logger.info("Image Preprocessor aktiviert")
        except Exception as e:
            logger.warning(f"Image Preprocessor nicht verfügbar: {e}")
            self.preprocessor = None
            self.use_preprocessing = False
        
        # Image Preprocessor für bessere OCR-Genauigkeit
        try:
            from app.image_preprocessor import ImagePreprocessor
            self.preprocessor = ImagePreprocessor()
            self.use_preprocessing = True
            logger.info("Image Preprocessor aktiviert")
        except Exception as e:
            logger.warning(f"Image Preprocessor nicht verfügbar: {e}")
            self.preprocessor = None
            self.use_preprocessing = False

    def process_document(self, file_path: str) -> Dict:
        """
        Verarbeitet ein Dokument komplett
        """
        # Lazy Import um Zyklen zu vermeiden
        from app.metrics import PROCESSING_DURATION_SECONDS, DOCUMENT_PROCESSED_TOTAL
        
        start_time = datetime.now()
        try:
            with PROCESSING_DURATION_SECONDS.labels(stage='total').time():
                return self._process_document_internal(file_path)
        except Exception as e:
            DOCUMENT_PROCESSED_TOTAL.labels(status='error', category='unknown').inc()
            raise e

    def _process_document_internal(self, file_path: str) -> Dict:
        """
        Interne Verarbeitungslogik
        
        Args:
            file_path: Pfad zum Dokument
            
        Returns:
            Dict mit extrahierten Informationen
        """
        logger.info(f"Verarbeite Dokument: {file_path}")
        
        result = {
            'file_path': file_path,
            'text': '',
            'detected_language': None,
            'dates': [],
            'amounts': [],
            'keywords': [],
            'confidence': 0,
            'processing_time': 0
        }
        
        start_time = datetime.now()
        
        try:
            # Text extrahieren
            text = self._extract_text(file_path)
            result['text'] = text
            
            if not text or len(text.strip()) < 10:
                logger.warning(f"Kein oder zu wenig Text extrahiert: {file_path}")
                return result
            
            # Sprache erkennen
            try:
                result['detected_language'] = detect(text)
            except:
                result['detected_language'] = 'de'
            
            # Datum extrahieren
            result['dates'] = self._extract_dates(text)
            
            # Geldbeträge extrahieren
            result['amounts'] = self._extract_amounts(text)

            # Keywords extrahieren
            result['keywords'] = self._extract_keywords(text)
            
            # Confidence berechnen
            result['confidence'] = self._calculate_confidence(result)
            
            # KI-Erweiterungen (OCR-Korrektur & Validierung)
            if self.config.get('ai', {}).get('ollama', {}).get('enabled', False):
                try:
                    # OCR Korrektur
                    if result['confidence'] < 0.8:  # Nur bei unsicherem OCR
                        corrected_text = self._correct_ocr_with_llm(text)
                        if corrected_text:
                            result['text'] = corrected_text
                            # Neu extrahieren mit korrigiertem Text
                            result['dates'] = self._extract_dates(corrected_text)
                            result['amounts'] = self._extract_amounts(corrected_text)
                            result['keywords'] = self._extract_keywords(corrected_text)
                    
                    # Validierung
                    validation = self._validate_document_with_llm(result['text'])
                    if validation:
                        result['validation'] = validation
                        # Merge AI data if better
                        if validation.get('date') and not result['dates']:
                            result['dates'] = [validation['date']]
                        if validation.get('amount') and not result['amounts']:
                            result['amounts'] = [validation['amount']]
                            
                except Exception as e:
                    logger.warning(f"KI-Verarbeitung fehlgeschlagen: {e}")
            
            end_time = datetime.now()
            result['processing_time'] = (end_time - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            logger.error(f"Fehler bei Dokumentenverarbeitung: {e}")
            return result

    def _correct_ocr_with_llm(self, text: str) -> Optional[str]:
        """Korrigiert OCR-Fehler mit LLM"""
        try:
            from app.ollama_client import OllamaClient
            client = OllamaClient()
            
            prompt = f"""Korrigiere OCR-Fehler im folgenden Text. 
            Behalte das Format bei. Antworte NUR mit dem korrigierten Text.
            
            Text:
            {text[:2000]}"""  # Limit context
            
            return client.chat(prompt)
        except:
            return None

    def _validate_document_with_llm(self, text: str) -> Optional[Dict]:
        """Validiert Dokument und extrahiert Metadaten mit LLM"""
        try:
            from app.ollama_client import OllamaClient
            client = OllamaClient()
            
            prompt = f"""Analysiere dieses Dokument und extrahiere:
            - Datum (YYYY-MM-DD)
            - Gesamtbetrag (Zahl)
            - Währung
            - Kategorie (Rechnung, Vertrag, Versicherung, Sonstiges)
            
            Antworte als JSON.
            
            Text:
            {text[:2000]}"""
            
            response = client.chat(prompt)
            # Versuche JSON zu parsen (einfach)
            import json
            # Finde JSON im Text
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return None
        except:
            return None

    def _calculate_confidence(self, result: Dict) -> float:
        """Berechnet Konfidenz-Score (0-1)"""
        score = 0.0
        
        # Text-Länge
        if len(result['text']) > 50: score += 0.3
        
        # Datum gefunden
        if result['dates']: score += 0.3
        
        # Betrag gefunden
        if result['amounts']: score += 0.2
        
        # Sprache erkannt
        if result['detected_language'] == 'de': score += 0.2
        
        return min(1.0, score)
            
    def _extract_text(self, file_path: str) -> str:
        """
        Extrahiert Text aus Bild oder PDF
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            Extrahierter Text
        """
        file_path = Path(file_path)
        
        try:
            if file_path.suffix.lower() == '.pdf':
                return self._extract_text_from_pdf(str(file_path))
            else:
                return self._extract_text_from_image(str(file_path))
        except Exception as e:
            logger.error(f"Text-Extraktion fehlgeschlagen: {e}")
            return ""
    
    def _extract_text_from_image(self, image_path: str) -> str:
        """OCR auf Bild (mit optionalem Pre-Processing)"""
        try:
            # Image Pre-Processing für bessere OCR-Genauigkeit
            processed_path = image_path
            if self.use_preprocessing and self.preprocessor:
                try:
                    processed_path = self.preprocessor.enhance(image_path)
                    logger.debug(f"Image enhanced: {processed_path}")
                except Exception as e:
                    logger.warning(f"Image preprocessing failed, using original: {e}")
                    processed_path = image_path
            
            with Image.open(processed_path) as image:
                # OCR Ensemble nutzen
                from app.metrics import OCR_DURATION_SECONDS, OCR_REQUESTS_TOTAL
                
                OCR_REQUESTS_TOTAL.labels(engine='ensemble', language=self.tesseract_lang).inc()
                
                with OCR_DURATION_SECONDS.observe():
                    # Initialisiere Ensemble (Lazy Loading)
                    if not hasattr(self, 'ocr_ensemble'):
                        from app.ocr_ensemble import OCREnsemble
                        self.ocr_ensemble = OCREnsemble(self.config)
                    
                    text = self.ocr_ensemble.extract_text(processed_path)
                
                return text.strip()
            
        except Exception as e:
            logger.error(f"Bild-OCR fehlgeschlagen: {e}")
            return ""
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrahiert Text aus PDF (mit OCR falls nötig)"""
        try:
            # Zuerst: versuche Text direkt zu extrahieren
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # Wenn kein Text → OCR
            if not text or len(text.strip()) < 50:
                logger.info("PDF enthält keinen Text, führe OCR durch...")
                text = self._ocr_pdf(pdf_path)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"PDF-Text-Extraktion fehlgeschlagen: {e}")
            return ""
    
    def _ocr_pdf(self, pdf_path: str) -> str:
        """OCR auf PDF durchführen"""
        try:
            # Konvertiere PDF zu Bildern
            images = convert_from_path(pdf_path, dpi=300)
            
            text = ""
            for i, image in enumerate(images):
                logger.info(f"OCR auf Seite {i+1}/{len(images)}...")
                page_text = pytesseract.image_to_string(
                    image,
                    lang=self.tesseract_lang
                )
                text += page_text + "\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"PDF-OCR fehlgeschlagen: {e}")
            return ""
    
    def _extract_dates(self, text: str) -> List[datetime]:
        """
        Extrahiert Daten aus Text
        
        Args:
            text: Eingabetext
            
        Returns:
            Liste von gefundenen Daten (sortiert, ältestes zuerst)
        """
        dates = []
        
        # Deutsche Datumsformate mit Kontext
        # Suche nach Ausdrücken wie "Datum:", "vom", "Rechnungsdatum" etc.
        context_patterns = [
            r'(?:datum|vom|am|den)\s*[:.]?\s*(\d{1,2}[\./]\d{1,2}[\./]\d{2,4})',
            r'(\d{1,2}[\./]\d{1,2}[\./]\d{2,4})',  # Allgemein
        ]
        
        for pattern in context_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1) if len(match.groups()) > 0 else match.group(0)
                try:
                    # Versuche zu parsen
                    parsed_date = dateparser.parse(
                        date_str, 
                        languages=['de', 'en'],
                        settings={'PREFER_DAY_OF_MONTH': 'first'}
                    )
                    if parsed_date:
                        # Filter unrealistische Daten
                        current_year = datetime.now().year
                        if 1990 <= parsed_date.year <= current_year + 1:
                            if parsed_date not in dates:
                                dates.append(parsed_date)
                except:
                    pass
        
        # Sortiere nach Datum (neuestes zuerst ist meist relevant)
        dates.sort(reverse=True)
        
        # Log für Debugging
        if dates:
            logger.debug(f"Gefundene Daten: {[d.strftime('%Y-%m-%d') for d in dates]}")
        else:
            logger.warning("⚠️  Kein Datum im Dokument erkannt!")
        
        return dates
    
    def _extract_amounts(self, text: str) -> List[float]:
        """
        Extrahiert Geldbeträge aus Text
        
        Args:
            text: Eingabetext
            
        Returns:
            Liste von gefundenen Beträgen
        """
        amounts = []
        
        # Patterns für Geldbeträge
        patterns = [
            r'(\d{1,3}(?:\.\d{3})*,\d{2})\s*€',  # 1.234,56 €
            r'€\s*(\d{1,3}(?:\.\d{3})*,\d{2})',  # € 1.234,56
            r'EUR\s*(\d{1,3}(?:\.\d{3})*,\d{2})',  # EUR 1.234,56
            r'(\d{1,3}(?:\.\d{3})*,\d{2})\s*EUR',  # 1.234,56 EUR
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # German format -> float
                    amount_str = match.replace('.', '').replace(',', '.')
                    amount = float(amount_str)
                    if amount not in amounts:
                        amounts.append(amount)
                except:
                    pass
        
        return sorted(amounts, reverse=True)  # Größte zuerst
    
    def _extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """
        Extrahiert wichtige Keywords aus Text
        
        Args:
            text: Eingabetext
            max_keywords: Maximale Anzahl Keywords
            
        Returns:
            Liste von Keywords
        """
        # Einfache Keyword-Extraktion (häufigste Wörter)
        # Entferne Stopwords
        stopwords = {
            'der', 'die', 'das', 'und', 'oder', 'aber', 'ein', 'eine', 'einen',
            'dem', 'den', 'des', 'im', 'in', 'von', 'zu', 'mit', 'auf', 'für',
            'ist', 'sind', 'wird', 'werden', 'wurde', 'wurden', 'sein', 'haben',
            'hat', 'kann', 'soll', 'muss', 'dass', 'als', 'wenn', 'wie', 'bei',
            'nach', 'vor', 'über', 'unter', 'zwischen', 'durch', 'an', 'aus'
        }
        
        # Normalisiere Text
        words = re.findall(r'\b[a-zäöüß]{3,}\b', text.lower())
        
        # Filtere Stopwords und zähle
        word_freq = {}
        for word in words:
            if word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sortiere nach Häufigkeit
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        keywords = [word for word, freq in sorted_words[:max_keywords]]
        
        return keywords
    
    def _calculate_confidence(self, result: Dict) -> int:
        """
        Berechnet Confidence-Score basierend auf extrahierten Daten
        
        Args:
            result: Ergebnis-Dictionary
            
        Returns:
            Confidence-Score (0-100)
        """
        score = 0
        
        # Text vorhanden
        if result['text'] and len(result['text']) > 50:
            score += 30
        
        # Datum gefunden
        if result['dates']:
            score += 25
        
        # Betrag gefunden
        if result['amounts']:
            score += 25
        
        # Keywords vorhanden
        if len(result['keywords']) >= 5:
            score += 20
        
        return min(score, 100)


def main():
    """Test-Funktion"""
    logging.basicConfig(level=logging.INFO)
    
    processor = DocumentProcessor()
    
    # Test mit Beispiel-Datei
    test_file = input("Pfad zu Test-Dokument: ")
    
    if Path(test_file).exists():
        result = processor.process_document(test_file)
        
        print("\n=== Ergebnisse ===")
        print(f"Sprache: {result['detected_language']}")
        print(f"Daten gefunden: {result['dates']}")
        print(f"Beträge gefunden: {result['amounts']}")
        print(f"Keywords: {result['keywords'][:10]}")
        print(f"Confidence: {result['confidence']}%")
        print(f"\nText (erste 500 Zeichen):\n{result['text'][:500]}...")
    else:
        print("Datei nicht gefunden!")


if __name__ == "__main__":
    main()
