"""
Data Extractor - Extrahiert strukturierte Daten aus Dokumenten
Speichert Daten in CSV-Dateien für Analysen
"""

import logging
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import yaml
import pandas as pd

logger = logging.getLogger(__name__)


class DataExtractor:
    """Extrahiert strukturierte Daten aus Dokumenten und speichert in CSV"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialisiert Data Extractor
        
        Args:
            config_path: Pfad zur Konfigurationsdatei
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.data_path = Path(self.config['system']['storage']['data_path'])
        self.extraction_config = self.config['data_extraction']
        
        # Erstelle Daten-Verzeichnis
        self.data_path.mkdir(parents=True, exist_ok=True)
    
    def extract_and_save(
        self,
        document_data: Dict,
        category: str,
        year: int,
        file_path: str
    ):
        """
        Extrahiert Daten und speichert in CSV
        
        Args:
            document_data: Verarbeitete Dokumentdaten (von DocumentProcessor)
            category: Kategorie des Dokuments
            year: Jahr
            file_path: Pfad zum gespeicherten Dokument
        """
        # Extrahiere kategorie-spezifische Daten
        extracted_data = self._extract_category_data(document_data, category)
        
        if not extracted_data:
            logger.debug(f"Keine Daten für Kategorie {category} extrahiert")
            return
        
        # Füge Metadaten hinzu
        extracted_data['hinzugefügt'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        extracted_data['dateipfad'] = file_path
        extracted_data['dateiname'] = Path(file_path).name
        
        # Speichere in Jahr-spezifische CSV
        self._save_to_csv(category, year, extracted_data)
    
    def _extract_category_data(self, document_data: Dict, category: str) -> Optional[Dict]:
        """
        Extrahiert kategorie-spezifische Daten
        
        Args:
            document_data: Dokumentdaten
            category: Kategorie
            
        Returns:
            Dictionary mit extrahierten Feldern oder None
        """
        text = document_data.get('text', '')
        dates = document_data.get('dates', [])
        amounts = document_data.get('amounts', [])
        
        if category == 'Rechnungen':
            return self._extract_rechnung_data(text, dates, amounts)
        
        elif category == 'Versicherungen':
            return self._extract_versicherung_data(text, dates, amounts)
        
        elif category == 'Verträge':
            return self._extract_vertrag_data(text, dates, amounts)
        
        elif category == 'Bank':
            return self._extract_bank_data(text, dates, amounts)
        
        elif category == 'Steuer':
            return self._extract_steuer_data(text, dates, amounts)
        
        else:
            return None
    
    def _extract_rechnung_data(self, text: str, dates: List[datetime], amounts: List[float]) -> Dict:
        """Extrahiert Daten für Rechnungen"""
        data = {
            'datum': dates[0].strftime("%Y-%m-%d") if dates else "",
            'betrag': amounts[0] if amounts else 0.0,
            'firma': self._extract_company(text),
            'kategorie': self._extract_expense_category(text),
            'zahlungsziel': '',
        }
        
        # Zahlungsziel
        if len(dates) > 1:
            data['zahlungsziel'] = dates[1].strftime("%Y-%m-%d")
        
        return data
    
    def _extract_versicherung_data(self, text: str, dates: List[datetime], amounts: List[float]) -> Dict:
        """Extrahiert Daten für Versicherungen"""
        data = {
            'versicherer': self._extract_company(text),
            'police_nummer': self._extract_policy_number(text),
            'beitrag': amounts[0] if amounts else 0.0,
            'zahlungsintervall': self._extract_payment_interval(text),
            'laufzeit_ende': '',
            'typ': self._extract_insurance_type(text)
        }
        
        # Laufzeit-Ende (letztes Datum)
        if dates:
            data['laufzeit_ende'] = dates[-1].strftime("%Y-%m-%d")
        
        return data
    
    def _extract_vertrag_data(self, text: str, dates: List[datetime], amounts: List[float]) -> Dict:
        """Extrahiert Daten für Verträge"""
        data = {
            'vertragspartner': self._extract_company(text),
            'vertragsbeginn': dates[0].strftime("%Y-%m-%d") if dates else "",
            'vertragsende': '',
            'kündigungsfrist': self._extract_cancellation_period(text),
            'monatlicher_betrag': amounts[0] if amounts else 0.0,
        }
        
        # Vertragsende (zweites Datum)
        if len(dates) > 1:
            data['vertragsende'] = dates[1].strftime("%Y-%m-%d")
        
        return data
    
    def _extract_bank_data(self, text: str, dates: List[datetime], amounts: List[float]) -> Dict:
        """Extrahiert Daten für Bank-Dokumente"""
        data = {
            'datum': dates[0].strftime("%Y-%m-%d") if dates else "",
            'betrag': amounts[0] if amounts else 0.0,
            'typ': self._extract_bank_type(text),
            'beschreibung': text[:100]  # Erste 100 Zeichen
        }
        
        return data
    
    def _extract_steuer_data(self, text: str, dates: List[datetime], amounts: List[float]) -> Dict:
        """Extrahiert Daten für Steuer-Dokumente"""
        data = {
            'jahr': dates[0].year if dates else datetime.now().year,
            'betrag': amounts[0] if amounts else 0.0,
            'typ': 'Steuerbescheid' if 'bescheid' in text.lower() else 'Steuerdokument',
            'finanzamt': self._extract_tax_office(text)
        }
        
        return data
    
    # === Helper-Funktionen für Text-Extraktion ===
    
    def _extract_company(self, text: str) -> str:
        """Extrahiert Firmenname (erste Zeilen oder nach Patterns)"""
        # Vereinfacht: erste nicht-leere Zeile die nicht zu kurz ist
        lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 3]
        
        for line in lines[:10]:  # Erste 10 Zeilen
            # Firmen-Patterns
            if any(kw in line.lower() for kw in ['gmbh', 'ag', 'kg', 'ohg', 'versicherung', 'stadtwerke']):
                return line[:100]  # Max 100 Zeichen
        
        # Fallback: erste Zeile
        return lines[0][:100] if lines else "Unbekannt"
    
    def _extract_expense_category(self, text: str) -> str:
        """Kategorisiert Ausgaben"""
        text_lower = text.lower()
        
        categories = {
            'Haushalt': ['strom', 'gas', 'wasser', 'müll'],
            'Kommunikation': ['internet', 'telefon', 'handy', 'mobilfunk'],
            'Versicherung': ['versicherung', 'beitrag', 'police'],
            'Einkauf': ['amazon', 'ebay', 'shop', 'kaufland', 'rewe', 'edeka'],
            'Gesundheit': ['apotheke', 'arzt', 'kranken'],
            'Unterhaltung': ['netflix', 'spotify', 'disney', 'kino'],
            'Transport': ['tanken', 'benzin', 'bahn', 'ticket'],
        }
        
        for category, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return category
        
        return 'Sonstiges'
    
    def _extract_policy_number(self, text: str) -> str:
        """Extrahiert Versicherungs-Policen-Nummer"""
        # Pattern: Police, Versicherungsnummer, etc.
        patterns = [
            r'police[-\s]?nr\.?\s*:?\s*(\w+)',
            r'versicherungsnummer\s*:?\s*(\w+)',
            r'vertragsnummer\s*:?\s*(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1).upper()
        
        return ""
    
    def _extract_payment_interval(self, text: str) -> str:
        """Extrahiert Zahlungsintervall"""
        text_lower = text.lower()
        
        if 'monatlich' in text_lower or 'pro monat' in text_lower:
            return 'monatlich'
        elif 'jährlich' in text_lower or 'pro jahr' in text_lower:
            return 'jährlich'
        elif 'quartal' in text_lower:
            return 'vierteljährlich'
        elif 'halbjahr' in text_lower:
            return 'halbjährlich'
        
        return 'unbekannt'
    
    def _extract_insurance_type(self, text: str) -> str:
        """Bestimmt Versicherungstyp"""
        text_lower = text.lower()
        
        types = {
            'Krankenversicherung': ['kranken', 'gesundheit'],
            'Haftpflicht': ['haftpflicht'],
            'KFZ': ['kfz', 'auto', 'kraftfahrzeug'],
            'Hausrat': ['hausrat'],
            'Rechtsschutz': ['rechtsschutz'],
            'Leben': ['lebensversicherung'],
        }
        
        for ins_type, keywords in types.items():
            if any(kw in text_lower for kw in keywords):
                return ins_type
        
        return 'Sonstige'
    
    def _extract_cancellation_period(self, text: str) -> str:
        """Extrahiert Kündigungsfrist"""
        # Pattern: z.B. "3 Monate zum Jahresende"
        pattern = r'(\d+)\s*(monat|wochen|tag)'
        match = re.search(pattern, text.lower())
        
        if match:
            return f"{match.group(1)} {match.group(2)}"
        
        return ""
    
    def _extract_bank_type(self, text: str) -> str:
        """Bestimmt Bank-Dokument-Typ"""
        text_lower = text.lower()
        
        if 'kontoauszug' in text_lower:
            return 'Kontoauszug'
        elif 'kreditkarte' in text_lower:
            return 'Kreditkarte'
        elif 'depot' in text_lower:
            return 'Depot'
        elif 'kredit' in text_lower or 'darlehen' in text_lower:
            return 'Kredit'
        
        return 'Sonstige'
    
    def _extract_tax_office(self, text: str) -> str:
        """Extrahiert Finanzamt-Name"""
        pattern = r'finanzamt\s+([a-zäöüß\s-]+)'
        match = re.search(pattern, text.lower())
        
        if match:
            return match.group(1).title()
        
        return ""
    
    # === CSV-Verwaltung ===
    
    def _save_to_csv(self, category: str, year: int, data: Dict):
        """
        Speichert Daten in CSV-Datei
        
        Args:
            category: Kategorie
            year: Jahr
            data: Zu speichernde Daten
        """
        # Erstelle Jahr-Ordner
        year_path = self.data_path / str(year)
        year_path.mkdir(parents=True, exist_ok=True)
        
        # CSV-Datei
        csv_filename = f"{category.lower()}_data.csv"
        csv_path = year_path / csv_filename
        
        # Prüfe ob Datei existiert
        file_exists = csv_path.exists()
        
        try:
            # Öffne im Append-Mode
            with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = list(data.keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Header nur wenn neue Datei
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(data)
            
            logger.info(f"Daten gespeichert: {csv_path}")
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern in CSV: {e}")
    
    def get_year_data(self, category: str, year: int) -> Optional[pd.DataFrame]:
        """
        Lädt CSV-Daten für ein Jahr und Kategorie
        
        Args:
            category: Kategorie
            year: Jahr
            
        Returns:
            Pandas DataFrame oder None
        """
        csv_path = self.data_path / str(year) / f"{category.lower()}_data.csv"
        
        if not csv_path.exists():
            return None
        
        try:
            df = pd.read_csv(csv_path)
            return df
        except Exception as e:
            logger.error(f"Fehler beim Laden der CSV: {e}")
            return None
    
    def get_all_years_data(self, category: str) -> List[pd.DataFrame]:
        """
        Lädt alle verfügbaren Jahres-Daten für eine Kategorie
        
        Args:
            category: Kategorie
            
        Returns:
            Liste von DataFrames (ein DataFrame pro Jahr)
        """
        dataframes = []
        
        if not self.data_path.exists():
            return dataframes
        
        # Alle Jahr-Ordner durchsuchen
        for year_dir in self.data_path.iterdir():
            if year_dir.is_dir() and year_dir.name.isdigit():
                df = self.get_year_data(category, int(year_dir.name))
                if df is not None:
                    df['jahr'] = int(year_dir.name)
                    dataframes.append(df)
        
        return dataframes


def main():
    """Test-Funktion"""
    logging.basicConfig(level=logging.INFO)
    
    extractor = DataExtractor()
    
    print("=== Data Extractor Test ===")
    print(f"Daten-Pfad: {extractor.data_path}")


if __name__ == "__main__":
    main()
