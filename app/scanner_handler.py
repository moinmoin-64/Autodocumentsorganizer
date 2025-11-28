"""
Scanner Handler für HP Scanner Integration
Überwacht Scanner und verarbeitet neue Dokumente
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import yaml

try:
    import sane
except ImportError:
    sane = None
    # Configure logging if not already configured (basic fallback)
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO)
    logging.warning("SANE module not found. Scanner functionality will be disabled.")

logger = logging.getLogger(__name__)


class ScannerHandler:
    """Verwaltet Scanner-Integration und überwacht neue Scans"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialisiert Scanner-Handler
        
        Args:
            config_path: Pfad zur Konfigurationsdatei
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.scanner_config = self.config['system']['scanner']
        self.temp_path = Path(self.config['system']['storage']['temp_path'])
        self.temp_path.mkdir(parents=True, exist_ok=True)
        
        self.scanner = None
        self.scanning = False
        
    def initialize_scanner(self) -> bool:
        """
        Initialisiert SANE und findet HP Scanner
        
        Returns:
            True wenn Scanner gefunden, sonst False
        """
        try:
            if sane is None:
                logger.warning("SANE nicht verfügbar (Windows?). Nutze Mock-Modus oder deaktiviere Scanner.")
                return False

            sane.init()
            devices = sane.get_devices()
            
            if not devices:
                logger.error("Kein Scanner gefunden!")
                return False
            
            # Finde HP Scanner
            hp_device = None
            for device in devices:
                device_name = device[0].lower()
                if 'hp' in device_name or 'hewlett' in device_name:
                    hp_device = device
                    break
            
            if hp_device:
                logger.info(f"HP Scanner gefunden: {hp_device}")
                self.scanner = sane.open(hp_device[0])
                self._configure_scanner()
                return True
            else:
                # Fallback: erster verfügbarer Scanner
                logger.warning("Kein HP Scanner gefunden, nutze erstes Gerät")
                self.scanner = sane.open(devices[0][0])
                self._configure_scanner()
                return True
                
        except Exception as e:
            logger.error(f"Fehler bei Scanner-Initialisierung: {e}")
            return False
    
    def _configure_scanner(self):
        """Konfiguriert Scanner-Parameter"""
        try:
            # Resolution
            if hasattr(self.scanner, 'resolution'):
                self.scanner.resolution = self.scanner_config['resolution']
            
            # Color Mode
            if hasattr(self.scanner, 'mode'):
                mode = self.scanner_config['color_mode']
                self.scanner.mode = mode
            
            # Format (ADF wenn verfügbar)
            if hasattr(self.scanner, 'source'):
                # Versuche ADF (Automatic Document Feeder)
                try:
                    self.scanner.source = 'ADF'
                except:
                    self.scanner.source = 'Flatbed'
            
            logger.info(f"Scanner konfiguriert: {self.scanner_config['resolution']}dpi, {self.scanner_config['color_mode']}")
            
        except Exception as e:
            logger.warning(f"Scanner-Konfiguration teilweise fehlgeschlagen: {e}")
    
    def scan_document(self) -> Optional[str]:
        """
        Scannt ein einzelnes Dokument
        
        Returns:
            Pfad zum gescannten Dokument oder None bei Fehler
        """
        if not self.scanner:
            logger.error("Scanner nicht initialisiert!")
            return None
        
        try:
            self.scanning = True
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.temp_path / f"scan_{timestamp}.jpg"
            
            logger.info(f"Starte Scan...")
            
            # Scan durchführen
            self.scanner.start()
            image = self.scanner.snap()
            
            # Als Bild speichern
            image.save(str(output_path))
            
            logger.info(f"Scan erfolgreich: {output_path}")
            self.scanning = False
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Scan-Fehler: {e}")
            self.scanning = False
            return None
    
    def scan_multi_page(self) -> list[str]:
        """
        Scannt mehrere Seiten (ADF)
        
        Returns:
            Liste von Pfaden zu gescannten Seiten
        """
        if not self.scanner:
            logger.error("Scanner nicht initialisiert!")
            return []
        
        scanned_pages = []
        page_num = 1
        
        try:
            self.scanning = True
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            while True:
                try:
                    logger.info(f"Scanne Seite {page_num}...")
                    
                    if page_num == 1:
                        self.scanner.start()
                    
                    image = self.scanner.snap()
                    
                    output_path = self.temp_path / f"scan_{timestamp}_page{page_num:02d}.jpg"
                    image.save(str(output_path))
                    
                    scanned_pages.append(str(output_path))
                    logger.info(f"Seite {page_num} gespeichert: {output_path}")
                    
                    page_num += 1
                    
                except StopIteration:
                    # Keine weiteren Seiten im ADF
                    logger.info(f"Multi-Page-Scan abgeschlossen: {len(scanned_pages)} Seiten")
                    break
                    
                except Exception as e:
                    logger.warning(f"Fehler bei Seite {page_num}: {e}")
                    break
            
            self.scanning = False
            return scanned_pages
            
        except Exception as e:
            logger.error(f"Multi-Page-Scan-Fehler: {e}")
            self.scanning = False
            return scanned_pages
    
    def watch_scanner_button(self, callback):
        """
        Überwacht Scanner-Button (Scan-Taste am Gerät)
        HINWEIS: Nicht alle Scanner unterstützen Button-Events
        
        Args:
            callback: Funktion, die aufgerufen wird wenn Scan-Button gedrückt wird
        """
        logger.info("Scanner-Button-Überwachung gestartet")
        logger.warning("Button-Erkennung ist hardware-abhängig. Fallback: nutze Web-Interface")
        
        # Für HP Scanner: verwende hp-toolbox oder Web-Interface
        # Alternativ: Überwache Verzeichnis für neue Dateien
    
    def cleanup(self):
        """Schließt Scanner-Verbindung"""
        try:
            if self.scanner:
                self.scanner.close()
            sane.exit()
            logger.info("Scanner-Verbindung geschlossen")
        except Exception as e:
            logger.error(f"Fehler beim Schließen: {e}")


def main():
    """Test-Funktion"""
    logging.basicConfig(level=logging.INFO)
    
    handler = ScannerHandler()
    
    if handler.initialize_scanner():
        print("Scanner bereit. Drücke Enter zum Scannen...")
        input()
        
        # Versuche Multi-Page
        pages = handler.scan_multi_page()
        
        if not pages:
            # Fallback: Single-Page
            page = handler.scan_document()
            if page:
                pages = [page]
        
        print(f"Gescannt: {pages}")
        
        handler.cleanup()
    else:
        print("Scanner-Initialisierung fehlgeschlagen")


if __name__ == "__main__":
    main()
