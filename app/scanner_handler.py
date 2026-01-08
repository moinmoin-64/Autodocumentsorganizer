"""
Scanner Handler für HP Scanner Integration
Überwacht Scanner und verarbeitet neue Dokumente
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import yaml

# SANE Module - optional, aber funktional auf Linux
try:
    import sane
    SANE_AVAILABLE = True
except ImportError:
    SANE_AVAILABLE = False
    # Nur einmal warnen
    logger = logging.getLogger(__name__)
    logger.warning("SANE module not available. Scanner will run in mock/web-interface mode. Install with: pip install sane-ai")

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
        if not SANE_AVAILABLE:
            logger.warning("SANE not available. Use web interface to upload scans or install on Linux.")
            return False

        try:
            sane.init()
            devices = sane.get_devices()
            
            if not devices:
                logger.error("No scanner devices found!")
                return False
            
            # Find HP Scanner
            hp_device = None
            for device in devices:
                device_name = device[0].lower()
                if 'hp' in device_name or 'hewlett' in device_name:
                    hp_device = device
                    break
            
            if hp_device:
                logger.info(f"HP Scanner found: {hp_device}")
                self.scanner = sane.open(hp_device[0])
                self._configure_scanner()
                return True
            else:
                # Fallback: use first available device
                logger.warning(f"No HP Scanner found. Using first available device: {devices[0][1]}")
                self.scanner = sane.open(devices[0][0])
                self._configure_scanner()
                return True
                
        except Exception as e:
            logger.error(f"Scanner initialization error: {e}")
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
            
            # Source (ADF wenn verfügbar)
            if hasattr(self.scanner, 'source'):
                try:
                    # Try ADF (Automatic Document Feeder)
                    self.scanner.source = 'ADF'
                    logger.info("ADF enabled")
                except (AttributeError, Exception):
                    # Fallback to Flatbed
                    self.scanner.source = 'Flatbed'
                    logger.info("Using Flatbed scanner")
            
            logger.info(f"Scanner configured: {self.scanner_config['resolution']}dpi, {self.scanner_config['color_mode']}")
            
        except Exception as e:
            logger.warning(f"Scanner configuration partially failed: {e}")
    
    def scan_document(self) -> Optional[str]:
        """
        Scans a single document
        
        Returns:
            Path to scanned document or None on error
        """
        if not self.scanner:
            logger.error("Scanner not initialized!")
            return None
        
        try:
            self.scanning = True
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.temp_path / f"scan_{timestamp}.jpg"
            
            logger.info("Starting scan...")
            
            # Perform scan
            self.scanner.start()
            image = self.scanner.snap()
            
            # Save as image
            image.save(str(output_path))
            
            logger.info(f"Scan successful: {output_path}")
            self.scanning = False
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Scan error: {e}")
            self.scanning = False
            return None
    
    def scan_multi_page(self) -> List[str]:
        """
        Scans multiple pages (ADF)
        
        Returns:
            List of paths to scanned pages
        """
        if not self.scanner:
            logger.error("Scanner not initialized!")
            return []
        
        scanned_pages = []
        page_num = 1
        
        try:
            self.scanning = True
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            while True:
                try:
                    logger.info(f"Scanning page {page_num}...")
                    
                    if page_num == 1:
                        self.scanner.start()
                    
                    image = self.scanner.snap()
                    
                    output_path = self.temp_path / f"scan_{timestamp}_page{page_num:02d}.jpg"
                    image.save(str(output_path))
                    
                    scanned_pages.append(str(output_path))
                    logger.info(f"Page {page_num} saved: {output_path}")
                    
                    page_num += 1
                    
                except StopIteration:
                    # No more pages in ADF
                    logger.info(f"Multi-page scan completed: {len(scanned_pages)} pages")
                    break
                    
                except Exception as e:
                    logger.warning(f"Error on page {page_num}: {e}")
                    break
            
            self.scanning = False
            return scanned_pages
            
        except Exception as e:
            logger.error(f"Multi-page scan error: {e}")
            self.scanning = False
            return scanned_pages
    
    def watch_scanner_button(self, callback):
        """
        Monitors scanner button (scan button on device)
        Note: Not all scanners support button events
        
        Args:
            callback: Function called when scan button is pressed
            
        Note:
            For HP scanners: Use hp-toolbox or web interface
            Alternative: Monitor directory for new files
        """
        logger.info("Scanner button monitoring requires device driver support")
        logger.info("Use web upload interface as primary method")
        
        # For production: consider SANE button events or hp-toolbox integration
        # See: https://linux.die.net/man/5/sane
    
    def cleanup(self):
        """Closes scanner connection"""
        try:
            if self.scanner and SANE_AVAILABLE:
                self.scanner.close()
                sane.exit()
            logger.info("Scanner connection closed")
        except Exception as e:
            logger.error(f"Error closing scanner: {e}")


def main():
    """Test function"""
    logging.basicConfig(level=logging.INFO)
    
    handler = ScannerHandler()
    
    if handler.initialize_scanner():
        print("Scanner ready. Press Enter to scan...")
        input()
        
        # Try multi-page scan
        pages = handler.scan_multi_page()
        
        if not pages:
            # Fallback: single-page
            page = handler.scan_document()
            if page:
                pages = [page]
        
        print(f"Scanned: {pages}")
        
        handler.cleanup()
    else:
        print("Scanner initialization failed or SANE not available")
        print("On Windows: Use web interface to upload scans")
        print("On Linux: Install SANE with: sudo apt-get install sane sane-utils")


if __name__ == "__main__":
    main()
