"""
OCR Ensemble - Kombiniert mehrere OCR-Engines für beste Ergebnisse
"""

import logging
import numpy as np
from PIL import Image
import pytesseract
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class OCREnsemble:
    """
    Kombiniert Tesseract und EasyOCR (falls verfügbar)
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.use_easyocr = False
        self.reader = None
        
        # Versuche EasyOCR zu laden
        try:
            import easyocr
            # Initialisiere Reader nur für Deutsch und Englisch (CPU mode default)
            self.reader = easyocr.Reader(['de', 'en'], gpu=False)
            self.use_easyocr = True
            logger.info("EasyOCR erfolgreich initialisiert")
        except ImportError:
            logger.info("EasyOCR nicht installiert, nutze nur Tesseract")
        except Exception as e:
            logger.warning(f"Fehler beim Initialisieren von EasyOCR: {e}")

    def extract_text(self, image_path: str) -> str:
        """
        Führt OCR mit verfügbaren Engines durch und kombiniert Ergebnisse
        """
        # 1. Tesseract (Basis)
        tesseract_text = self._run_tesseract(image_path)
        
        if not self.use_easyocr:
            return tesseract_text
            
        # 2. EasyOCR (Zusatz)
        try:
            easyocr_text = self._run_easyocr(image_path)
            
            # 3. Ensemble Logic (Simple Merge for now)
            # Wenn Tesseract sehr wenig Text liefert, nimm EasyOCR
            if len(tesseract_text.strip()) < 50 and len(easyocr_text.strip()) > 50:
                logger.info("Nutze EasyOCR Ergebnis (Tesseract lieferte wenig Text)")
                return easyocr_text
                
            # Wenn beide Text liefern, nimm den längeren (oft besser)
            # TODO: Intelligenteres Merging basierend auf Confidence
            if len(easyocr_text) > len(tesseract_text) * 1.2:
                logger.info("Nutze EasyOCR Ergebnis (deutlich mehr Text)")
                return easyocr_text
                
            return tesseract_text
            
        except Exception as e:
            logger.error(f"EasyOCR fehlgeschlagen: {e}")
            return tesseract_text

    def _run_tesseract(self, image_path: str) -> str:
        try:
            return pytesseract.image_to_string(
                Image.open(image_path),
                lang='deu+eng',
                config='--oem 3 --psm 3'
            )
        except Exception as e:
            logger.error(f"Tesseract Fehler: {e}")
            return ""

    def _run_easyocr(self, image_path: str) -> str:
        if not self.reader:
            return ""
        
        results = self.reader.readtext(image_path)
        # EasyOCR liefert Liste von (bbox, text, conf)
        text = " ".join([res[1] for res in results])
        return text
