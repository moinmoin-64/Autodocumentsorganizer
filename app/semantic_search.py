"""
Semantic Search & Duplicate Detection
"""

import logging
import json
import numpy as np
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class SemanticSearch:
    """
    Verwaltet Embeddings und semantische Suche
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SemanticSearch, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.model = None
        self.enabled = False
        
        try:
            from sentence_transformers import SentenceTransformer
            # Kleines, schnelles Modell (ca. 80MB)
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.enabled = True
            logger.info("Semantic Search Model geladen (all-MiniLM-L6-v2)")
        except ImportError:
            logger.warning("sentence-transformers nicht installiert. Semantic Search deaktiviert.")
        except Exception as e:
            logger.error(f"Fehler beim Laden des Semantic Models: {e}")
            
        self._initialized = True

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generiert Embedding Vektor für Text"""
        if not self.enabled or not text:
            return None
            
        try:
            # Nur die ersten 1000 Zeichen nutzen (reicht für Duplikat-Check)
            embedding = self.model.encode(text[:1000])
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding Fehler: {e}")
            return None

    def find_duplicates(self, embedding: List[float], all_embeddings: List[Dict], threshold: float = 0.95) -> List[Tuple[int, float]]:
        """
        Findet Duplikate basierend auf Cosine Similarity
        
        Args:
            embedding: Vektor des neuen Dokuments
            all_embeddings: Liste von {'doc_id': int, 'embedding': List[float]}
            threshold: Ähnlichkeits-Schwellenwert (0-1)
            
        Returns:
            Liste von (doc_id, score)
        """
        if not self.enabled or not embedding or not all_embeddings:
            return []
            
        duplicates = []
        vec_a = np.array(embedding)
        norm_a = np.linalg.norm(vec_a)
        
        for item in all_embeddings:
            doc_id = item['doc_id']
            vec_b = np.array(item['embedding'])
            
            # Cosine Similarity
            norm_b = np.linalg.norm(vec_b)
            if norm_a == 0 or norm_b == 0:
                continue
                
            score = np.dot(vec_a, vec_b) / (norm_a * norm_b)
            
            if score >= threshold:
                duplicates.append((doc_id, float(score)))
                
        # Sortiere nach Score (höchste zuerst)
        duplicates.sort(key=lambda x: x[1], reverse=True)
        return duplicates
