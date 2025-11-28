"""
Document Management System - Main Application Package
"""

__version__ = "1.0.0"
__author__ = "Your Name"

# Package-level imports für einfacheren Zugriff
from .scanner_handler import ScannerHandler
from .document_processor import DocumentProcessor
from .categorizer import DocumentCategorizer
from .storage_manager import StorageManager
from .data_extractor import DataExtractor
from .database import Database
from .search_engine import SearchEngine
from .ollama_client import OllamaClient

__all__ = [
    'ScannerHandler',
    'DocumentProcessor',
    'DocumentCategorizer',
    'StorageManager',
    'DataExtractor',
    'Database',
    'SearchEngine',
    'OllamaClient',
]
