"""
Search Engine - BM25-basierte Dokumentensuche
Implementiert relevante Volltextsuche
"""

import logging
import re
import math
from typing import List, Dict, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class SearchEngine:
    """BM25-Algorithmus für relevante Dokumentensuche"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialisiert Search Engine
        
        Args:
            k1: BM25 parameter (term frequency saturation)
            b: BM25 parameter (length normalization)
        """
        self.k1 = k1
        self.b = b
        
        self.documents = []
        self.doc_lengths = []
        self.avgdl = 0
        self.doc_count = 0
        self.inverted_index = {}
        self.idf = {}
    
    def index_documents(self, documents: List[Dict]):
        """
        Indexiert Dokumente für Suche
        
        Args:
            documents: Liste von Dokumenten mit 'id', 'text', 'filename', etc.
        """
        self.documents = documents
        self.doc_count = len(documents)
        
        # Berechne Document Lengths
        self.doc_lengths = []
        for doc in documents:
            text = self._get_searchable_text(doc)
            tokens = self._tokenize(text)
            self.doc_lengths.append(len(tokens))
        
        # Average Document Length
        self.avgdl = sum(self.doc_lengths) / self.doc_count if self.doc_count > 0 else 0
        
        # Baue Inverted Index
        self._build_inverted_index()
        
        # Berechne IDF
        self._calculate_idf()
        
        logger.info(f"Indexiert: {self.doc_count} Dokumente, AvgDL: {self.avgdl:.1f}")
    
    def _get_searchable_text(self, doc: Dict) -> str:
        """Kombiniert durchsuchbare Felder"""
        parts = [
            doc.get('filename', ''),
            doc.get('summary', ''),
            doc.get('keywords', ''),
            doc.get('full_text', '')[:1000],  # Nur erste 1000 Zeichen
        ]
        return ' '.join(str(p) for p in parts if p)
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenisiert Text (Kleinbuchstaben, Wörter)
        
        Args:
            text: Eingabetext
            
        Returns:
            Liste von Tokens
        """
        # Kleinbuchstaben
        text = text.lower()
        
        # Extrahiere Wörter (inkl. deutsche Umlaute)
        tokens = re.findall(r'\b[a-zäöüß]+\b', text)
        
        return tokens
    
    def _build_inverted_index(self):
        """Baut Inverted Index auf"""
        self.inverted_index = {}
        
        for doc_id, doc in enumerate(self.documents):
            text = self._get_searchable_text(doc)
            tokens = self._tokenize(text)
            
            # Count term frequencies
            term_freq = Counter(tokens)
            
            for term, freq in term_freq.items():
                if term not in self.inverted_index:
                    self.inverted_index[term] = {}
                
                self.inverted_index[term][doc_id] = freq
    
    def _calculate_idf(self):
        """Berechnet Inverse Document Frequency"""
        self.idf = {}
        
        for term, posting_list in self.inverted_index.items():
            # IDF = log((N - df + 0.5) / (df + 0.5) + 1)
            df = len(posting_list)  # Document Frequency
            idf = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)
            self.idf[term] = idf
    
    def search(self, query: str, top_k: int = 20) -> List[Tuple[int, float]]:
        """
        Sucht Dokumente
        
        Args:
            query: Suchbegriff
            top_k: Anzahl Top-Ergebnisse
            
        Returns:
            Liste von (doc_id, score) Tupeln, sortiert nach Score
        """
        # Tokenize Query
        query_tokens = self._tokenize(query)
        
        if not query_tokens:
            return []
        
        # Berechne Scores
        scores = {}
        
        for doc_id in range(self.doc_count):
            score = self._calculate_bm25_score(query_tokens, doc_id)
            if score > 0:
                scores[doc_id] = score
        
        # Sortiere nach Score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_results[:top_k]
    
    def _calculate_bm25_score(self, query_tokens: List[str], doc_id: int) -> float:
        """
        Berechnet BM25-Score für ein Dokument
        
        Args:
            query_tokens: Query-Tokens
            doc_id: Dokument-ID
            
        Returns:
            BM25-Score
        """
        score = 0.0
        doc_length = self.doc_lengths[doc_id]
        
        for term in query_tokens:
            if term not in self.inverted_index:
                continue
            
            if doc_id not in self.inverted_index[term]:
                continue
            
            # Term Frequency im Dokument
            tf = self.inverted_index[term][doc_id]
            
            # IDF
            idf = self.idf.get(term, 0)
            
            # BM25 Formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avgdl)
            
            score += idf * (numerator / denominator)
        
        return score
    
    def get_documents_by_ids(self, doc_ids: List[int]) -> List[Dict]:
        """
        Holt Dokumente per IDs
        
        Args:
            doc_ids: Liste von Dokument-IDs
            
        Returns:
            Liste von Dokumenten
        """
        return [self.documents[doc_id] for doc_id in doc_ids if 0 <= doc_id < self.doc_count]


def main():
    """Test"""
    logging.basicConfig(level=logging.INFO)
    
    # Test-Dokumente
    docs = [
        {'id': 1, 'filename': 'stromrechnung.pdf', 'text': 'Rechnung für Strom Januar 2024'},
        {'id': 2, 'filename': 'haftpflicht.pdf', 'text': 'Versicherungspolice Haftpflicht'},
        {'id': 3, 'filename': 'mietvertrag.pdf', 'text': 'Mietvertrag Wohnung Berlin'},
    ]
    
    engine = BM25SearchEngine()
    engine.index_documents(docs)
    
    # Suche
    results = engine.search("rechnung strom", top_k=5)
    
    print("=== Suchergebnisse ===")
    for doc_id, score in results:
        doc = docs[doc_id]
        print(f"Score: {score:.2f} - {doc['filename']}")


if __name__ == "__main__":
    main()
