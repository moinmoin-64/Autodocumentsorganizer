"""
Async Processing Queue - Verarbeitet Dokumente asynchron
Verhindert Blockierung bei Scanner-Input
"""

import logging
import queue
import threading
import time
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentQueue:
    """Thread-safe Queue für asynchrone Dokumentenverarbeitung"""
    
    def __init__(self, worker_count: int = 2):
        """
        Initialisiert die Processing Queue
        
        Args:
            worker_count: Anzahl paralleler Worker-Threads
        """
        self.queue = queue.Queue()
        self.worker_count = worker_count
        self.workers = []
        self.running = False
        self.processing_callback = None
        
        logger.info(f"DocumentQueue initialisiert mit {worker_count} Workers")
    
    def set_processing_callback(self, callback: Callable):
        """
        Setzt die Verarbeitungs-Funktion
        
        Args:
            callback: Funktion die (file_path) akzeptiert und Dokument verarbeitet
        """
        self.processing_callback = callback
    
    def start(self):
        """Startet Worker-Threads"""
        if self.running:
            logger.warning("Queue läuft bereits")
            return
        
        self.running = True
        
        for i in range(self.worker_count):
            worker = threading.Thread(
                target=self._worker,
                name=f"DocumentWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"{self.worker_count} Worker-Threads gestartet")
    
    def stop(self):
        """Stoppt Worker-Threads"""
        logger.info("Stoppe Queue...")
        self.running = False
        
        # Warte auf alle Worker
        for worker in self.workers:
            worker.join(timeout=5)
        
        self.workers = []
        logger.info("Queue gestoppt")
    
    def add_document(self, file_path: str, priority: int = 5) -> str:
        """
        Fügt Dokument zur Verarbeitungs-Queue hinzu
        
        Args:
            file_path: Pfad zum Dokument
            priority: Priorität (1=höchste, 10=niedrigste)
            
        Returns:
            Job-ID
        """
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        job = {
            'id': job_id,
            'file_path': file_path,
            'priority': priority,
            'added_at': datetime.now(),
            'status': 'queued'
        }
        
        self.queue.put((priority, job))
        
        logger.info(f"Dokument zur Queue hinzugefügt: {file_path} (Job: {job_id})")
        
        return job_id
    
    def _worker(self):
        """Worker-Thread der Dokumente verarbeitet"""
        thread_name = threading.current_thread().name
        logger.info(f"{thread_name} gestartet")
        
        while self.running:
            try:
                # Hole nächstes Item (timeout um running-Flag zu checken)
                priority, job = self.queue.get(timeout=1)
                
                if not self.running:
                    break
                
                job['status'] = 'processing'
                job['started_at'] = datetime.now()
                
                logger.info(f"{thread_name}: Verarbeite {job['file_path']}")
                
                try:
                    # Verarbeite Dokument
                    if self.processing_callback:
                        self.processing_callback(job['file_path'])
                    else:
                        logger.error("Kein Processing Callback gesetzt!")
                    
                    job['status'] = 'completed'
                    logger.info(f"{thread_name}: ✓ Fertig - {job['file_path']}")
                    
                except Exception as e:
                    job['status'] = 'failed'
                    job['error'] = str(e)
                    logger.error(f"{thread_name}: ✗ Fehler - {job['file_path']}: {e}")
                
                finally:
                    job['completed_at'] = datetime.now()
                    self.queue.task_done()
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"{thread_name}: Unerwarteter Fehler: {e}")
        
        logger.info(f"{thread_name} gestoppt")
    
    def get_queue_size(self) -> int:
        """Gibt Anzahl wartender Jobs zurück"""
        return self.queue.qsize()
    
    def is_empty(self) -> bool:
        """Prüft ob Queue leer ist"""
        return self.queue.empty()
    
    def wait_complete(self, timeout: Optional[float] = None):
        """
        Wartet bis alle Jobs verarbeitet sind
        
        Args:
            timeout: Max. Wartezeit in Sekunden
        """
        self.queue.join()


# Singleton-Instanz
_global_queue = None


def get_global_queue(worker_count: int = 2) -> DocumentQueue:
    """Gibt globale Queue-Instanz zurück (Singleton)"""
    global _global_queue
    
    if _global_queue is None:
        _global_queue = DocumentQueue(worker_count=worker_count)
    
    return _global_queue


def main():
    """Test-Funktion"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    def process_document(file_path):
        """Dummy Processing"""
        logger.info(f"Verarbeite: {file_path}")
        time.sleep(2)  # Simuliere Verarbeitung
    
    # Erstelle Queue
    doc_queue = DocumentQueue(worker_count=2)
    doc_queue.set_processing_callback(process_document)
    doc_queue.start()
    
    # Füge Test-Dokumente hinzu
    for i in range(5):
        doc_queue.add_document(f"/tmp/test_doc_{i}.pdf", priority=i)
    
    print(f"Queue Size: {doc_queue.get_queue_size()}")
    
    # Warte auf Completion
    doc_queue.wait_complete()
    
    print("Alle Jobs abgeschlossen!")
    
    doc_queue.stop()


if __name__ == "__main__":
    main()
