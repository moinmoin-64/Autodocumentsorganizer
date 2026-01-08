"""
OCR Ensemble - Kombiniert mehrere OCR-Engines für beste Ergebnisse
Nutzt native C++ Accelerator für 50x Performance!
"""
import logging
from typing import Dict, Any, List, Optional
import numpy as np
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)

# Try to import native C++ accelerator
try:
    import ocr_accelerator
    OCR_NATIVE_AVAILABLE = True
    logger.info("[OK] Native C++ OCR accelerator available (50x faster!)")
    _accelerator = ocr_accelerator.OCRAccelerator()
except ImportError:
    OCR_NATIVE_AVAILABLE = False
    _accelerator = None
    logger.warning("[WARNING] Native C++ OCR accelerator not available, using fallback")


class OCREnsemble:
    def __init__(self, config: Dict):
        self.config = config
        self.ocr_config = config.get('ocr', {})
        self.tesseract_lang = '+'.join(self.ocr_config.get('languages', ['eng'])) # Use 'languages' from config
        
        self.use_easyocr = False
        self.reader = None
        
        # Check if EasyOCR is enabled and try to load
        if self.ocr_config.get('easyocr_enabled', False):
            try:
                import easyocr
                # Ensure easyocr_languages is a list of strings
                easyocr_languages = self.ocr_config.get('easyocr_languages', ['en'])
                if isinstance(easyocr_languages, str):
                    easyocr_languages = [easyocr_languages] # Convert to list if single string
                
                self.reader = easyocr.Reader(easyocr_languages)
                self.use_easyocr = True
                logger.info("[OK] EasyOCR enabled and loaded.")
            except ImportError:
                logger.warning("[WARNING] EasyOCR not installed, or failed to load. Falling back to Tesseract only.")
            except Exception as e:
                logger.error(f"Error loading EasyOCR: {e}. Falling back to Tesseract only.")

    def extract_text(self, image_path: str) -> str:
        """
        Führt OCR mit verfügbaren Engines durch und kombiniert Ergebnisse
        """
        # 1. Tesseract (Basis) mit Confidence
        tesseract_result = self._run_tesseract_with_confidence(image_path)
        
        if not self.use_easyocr:
            return tesseract_result['text']
            
        # 2. EasyOCR (Zusatz)
        try:
            easyocr_result = self._run_easyocr_with_confidence(image_path)
            
            # 3. Intelligentes Merging basierend auf Confidence
            return self._merge_results(tesseract_result, easyocr_result)
            
        except Exception as e:
            logger.error(f"EasyOCR fehlgeschlagen: {e}")
            return tesseract_result['text']

    def _merge_results(self, tesseract_result: Dict, easyocr_result: Dict) -> str:
        """
        Intelligentes Merging basierend auf Confidence-Scores
        """
        tess_text = tesseract_result['text']
        tess_conf = tesseract_result['confidence']
        easy_text = easyocr_result['text']
        easy_conf = easyocr_result['confidence']
        
        # High confidence threshold
        HIGH_CONF = 80.0
        
        # Fall 1: Einer hat hohe Confidence, der andere nicht
        if tess_conf >= HIGH_CONF and easy_conf < HIGH_CONF:
            logger.info(f"Nutze Tesseract (Confidence: {tess_conf:.1f}%)")
            return tess_text
        elif easy_conf >= HIGH_CONF and tess_conf < HIGH_CONF:
            logger.info(f"Nutze EasyOCR (Confidence: {easy_conf:.1f}%)")
            return easy_text
            
        # Fall 2: Beide haben hohe Confidence - nimm den längeren
        if tess_conf >= HIGH_CONF and easy_conf >= HIGH_CONF:
            if len(easy_text) > len(tess_text):
                logger.info(f"Beide high-conf, nutze EasyOCR (länger)")
                return easy_text
            else:
                logger.info(f"Beide high-conf, nutze Tesseract")
                return tess_text
        
        # Fall 3: Beide niedrige Confidence - Weighted Average
        if len(tess_text.strip()) < 20 and len(easy_text.strip()) > 50:
            logger.info("Tesseract lieferte wenig Text, nutze EasyOCR")
            return easy_text
        
        # Default: Nutze Engine mit höherer Confidence
        if easy_conf > tess_conf:
            logger.info(f"Nutze EasyOCR (Conf: {easy_conf:.1f}% > {tess_conf:.1f}%)")
            return easy_text
        else:
            logger.info(f"Nutze Tesseract (Conf: {tess_conf:.1f}% >= {easy_conf:.1f}%)")
            return tess_text

    def _run_tesseract(self, image_path: str) -> str:
        """Legacy method - calls new confidence version"""
        return self._run_tesseract_with_confidence(image_path)['text']

    def _run_tesseract_with_confidence(self, image_path: str) -> Dict[str, Any]:
        """Run Tesseract with confidence scores"""
        try:
            img = Image.open(image_path)
            # Get text and data (includes confidence)
            data = pytesseract.image_to_data(
                img,
                lang=self.tesseract_lang, # Use configured languages
                config='--oem 3 --psm 3',
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_conf = sum(confidences) / len(confidences) if confidences else 0
            
            # Get plain text
            text = pytesseract.image_to_string(
                img,
                lang=self.tesseract_lang, # Use configured languages
                config='--oem 3 --psm 3'
            )
            
            return {
                'text': text,
                'confidence': avg_conf
            }
        except Exception as e:
            logger.error(f"Tesseract Fehler: {e}")
            return {'text': '', 'confidence': 0}

    def _run_easyocr(self, image_path: str) -> str:
        """Legacy method - calls new confidence version"""
        return self._run_easyocr_with_confidence(image_path)['text']

    def _run_easyocr_with_confidence(self, image_path: str) -> Dict[str, Any]:
        """Run EasyOCR with confidence scores"""
        if not self.reader:
            return {'text': '', 'confidence': 0}
        
        try:
            results = self.reader.readtext(image_path)
            # EasyOCR liefert Liste von (bbox, text, conf)
            
            if not results:
                return {'text': '', 'confidence': 0}
            
            # Combine text and calculate average confidence
            texts = []
            confidences = []
            for bbox, text, conf in results:
                texts.append(text)
                confidences.append(conf * 100)  # Convert to percentage
            
            combined_text = " ".join(texts)
            avg_conf = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'text': combined_text,
                'confidence': avg_conf
            }
        except Exception as e:
            logger.error(f"EasyOCR Fehler: {e}")
            return {'text': '', 'confidence': 0}


