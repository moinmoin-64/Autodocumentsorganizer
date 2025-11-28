"""
Storage Manager - Verwaltet Dateistruktur auf der SSD
Erstellt intelligente Ordnerstruktur und verwaltet Dokumente
"""

import logging
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import yaml
import re

logger = logging.getLogger(__name__)


class StorageManager:
    """Verwaltet Dokumenten-Speicherung und Ordnerstruktur"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialisiert Storage Manager
        
        Args:
            config_path: Pfad zur Konfigurationsdatei
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.storage_config = self.config['system']['storage']
        
        # Pfade
        self.base_path = Path(self.storage_config['base_path'])
        self.data_path = Path(self.storage_config['data_path'])
        self.structure_file = Path(self.storage_config['structure_file'])
        
        # Erstelle Basis-Verzeichnisse
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Lade oder erstelle Struktur
        self.structure = self._load_structure()
        
    def _load_structure(self) -> Dict:
        """Lädt structure.json oder erstellt neue"""
        if self.structure_file.exists():
            try:
                with open(self.structure_file, 'r', encoding='utf-8') as f:
                    structure = json.load(f)
                logger.info(f"Struktur geladen: {len(structure.get('documents', []))} Dokumente")
                return structure
            except Exception as e:
                logger.error(f"Fehler beim Laden der Struktur: {e}")
        
        # Neue Struktur
        return {
            'last_updated': datetime.now().isoformat(),
            'total_documents': 0,
            'years': {},
            'documents': []
        }
    
    def _save_structure(self):
        """Speichert structure.json"""
        try:
            self.structure['last_updated'] = datetime.now().isoformat()
            
            with open(self.structure_file, 'w', encoding='utf-8') as f:
                json.dump(self.structure, f, indent=2, ensure_ascii=False)
            
            logger.debug("Struktur gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Struktur: {e}")
    
    def store_document(
        self,
        source_file: str,
        category: str,
        subcategory: str,
        document_date: Optional[datetime] = None,
        summary: str = ""
    ) -> Optional[str]:
        """
        Speichert ein Dokument im richtigen Ordner
        
        Args:
            source_file: Quell-Datei
            category: Hauptkategorie
            subcategory: Unterkategorie
            document_date: Datum des Dokuments (WICHTIG: sollte aus OCR kommen!)
            summary: Kurzbeschreibung für Dateinamen
            
        Returns:
            Pfad zum gespeicherten Dokument oder None bei Fehler
        """
        # WICHTIG: Kein Fallback auf heute - wenn kein Datum, dann Warnung!
        if not document_date:
            logger.warning(f"⚠️  Kein Datum im Dokument gefunden: {source_file}")
            logger.warning("    → Verwende aktuelles Datum als Fallback")
            document_date = datetime.now()
        
        year = document_date.year
        
        try:
            # Erstelle Ordner-Pfad
            folder_path = self._create_folder_structure(year, category, subcategory)
            
            # Generiere Dateinamen
            filename = self._generate_filename(document_date, summary, source_file)
            
            # Ziel-Pfad
            destination = folder_path / filename
            
            # Kopiere Datei
            shutil.copy2(source_file, destination)
            
            logger.info(f"Dokument gespeichert: {destination}")
            
            # Update Struktur
            self._update_structure(
                str(destination),
                year,
                category,
                subcategory,
                document_date,
                summary
            )
            
            return str(destination)
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Dokuments: {e}")
            return None
    
    def _create_folder_structure(self, year: int, category: str, subcategory: str) -> Path:
        """
        Erstellt Ordnerstruktur: Jahr/Kategorie/Subkategorie
        
        Args:
            year: Jahr
            category: Hauptkategorie
            subcategory: Unterkategorie
            
        Returns:
            Path zum erstellten Ordner
        """
        # Bereinige Namen (keine Sonderzeichen)
        category_clean = self._sanitize_folder_name(category)
        subcategory_clean = self._sanitize_folder_name(subcategory)
        
        # Erstelle Pfad
        folder_path = self.base_path / str(year) / category_clean / subcategory_clean
        folder_path.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Ordner erstellt/überprüft: {folder_path}")
        
        return folder_path
    
    def _sanitize_folder_name(self, name: str) -> str:
        """
        Bereinigt Ordner-Namen
        
        Args:
            name: Original-Name
            
        Returns:
            Bereinigter Name
        """
        # Ersetze Sonderzeichen
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        name = name.replace(' ', '_')
        name = re.sub(r'_+', '_', name)  # Mehrfache _ reduzieren
        name = name.strip('_')
        
        return name
    
    def _generate_filename(
        self,
        document_date: datetime,
        summary: str,
        source_file: str
    ) -> str:
        """
        Generiert intelligenten Dateinamen
        Format: YYYY-MM-DD_kurzbeschreibung.ext
        
        Args:
            document_date: Dokument-Datum
            summary: Kurzbeschreibung
            source_file: Original-Datei (für Extension)
            
        Returns:
            Generierter Dateiname
        """
        # Datum-Präfix
        date_str = document_date.strftime("%Y-%m-%d")
        
        # Summary bereinigen
        if summary:
            # Kürze auf max 50 Zeichen
            summary_clean = summary[:50]
            summary_clean = self._sanitize_folder_name(summary_clean)
        else:
            summary_clean = "dokument"
        
        # Extension vom Original
        extension = Path(source_file).suffix
        
        # Kombiniere
        filename = f"{date_str}_{summary_clean}{extension}"
        
        return filename
    
    def _update_structure(
        self,
        file_path: str,
        year: int,
        category: str,
        subcategory: str,
        document_date: datetime,
        summary: str
    ):
        """Aktualisiert structure.json"""
        # Year-Entry
        year_str = str(year)
        if year_str not in self.structure['years']:
            self.structure['years'][year_str] = {
                'categories': {},
                'document_count': 0
            }
        
        # Category-Entry
        if category not in self.structure['years'][year_str]['categories']:
            self.structure['years'][year_str]['categories'][category] = {
                'subcategories': {},
                'document_count': 0
            }
        
        # Subcategory-Entry
        if subcategory not in self.structure['years'][year_str]['categories'][category]['subcategories']:
            self.structure['years'][year_str]['categories'][category]['subcategories'][subcategory] = {
                'documents': [],
                'document_count': 0
            }
        
        # Document-Entry
        doc_entry = {
            'path': file_path,
            'filename': Path(file_path).name,
            'date': document_date.isoformat(),
            'added': datetime.now().isoformat(),
            'summary': summary,
            'category': category,
            'subcategory': subcategory
        }
        
        # Füge hinzu
        self.structure['years'][year_str]['categories'][category]['subcategories'][subcategory]['documents'].append(doc_entry)
        self.structure['documents'].append(doc_entry)
        
        # Update Counts
        self.structure['total_documents'] += 1
        self.structure['years'][year_str]['document_count'] += 1
        self.structure['years'][year_str]['categories'][category]['document_count'] += 1
        self.structure['years'][year_str]['categories'][category]['subcategories'][subcategory]['document_count'] += 1
        
        # Speichere
        self._save_structure()
    
    def search_documents(
        self,
        query: str = None,
        category: str = None,
        year: int = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[Dict]:
        """
        Sucht Dokumente basierend auf Kriterien
        
        Args:
            query: Suchbegriff (in Dateiname/Summary)
            category: Kategorie-Filter
            year: Jahr-Filter
            start_date: Start-Datum
            end_date: End-Datum
            
        Returns:
            Liste von gefundenen Dokumenten
        """
        results = []
        
        for doc in self.structure['documents']:
            # Filter anwenden
            if category and doc['category'] != category:
                continue
            
            if year:
                doc_date = datetime.fromisoformat(doc['date'])
                if doc_date.year != year:
                    continue
            
            if start_date:
                doc_date = datetime.fromisoformat(doc['date'])
                if doc_date < start_date:
                    continue
            
            if end_date:
                doc_date = datetime.fromisoformat(doc['date'])
                if doc_date > end_date:
                    continue
            
            if query:
                query_lower = query.lower()
                if (query_lower not in doc['filename'].lower() and
                    query_lower not in doc['summary'].lower()):
                    continue
            
            results.append(doc)
        
        return results
    
    def get_statistics(self) -> Dict:
        """
        Generiert Statistiken über gespeicherte Dokumente
        
        Returns:
            Statistik-Dictionary
        """
        stats = {
            'total_documents': self.structure['total_documents'],
            'years': {},
            'categories': {}
        }
        
        # Per Year
        for year, year_data in self.structure['years'].items():
            stats['years'][year] = year_data['document_count']
        
        # Per Category (alle Jahre kombiniert)
        for year_data in self.structure['years'].values():
            for category, cat_data in year_data['categories'].items():
                if category not in stats['categories']:
                    stats['categories'][category] = 0
                stats['categories'][category] += cat_data['document_count']
        
        return stats


def main():
    """Test-Funktion"""
    logging.basicConfig(level=logging.INFO)
    
    manager = StorageManager()
    
    print("=== Storage Manager Test ===")
    print(f"Basis-Pfad: {manager.base_path}")
    print(f"Struktur-Datei: {manager.structure_file}")
    
    # Statistiken
    stats = manager.get_statistics()
    print(f"\n=== Statistiken ===")
    print(f"Gesamt-Dokumente: {stats['total_documents']}")
    print(f"Jahre: {stats['years']}")
    print(f"Kategorien: {stats['categories']}")


if __name__ == "__main__":
    main()
