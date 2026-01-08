"""
Custom Exceptions für besseres Error Handling
"""

class DocumentProcessingError(Exception):
    """Fehler bei der Dokumentenverarbeitung (OCR, Analyse, etc.)"""
    pass

class CategorizationError(Exception):
    """Fehler bei der Dokumentenkategorisierung"""
    pass

class SearchError(Exception):
    """Fehler bei der Suche"""
    pass

class ValidationError(Exception):
    """Input-Validierungsfehler"""
    pass

class ConfigurationError(Exception):
    """Konfigurationsfehler"""
    pass

class DatabaseError(Exception):
    """Datenbankfehler"""
    pass

class AuthenticationError(Exception):
    """Authentication-Fehler"""
    pass

class AuthorizationError(Exception):
    """Authorization-Fehler"""
    pass

class ExternalServiceError(Exception):
    """Fehler bei externen Services (Ollama, Scanner, etc.)"""
    pass

class FileProcessingError(Exception):
    """Fehler beim File-Upload oder -Processing"""
    pass
