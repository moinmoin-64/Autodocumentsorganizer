"""
Image Preprocessing - Bildverbesserung für bessere OCR-Genauigkeit
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """
    Verbessert Bildqualität vor OCR-Verarbeitung
    
    Features:
    - Graustufen-Konvertierung
    - Noise Reduction
    - Deskewing (Schräglage korrigieren)
    - Adaptive Binarisierung
    - Kontrast-Verbesserung
    """
    
    def enhance(self, image_path: str) -> str:
        """
        Verbessert Bildqualität für OCR
        
        Args:
            image_path: Pfad zum Original-Bild
            
        Returns:
            Pfad zum verbesserten Bild
        """
        try:
            # Original laden
            img = cv2.imread(str(image_path))
            
            if img is None:
                logger.error(f"Could not load image: {image_path}")
                return image_path
            
            # 1. Grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 2. Noise Reduction
            denoised = cv2.fastNlMeansDenoising(gray, h=10)
            
            # 3. Deskew (Schräglage korrigieren)
            deskewed = self._deskew(denoised)
            
            # 4. Adaptive Binarization
            binary = cv2.adaptiveThreshold(
                deskewed,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2
            )
            
            # 5. Morphological Operations (kleine Artefakte entfernen)
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # 6. Kontrast-Verbesserung
            pil_img = Image.fromarray(cleaned)
            enhancer = ImageEnhance.Contrast(pil_img)
            enhanced = enhancer.enhance(1.5)
            
            # Speichern
            path_obj = Path(image_path)
            output_path = path_obj.parent / f"{path_obj.stem}_enhanced{path_obj.suffix}"
            enhanced.save(str(output_path))
            
            logger.info(f"Image enhanced: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Image enhancement failed: {e}")
            return image_path  # Return original on failure
    
    def _deskew(self, image):
        """
        Korrigiert Schräglage des Bildes
        
        Args:
            image: Grayscale image
            
        Returns:
            Rotiertes Bild
        """
        try:
            coords = np.column_stack(np.where(image > 0))
            
            if len(coords) == 0:
                return image
            
            angle = cv2.minAreaRect(coords)[-1]
            
            # Winkel korrigieren
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            # Rotation durchführen
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                image, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            
            return rotated
            
        except Exception as e:
            logger.warning(f"Deskew failed: {e}")
            return image
