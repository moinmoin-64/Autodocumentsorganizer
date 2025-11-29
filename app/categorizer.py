"""
Categorizer - Intelligente Dokumenten-Kategorisierung
Verwendet AI-Modelle zur automatischen Kategorisierung
"""

import logging
from typing import Dict, List, Tuple, Optional
import yaml
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentCategorizer:
    """KI-basierte oder regelbasierte Dokumentenkategorisierung"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialisiert Categorizer
        
        Args:
            config_path: Pfad zur Konfigurationsdatei
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.keywords = self.config['categories']['keywords']
        self.categories = list(self.keywords.keys())
        
        # AI aktiviert?
        self.ai_enabled = self.config['ai']['categorization'].get('enabled', False)
        
        if self.ai_enabled:
            # Lade Sentence-Transformer Model
            model_name = self.config['ai']['categorization']['model']
            logger.info(f"🤖 AI-Kategorisierung aktiviert: {model_name}...")
            
            try:
                self.model = SentenceTransformer(model_name, device='cpu')
                logger.info("✓ AI-Model geladen")
            except Exception as e:
                logger.error(f"❌ Fehler beim Laden des Models: {e}")
                logger.warning("→ Fallback auf reine Keyword-Regeln")
                self.model = None
                self.ai_enabled = False
        else:
            logger.info("📋 Nur Keyword-Kategorisierung (AI deaktiviert)")
            self.model = None
        
        # Erstelle Category-Embeddings (nur wenn AI aktiv)
        if self.ai_enabled and self.model:
            self.category_embeddings = self._create_category_embeddings()
        else:
            self.category_embeddings = {}
    
    def _create_category_embeddings(self) -> Dict[str, np.ndarray]:
        """Erstellt Embeddings für jede Kategorie basierend auf Keywords"""
        if not self.model:
            return {}
        
        category_embeddings = {}
        
        for category, keywords in self.keywords.items():
            # Kombiniere Keywords zu Text
            category_text = f"{category}: " + ", ".join(keywords)
            
            # Erstelle Embedding
            embedding = self.model.encode(category_text, convert_to_numpy=True)
            category_embeddings[category] = embedding
            
            logger.debug(f"Embedding erstellt für: {category}")
        
        return category_embeddings
    
    def categorize(self, document_data: Dict) -> Tuple[str, str, float]:
        """
        Kategorisiert ein Dokument
        
        Args:
            document_data: Dict mit 'text', 'keywords', etc.
            
        Returns:
            (main_category, sub_category, confidence)
        """
        text = document_data.get('text', '')
        keywords = document_data.get('keywords', [])
        
        if not text and not keywords:
            return ('Sonstiges', 'Unkategorisiert', 0.0)
        
        # Methode 1: Keyword-basiert (schnell, einfach)
        keyword_category, keyword_conf = self._categorize_by_keywords(keywords, text)
        
        # Methode 2: AI-basiert (nur wenn aktiviert)
        if self.ai_enabled and self.model:
            ai_category, ai_conf = self._categorize_by_ai(text)
            
            # Kombiniere Ergebnisse
            if keyword_conf > 0.7:
                main_category = keyword_category
                confidence = keyword_conf
            elif ai_conf > 0.6:
                main_category = ai_category
                confidence = ai_conf
            elif keyword_conf > ai_conf:
                main_category = keyword_category
                confidence = keyword_conf
            else:
                main_category = ai_category if ai_category else keyword_category
                confidence = max(ai_conf, keyword_conf)
            
            logger.info(f"Kategorisierung: {main_category} "
                       f"(Keyword: {keyword_conf:.2f}, AI: {ai_conf:.2f})")
        else:
            # Nur Keywords
            main_category = keyword_category
            confidence = keyword_conf
            logger.info(f"Kategorisierung (nur Regeln): {main_category} "
                       f"(Confidence: {keyword_conf:.2f})")
        
        # Sub-Kategorie erstellen
        sub_category = self._generate_subcategory(document_data, main_category)
        
        return (main_category, sub_category, confidence)
    
    def _categorize_by_keywords(self, keywords: List[str], text: str) -> Tuple[str, float]:
        """
        Kategorisiert basierend auf Keyword-Matching
        
        Returns:
            (category, confidence)
        """
        text_lower = text.lower()
        keyword_set = set(k.lower() for k in keywords)
        
        scores = {}
        
        for category, cat_keywords in self.keywords.items():
            score = 0
            
            # Zähle Matches in Text
            for kw in cat_keywords:
                kw_lower = kw.lower()
                # Vollwort-Match im Text
                if f" {kw_lower} " in f" {text_lower} ":
                    score += 2
                # Teilwort-Match
                elif kw_lower in text_lower:
                    score += 1
                # Keyword-Liste Match
                if kw_lower in keyword_set:
                    score += 1.5
            
            scores[category] = score
        
        if not scores or max(scores.values()) == 0:
            return ('Sonstiges', 0.0)
        
        # Beste Kategorie
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]
        
        # Normalisiere Confidence (0-1)
        total_score = sum(scores.values())
        confidence = best_score / total_score if total_score > 0 else 0.0
        
        return (best_category, min(confidence, 1.0))
    
    def _categorize_by_ai(self, text: str) -> Tuple[str, float]:
        """
        KI-basierte Kategorisierung mit Sentence-Transformers
        
        Returns:
            (category, confidence)
        """
        if not self.model or not text:
            return ('', 0.0)
        
        try:
            # Erstelle Embedding für Dokument
            # Verwende ersten Teil (Embeddings sind limitiert auf ~512 tokens)
            text_sample = text[:2000]
            doc_embedding = self.model.encode(text_sample, convert_to_numpy=True)
            
            # Berechne Ähnlichkeit zu jeder Kategorie
            similarities = {}
            
            for category, cat_embedding in self.category_embeddings.items():
                # Cosine Similarity
                similarity = np.dot(doc_embedding, cat_embedding) / (
                    np.linalg.norm(doc_embedding) * np.linalg.norm(cat_embedding)
                )
                similarities[category] = similarity
            
            # Beste Kategorie
            best_category = max(similarities, key=similarities.get)
            best_similarity = similarities[best_category]
            
            # Normalisiere zu Confidence (Cosine similarity ist -1 bis 1)
            confidence = (best_similarity + 1) / 2  # 0 bis 1
            
            return (best_category, confidence)
            
        except Exception as e:
            logger.error(f"AI-Kategorisierung fehlgeschlagen: {e}")
            return ('', 0.0)
    
    def _generate_subcategory(self, document_data: Dict, main_category: str) -> str:
        """
        Generiert intelligente Sub-Kategorie
        
        Args:
            document_data: Dokumentdaten
            main_category: Hauptkategorie
            
        Returns:
            Sub-Kategorie Name
        """
        text = document_data.get('text', '').lower()
        keywords = document_data.get('keywords', [])
        
        # Kategorie-spezifische Sub-Kategorisierung
        if main_category == 'Rechnungen':
            return self._subcategorize_rechnung(text, keywords)
        
        elif main_category == 'Versicherungen':
            return self._subcategorize_versicherung(text, keywords)
        
        elif main_category == 'Verträge':
            return self._subcategorize_vertrag(text, keywords)
        
        elif main_category == 'Bank':
            return self._subcategorize_bank(text, keywords)
        
        elif main_category == 'Steuer':
            return 'Steuerdokumente'
        
        elif main_category == 'Medizin':
            return self._subcategorize_medizin(text, keywords)
        
        elif main_category == 'Behörden':
            return 'Behördendokumente'
        
        else:
            return 'Allgemein'
    
    def _subcategorize_rechnung(self, text: str, keywords: List[str]) -> str:
        """Sub-Kategorisierung für Rechnungen"""
        text = text.lower()
        patterns = {
            'Strom': ['strom', 'stadtwerke', 'energie', 'kwh'],
            'Gas': ['gas', 'heizung', 'erdgas'],
            'Wasser': ['wasser', 'wasserwerk', 'abwasser'],
            'Internet': ['internet', 'telekom', 'vodafone', 'o2', 'dsl', 'glasfaser'],
            'Telefon': ['telefon', 'handy', 'mobilfunk', 'smartphone'],
            'Versicherung': ['versicherung', 'beitrag', 'police'],
            'Einkauf': ['amazon', 'shop', 'bestell', 'lieferung', 'kauf'],
            'GEZ': ['rundfunk', 'gez', 'beitrag'],
        }
        
        for subcategory, keywords_list in patterns.items():
            if any(kw in text for kw in keywords_list):
                return subcategory
        
        return 'Sonstige_Rechnungen'
    
    def _subcategorize_versicherung(self, text: str, keywords: List[str]) -> str:
        """Sub-Kategorisierung für Versicherungen"""
        text = text.lower()
        patterns = {
            'Krankenversicherung': ['kranken', 'gesundheit', 'krankenkasse', 'tkk', 'aok', 'barmer'],
            'Haftpflicht': ['haftpflicht', 'privathaftpflicht'],
            'KFZ': ['kfz', 'auto', 'kraftfahrzeug', 'fahrzeug'],
            'Hausrat': ['hausrat', 'einbruch'],
            'Rechtsschutz': ['rechtsschutz', 'rechtschutz'],
            'Lebensversicherung': ['lebensversicherung', 'leben'],
            'Berufsunfähigkeit': ['berufsunfähigkeit', 'bu-versicherung'],
        }
        
        for subcategory, keywords_list in patterns.items():
            if any(kw in text for kw in keywords_list):
                return subcategory
        
        return 'Sonstige_Versicherungen'
    
    def _subcategorize_vertrag(self, text: str, keywords: List[str]) -> str:
        """Sub-Kategorisierung für Verträge"""
        text = text.lower()
        patterns = {
            'Mietvertrag': ['miete', 'wohnung', 'haus', 'vermieter'],
            'Arbeitsvertrag': ['arbeit', 'anstellung', 'gehalt', 'arbeitgeber'],
            'Handyvertrag': ['handy', 'mobilfunk', 'smartphone'],
            'Stromvertrag': ['strom', 'energie'],
            'Internetvertrag': ['internet', 'dsl'],
        }
        
        for subcategory, keywords_list in patterns.items():
            if any(kw in text for kw in keywords_list):
                return subcategory
        
        return 'Sonstige_Verträge'
    
    def _subcategorize_bank(self, text: str, keywords: List[str]) -> str:
        """Sub-Kategorisierung für Bank-Dokumente"""
        text = text.lower()
        patterns = {
            'Kontoauszug': ['kontoauszug', 'konto'],
            'Kreditkarte': ['kreditkarte', 'visa', 'mastercard'],
            'Depot': ['depot', 'wertpapier', 'aktie'],
            'Kredit': ['kredit', 'darlehen'],
        }
        
        for subcategory, keywords_list in patterns.items():
            if any(kw in text for kw in keywords_list):
                return subcategory
        
        return 'Sonstige_Bankdokumente'
    
    def _subcategorize_medizin(self, text: str, keywords: List[str]) -> str:
        """Sub-Kategorisierung für Medizin"""
        text = text.lower()
        patterns = {
            'Arztbriefe': ['arzt', 'befund', 'diagnose'],
            'Rezepte': ['rezept', 'medikament'],
            'Krankschreibung': ['krankschreibung', 'arbeitsunfähig'],
            'Labor': ['labor', 'blutwerte', 'blutbild'],
        }
        
        for subcategory, keywords_list in patterns.items():
            if any(kw in text for kw in keywords_list):
                return subcategory
        
        return 'Sonstige_Medizin'


def main():
    """Test-Funktion"""
    logging.basicConfig(level=logging.INFO)
    
    categorizer = DocumentCategorizer()
    
    # Test-Dokumente
    test_docs = [
        {
            'text': 'Stromrechnung für Januar 2024. Verbrauch: 150 kWh. Betrag: 45,50 EUR',
            'keywords': ['strom', 'rechnung', 'kwh', 'betrag']
        },
        {
            'text': 'Police-Nr. 12345. Ihre Haftpflichtversicherung. Jahresbeitrag: 125 EUR',
            'keywords': ['versicherung', 'haftpflicht', 'police', 'beitrag']
        },
        {
            'text': 'Mietvertrag für Wohnung in Berlin. Kaltmiete: 850 EUR',
            'keywords': ['vertrag', 'miete', 'wohnung']
        }
    ]
    
    for i, doc in enumerate(test_docs, 1):
        print(f"\n=== Test-Dokument {i} ===")
        print(f"Text: {doc['text'][:100]}...")
        
        main_cat, sub_cat, conf = categorizer.categorize(doc)
        
        print(f"Kategorie: {main_cat}/{sub_cat}")
        print(f"Confidence: {conf:.2f}")


if __name__ == "__main__":
    main()
