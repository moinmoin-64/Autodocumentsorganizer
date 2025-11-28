"""
Ollama Client - Integration für lokales LLM
Chatbot-Funktionalität mit TinyLlama oder DeepSeek
"""

import logging
import requests
from typing import Dict, Optional, List
import yaml

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client für Ollama API (lokales LLM)"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialisiert Ollama Client
        
        Args:
            config_path: Pfad zur Konfiguration
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        ollama_config = self.config['ai']['ollama']
        
        self.base_url = ollama_config['url']
        self.model = ollama_config['model']
        self.temperature = ollama_config.get('temperature', 0.7)
        self.max_tokens = ollama_config.get('max_tokens', 2048)
        
        # Check connection
        self.available = self._check_connection()
        
        if self.available:
            logger.info(f"Ollama connected: {self.base_url}, Model: {self.model}")
        else:
            logger.warning("Ollama not available. Chatbot will use fallback responses.")
    
    def _check_connection(self) -> bool:
        """Prüft Ollama-Verbindung"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def chat(
        self,
        message: str,
        context: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Sendet Nachricht an Ollama und erhält Antwort
        
        Args:
            message: Benutzer-Nachricht
            context: Kontext-Daten (z.B. Versicherungen, Ausgaben)
            conversation_history: Bisherige Konversation
            
        Returns:
            Antwort vom Model
        """
        if not self.available:
            return self._fallback_response(message)
        
        # Baue Prompt
        prompt = self._build_prompt(message, context)
        
        try:
            # Ollama API Call
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'temperature': self.temperature,
                    'stream': False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('response', 'Entschuldigung, ich konnte keine Antwort generieren.')
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return self._fallback_response(message)
                
        except Exception as e:
            logger.error(f"Fehler bei Ollama-Anfrage: {e}")
            return self._fallback_response(message)
    
    def _build_prompt(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Baut Prompt für das Model
        
        Args:
            message: Benutzer-Nachricht
            context: Kontext-Daten
            
        Returns:
            Vollständiger Prompt
        """
        system_prompt = """Du bist ein hilfreicher Assistent für Dokumentenverwaltung.
Du hilfst dem Benutzer, Informationen über seine Dokumente, Versicherungen und Ausgaben zu finden.
Antworte präzise und hilfreich auf Deutsch.

"""
        
        # Füge Kontext hinzu
        if context:
            system_prompt += "Verfügbare Informationen:\n"
            
            if 'insurances' in context:
                system_prompt += f"Anzahl Versicherungen: {len(context['insurances'])}\n"
            
            if 'total_expenses' in context:
                system_prompt += f"Gesamtausgaben: {context['total_expenses']} EUR\n"
            
            if 'categories' in context:
                system_prompt += f"Kategorien: {', '.join(context['categories'].keys())}\n"
            
            system_prompt += "\n"
        
        # Kombiniere
        full_prompt = system_prompt + f"Benutzer: {message}\nAssistent:"
        
        return full_prompt
    
    def _fallback_response(self, message: str) -> str:
        """
        Fallback-Antworten wenn Ollama nicht verfügbar
        
        Args:
            message: Benutzer-Nachricht
            
        Returns:
            Fallback-Antwort
        """
        message_lower = message.lower()
        
        # Einfache Keyword-basierte Antworten
        if 'versicherung' in message_lower:
            return "Ich kann dir Informationen über deine Versicherungen geben. Schau in der Versicherungsliste im Dashboard."
        
        elif 'ausgaben' in message_lower or 'kosten' in message_lower:
            return "Deine Ausgaben kannst du im Tortendiagramm und im Jahresvergleich sehen."
        
        elif 'dokument' in message_lower or 'datei' in message_lower:
            return "Nutze die Suchfunktion oben rechts, um Dokumente zu finden."
        
        else:
            return "Entschuldigung, Ollama ist momentan nicht verfügbar. Bitte versuche es später erneut."


def main():
    """Test"""
    logging.basicConfig(level=logging.INFO)
    
    client = OllamaClient()
    
    if client.available:
        print("=== Ollama Chatbot Test ===")
        
        response = client.chat("Hallo, wie viele Versicherungen habe ich?")
        print(f"Antwort: {response}")
    else:
        print("Ollama nicht verfügbar")


if __name__ == "__main__":
    main()
