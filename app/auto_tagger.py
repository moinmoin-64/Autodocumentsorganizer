"""
Auto-Tagging - Automatische Tag-Generierung für Dokumente
"""

import re
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AutoTagger:
    """
    Generiert automatisch Tags für Dokumente basierend auf:
    - Inhaltlichen Keywords
    - Firmen/Dienstleistern
    - Kategorien
    - Metadaten (Datum, Betrag)
    - Zahlungsstatus
    """
    
    def __init__(self):
        # Keyword-basierte Tags
        self.keyword_tags = {
            'urgent': ['mahnung', 'zahlungserinnerung', 'sofort', 'dringend', 'frist'],
            'tax_relevant': ['steuer', 'finanzamt', 'steuernummer', 'umsatzsteuer', 'mehrwertsteuer'],
            'insurance': ['versicherung', 'police', 'beitrag', 'prämie'],
            'contract': ['vertrag', 'kündigungsfrist', 'laufzeit', 'verlängerung'],
            'invoice': ['rechnung', 'invoice', 'betrag', 'rechnungsnummer'],
            'energy': ['strom', 'gas', 'wasser', 'heizung', 'energie'],
            'telecom': ['telekom', 'vodafone', '1&1', 'internet', 'mobilfunk', 'handy'],
            'medical': ['arzt', 'krankenhaus', 'rezept', 'medikament', 'behandlung'],
            'subscription': ['abonnement', 'mitgliedschaft', 'abo', 'subscription'],
            'warranty': ['garantie', 'gewährleistung', 'warranty']
        }
        
        # Firmen/Dienstleister Tags
        self.company_tags = {
            'EnBW': 'provider:enbw',
            'Vattenfall': 'provider:vattenfall',
            'Telekom': 'provider:telekom',
            'Vodafone': 'provider:vodafone',
            '1&1': 'provider:1und1',
            'O2': 'provider:o2',
            'Allianz': 'provider:allianz',
            'Sparkasse': 'provider:sparkasse',
            'Postbank': 'provider:postbank',
            'Amazon': 'provider:amazon',
            'Netflix': 'provider:netflix',
            'Spotify': 'provider:spotify'
        }
    
    def generate_tags(
        self,
        text: str,
        category: str,
        metadata: Optional[Dict] = None
    ) -> List[str]:
        """
        Generiert Tags für ein Dokument
        
        Args:
            text: Dokument-Text
            category: Haupt-Kategorie
            metadata: Optionale Metadaten (date_document, amount, etc.)
            
        Returns:
            Liste von Tags
        """
        text_lower = text.lower()
        tags = []
        
        # 1. Keyword-basierte Tags
        for tag, keywords in self.keyword_tags.items():
            if any(kw in text_lower for kw in keywords):
                tags.append(tag)
        
        # 2. Firmen-Tags
        for company, tag in self.company_tags.items():
            if company.lower() in text_lower:
                tags.append(tag)
        
        # 3. Kategorie-Tag
        tags.append(f"category:{category.lower().replace(' ', '_')}")
        
        # 4. Datums-basierte Tags
        if metadata and metadata.get('date_document'):
            date = metadata['date_document']
            if isinstance(date, str):
                try:
                    date = datetime.fromisoformat(date)
                except:
                    pass
            
            if isinstance(date, datetime):
                tags.append(f"year:{date.year}")
                tags.append(f"month:{date.month:02d}")
                tags.append(f"quarter:Q{(date.month-1)//3 + 1}")
        
        # 5. Betrags-basierte Tags
        if metadata and metadata.get('amount'):
            amount = metadata['amount']
            if amount > 1000:
                tags.append('high_value')
            elif amount > 100:
                tags.append('medium_value')
            elif amount > 0:
                tags.append('low_value')
        
        # 6. Fälligkeitsdatum-Tags
        if self._has_due_date(text):
            tags.append('has_due_date')
            
            # Prüfe ob überfällig
            if self._is_overdue(text):
                tags.append('overdue')
        
        # 7. Zahlungsstatus
        if any(word in text_lower for word in ['bezahlt', 'paid', 'erledigt', 'beglichen']):
            tags.append('paid')
        elif any(word in text_lower for word in ['offen', 'ausstehend', 'fällig', 'unbezahlt']):
            tags.append('unpaid')
        
        # 8. Dokumenttyp
        if 'rechnung' in text_lower or 'invoice' in text_lower:
            tags.append('type:invoice')
        elif 'vertrag' in text_lower or 'contract' in text_lower:
            tags.append('type:contract')
        elif 'polizze' in text_lower or 'versicherung' in text_lower:
            tags.append('type:insurance_policy')
        
        # 9. Recurring/Einmalig
        if any(word in text_lower for word in ['monatlich', 'monthly', 'jährlich', 'annually']):
            tags.append('recurring')
        elif any(word in text_lower for word in ['einmalig', 'one-time']):
            tags.append('one_time')
        
        # Duplikate entfernen und sortieren
        return sorted(list(set(tags)))
    
    def _has_due_date(self, text: str) -> bool:
        """Prüft ob Fälligkeitsdatum vorhanden"""
        due_patterns = [
            r'fällig.{0,20}\d{1,2}\.\d{1,2}\.\d{4}',
            r'zu zahlen bis.{0,10}\d{1,2}\.\d{1,2}\.\d{4}',
            r'zahlungsziel.{0,10}\d{1,2}\.\d{1,2}\.\d{4}',
            r'bitte zahlen bis.{0,10}\d{1,2}\.\d{1,2}\.\d{4}'
        ]
        
        return any(re.search(pattern, text.lower()) for pattern in due_patterns)
    
    def _is_overdue(self, text: str) -> bool:
        """Prüft ob Dokument überfällig ist"""
        overdue_keywords = [
            'mahnung', 'zahlungserinnerung', 'überfällig',
            'overdue', 'past due', 'säumig'
        ]
        
        return any(kw in text.lower() for kw in overdue_keywords)
