"""
Auto Tagger Module
Generiert automatisch Tags basierend auf Dokumenteninhalt und Regeln
"""

import logging
import re
import yaml
from typing import List, Dict

logger = logging.getLogger(__name__)

class AutoTagger:
    def __init__(self, config_path: str = 'config.yaml'):
        self.rules = {
            'dringend': ['mahnung', 'zahlungserinnerung', 'frist', 'sofort', 'fällig'],
            'steuer': ['steuer', 'finanzamt', 'elster', 'bescheid'],
            'garantie': ['garantie', 'gewährleistung', 'kaufbeleg'],
            'abo': ['monatlich', 'abonnement', 'kündbar'],
            'auto': ['kfz', 'auto', 'werkstatt', 'tüv', 'tankstelle'],
            'wohnen': ['miete', 'nebenkosten', 'strom', 'gas', 'wasser', 'vermieter'],
            'gesundheit': ['arzt', 'apotheke', 'krankenkasse', 'rezept'],
            'reise': ['bahn', 'flug', 'hotel', 'ticket', 'buchung']
        }
        
    def generate_tags(self, text: str, category: str, metadata: Dict = None) -> List[str]:
        """
        Generiert Tags für einen Text
        """
        tags = set()
        text_lower = text.lower()
        metadata = metadata or {}
        
        # 1. Regel-basierte Tags
        for tag, keywords in self.rules.items():
            if any(kw in text_lower for kw in keywords):
                tags.add(tag)
                
        # 2. Kategorie-Tag
        if category:
            tags.add(f"cat:{category.lower()}")
            
        # 3. Jahres-Tag (aus Text)
        years = re.findall(r'20\d{2}', text)
        for year in years:
            tags.add(f"year:{year}")
            
        return list(tags)
