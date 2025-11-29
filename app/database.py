"""
Database - SQLite Datenbank für Metadaten
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import sqlite3
import json
import yaml

logger = logging.getLogger(__name__)


class Database:
    """SQLite Datenbank-Manager (einfache Implementierung ohne SQLAlchemy)"""

    def __init__(self, config_path: str = 'config.yaml'):
        """Initialisiert Datenbank"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.db_path = self.config['database']['path']

        # Erstelle Verzeichnis
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialisiere DB
        self._initialize_database()

        logger.info(f"Datenbank initialisiert: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Erstellt DB-Verbindung"""
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_database(self):
        """Erstellt Tabellen"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                date_document TEXT,
                date_added TEXT DEFAULT CURRENT_TIMESTAMP,
                summary TEXT,
                keywords TEXT,
                full_text TEXT,
                confidence REAL,
                processing_time REAL,
                content_hash TEXT,
                amount REAL,
                currency TEXT
            )
        ''')

        # Kategorien
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                parent_id INTEGER,
                auto_created INTEGER DEFAULT 0,
                FOREIGN KEY (parent_id) REFERENCES categories(id)
            )
        ''')

        # Tags
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                tag_name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        ''')

        # gespeicherte Suchen
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                name TEXT NOT NULL,
                filters TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Budgets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                month TEXT NOT NULL,
                budget_amount REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, month)
            )
        ''')

        # Audit Log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                action TEXT NOT NULL,
                resource_id TEXT,
                details TEXT
            )
        ''')

        # Optimierte Indexe für häufige Queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_date ON documents(date_document)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_document ON tags(document_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(tag_name)")
        
        # Composite Indizes für Performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_docs_category_date 
            ON documents(category, date_document)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_docs_amount_date
            ON documents(amount, date_document)
            WHERE amount IS NOT NULL
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tags_composite
            ON tags(tag_name, document_id)
        """)
        
        # Statistik-Cache-Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats_cache (
                cache_key TEXT PRIMARY KEY,
                result TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Trigger für Auto-Invalidierung des Caches
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS invalidate_stats_on_insert
            AFTER INSERT ON documents
            BEGIN
                DELETE FROM stats_cache;
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS invalidate_stats_on_update
            AFTER UPDATE ON documents
            BEGIN
                DELETE FROM stats_cache;
            END
        ''')

        conn.commit()
        conn.close()

    def add_document(
        self,
        filepath: str,
        category: str,
        subcategory: str,
        document_data: dict,
        date_document: Optional[datetime] = None
    ) -> Optional[int]:

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            date_str = date_document.isoformat() if date_document else None

            amount = document_data.get('validation', {}).get('amount')
            if amount is None and document_data.get('amounts'):
                amount = document_data['amounts'][0]

            currency = document_data.get('validation', {}).get('currency', 'EUR')

            cursor.execute('''
                INSERT INTO documents (
                    filepath, filename, category, subcategory,
                    date_document, summary, keywords, full_text,
                    confidence, processing_time, content_hash,
                    amount, currency
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                filepath,
                Path(filepath).name,
                category,
                subcategory,
                date_str,
                document_data.get('text', '')[:500],
                json.dumps(document_data.get('keywords', [])),
                document_data.get('text', ''),
                document_data.get('confidence', 0),
                document_data.get('processing_time', 0),
                document_data.get('content_hash'),
                amount,
                currency
            ))

            doc_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Dokument hinzugefügt: {filepath} (ID {doc_id})")
            return doc_id

        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Dokuments: {e}")
            conn.rollback()
            return None

        finally:
            conn.close()

    def search_documents(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[dict]:

        conn = self._get_connection()
        cursor = conn.cursor()

        sql = "SELECT * FROM documents WHERE 1=1"
        params = []

        if category:
            sql += " AND category = ?"
            params.append(category)

        if start_date:
            sql += " AND date_document >= ?"
            params.append(start_date.isoformat())

        if end_date:
            sql += " AND date_document <= ?"
            params.append(end_date.isoformat())

        if query:
            q = f"%{query}%"
            sql += " AND (filename LIKE ? OR summary LIKE ? OR keywords LIKE ?)"
            params.extend([q, q, q])

        sql += " ORDER BY date_added DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            d = dict(row)
            try:
                d["keywords"] = json.loads(d["keywords"]) if d["keywords"] else []
            except (json.JSONDecodeError, TypeError) as e:
                logger.debug(f"Keyword-Parsing fehlgeschlagen: {e}")
                d["keywords"] = []
            result.append(d)

        conn.close()
        return result

    def get_document_by_id(self, doc_id: int) -> Optional[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        doc = dict(row)
        try:
            doc["keywords"] = json.loads(doc["keywords"]) if doc["keywords"] else []
        except (json.JSONDecodeError, TypeError) as e:
            logger.debug(f"Keyword-Parsing fehlgeschlagen für Doc {doc_id}: {e}")
            doc["keywords"] = []
        return doc

    # ----------------------------------------------------------
    #   FIXED: Die kaputt kopierte Methode ist vollständig neu!
    # ----------------------------------------------------------
    def search_documents_advanced(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[dict]:

        conn = self._get_connection()
        cursor = conn.cursor()

        where = []
        params = []

        if query:
            where.append("(full_text LIKE ? OR filename LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        if category:
            where.append("category = ?")
            params.append(category)

        if start_date:
            where.append("date_document >= ?")
            params.append(start_date.isoformat())

        if end_date:
            where.append("date_document <= ?")
            params.append(end_date.isoformat())

        if min_amount:
            where.append("amount >= ?")
            params.append(min_amount)

        if max_amount:
            where.append("amount <= ?")
            params.append(max_amount)

        if tags:
            placeholders = ",".join(["?"] * len(tags))
            where.append(f"""
            id IN (
                SELECT document_id FROM tags
                WHERE tag_name IN ({placeholders})
                GROUP BY document_id
                HAVING COUNT(DISTINCT tag_name) = ?
            )
            """)
            params.extend([t.lower() for t in tags])
            params.append(len(tags))

        sql = "SELECT * FROM documents"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY date_document DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        # Convert rows...
        result = []
        for row in rows:
            d = dict(row)
            try:
                d["keywords"] = json.loads(d["keywords"]) if d["keywords"] else []
            except (json.JSONDecodeError, TypeError) as e:
                logger.debug(f"Keyword-Parsing fehlgeschlagen: {e}")
                d["keywords"] = []
            result.append(d)
            
        conn.close()
        return result

    # ----------------------------------------------------------
    #  FIXED: add_tag() – die Funktion war kaputt abgeschnitten
    # ----------------------------------------------------------
    def add_tag(self, document_id: int, tag_name: str) -> Optional[int]:
        """Fügt einem Dokument ein Tag hinzu"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO tags (document_id, tag_name) VALUES (?, ?)",
                (document_id, tag_name.lower())
            )

            tag_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"Tag '{tag_name}' zu Dokument {document_id} hinzugefügt")
            return tag_id

        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen eines Tags: {e}")
            return None

    def remove_tag(self, tag_id: int) -> bool:
        """Entfernt ein Tag"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
            conn.commit()
            conn.close()

            logger.info(f"Tag {tag_id} entfernt")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Entfernen eines Tags: {e}")
            return False

    def get_tags(self, document_id: int) -> List[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM tags WHERE document_id = ? ORDER BY tag_name",
            (document_id,)
        )

        tags = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tags

    def get_all_tags(self) -> List[str]:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT tag_name FROM tags ORDER BY tag_name")
        tags = [row["tag_name"] for row in cursor.fetchall()]

        conn.close()
        return tags

    def save_search(self, name: str, filters: dict, user_id: str = 'default') -> Optional[int]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO saved_searches (user_id, name, filters) VALUES (?, ?, ?)",
                (user_id, name, json.dumps(filters))
            )

            sid = cursor.lastrowid
            conn.commit()
            conn.close()
            return sid

        except Exception as e:
            logger.error(f"Fehler beim Speichern einer Suche: {e}")
            return None

    def get_saved_searches(self, user_id: str = "default") -> List[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM saved_searches WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )

        result = []
        for row in cursor.fetchall():
            r = dict(row)
            r["filters"] = json.loads(r["filters"])
            result.append(r)

        conn.close()
        return result

    def delete_saved_search(self, search_id: int) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM saved_searches WHERE id = ?", (search_id,))
            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Fehler beim Löschen einer Suche: {e}")
            return False

    def set_budget(self, category: str, month: str, amount: float) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO budgets (category, month, budget_amount)
                VALUES (?, ?, ?)
                ON CONFLICT(category, month)
                DO UPDATE SET budget_amount = excluded.budget_amount
            ''', (category, month, amount))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Fehler beim Setzen eines Budgets: {e}")
            return False

    def get_budget(self, category: str, month: str) -> Optional[float]:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT budget_amount FROM budgets WHERE category = ? AND month = ?",
            (category, month)
        )

        row = cursor.fetchone()
        conn.close()

        return row['budget_amount'] if row else None

    def get_budget_status(self, category: str, month: str) -> dict:
        budget = self.get_budget(category, month) or 0.0

        conn = self._get_connection()
        cursor = conn.cursor()

        year, month_num = month.split('-')
        year = int(year)
        month_num = int(month_num)

        start = f"{year}-{month_num:02d}-01"
        end = f"{year + (1 if month_num == 12 else 0)}-{(1 if month_num == 12 else month_num + 1):02d}-01"

        cursor.execute('''
            SELECT SUM(amount) AS total
            FROM documents
            WHERE category = ? AND date_document >= ? AND date_document < ?
        ''', (category, start, end))

        actual = cursor.fetchone()["total"] or 0.0
        conn.close()

        return {
            "budget": budget,
            "actual": actual,
            "remaining": budget - actual,
            "percent": (actual / budget * 100) if budget > 0 else 0
        }

    def get_monthly_expenses(self, year: int, month: int) -> dict:
        conn = self._get_connection()
        cursor = conn.cursor()

        start = f"{year}-{month:02d}-01"
        end = f"{year + (1 if month == 12 else 0)}-{(1 if month == 12 else month + 1):02d}-01"

        cursor.execute('''
            SELECT category, SUM(amount) as total
            FROM documents
            WHERE date_document >= ? AND date_document < ?
                  AND amount IS NOT NULL
            GROUP BY category
        ''', (start, end))

        result = {row["category"]: row["total"] for row in cursor.fetchall()}
        conn.close()

        return result

    def get_monthly_trends(self, year: int) -> dict:
        """Monatliche Gesamtausgaben eines Jahres"""
        conn = self._get_connection()
        cursor = conn.cursor()

        totals = {}

        for m in range(1, 13):
            start = f"{year}-{m:02d}-01"
            end = f"{year + (1 if m == 12 else 0)}-{(1 if m == 12 else m + 1):02d}-01"

            cursor.execute('''
                SELECT SUM(amount) AS total
                FROM documents
                WHERE date_document >= ? AND date_document < ?
            ''', (start, end))

            value = cursor.fetchone()["total"] or 0.0
            totals[m] = value

        conn.close()
        return totals

    def get_statistics(self) -> Dict:
        """
        Holt Gesamt-Statistiken (mit Caching)
        """
        # Versuche Cache (Redis/Memory)
        try:
            from app.cache import CacheManager
            cache = CacheManager()
            cached_stats = cache.get('db:statistics')
            if cached_stats:
                return cached_stats
        except ImportError:
            logger.debug("Cache nicht verfügbar")
            pass
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {
            'total_documents': 0,
            'categories': {},
            'recent_uploads': []
        }
        
        # Total Documents
        cursor.execute("SELECT COUNT(*) as count FROM documents")
        stats['total_documents'] = cursor.fetchone()['count']
        
        # Categories
        cursor.execute("SELECT category, COUNT(*) as count FROM documents GROUP BY category")
        for row in cursor.fetchall():
            stats['categories'][row['category']] = row['count']
            
        conn.close()
        
        # Cache speichern
        try:
            cache.set('db:statistics', stats, timeout=3600)
        except (ImportError, Exception) as e:
            logger.debug(f"Cache-Speicherung fehlgeschlagen: {e}")
            pass
            
        return stats

    # --- Semantic Search Support ---

    def save_embedding(self, document_id: int, embedding: List[float]):
        """Speichert Embedding Vektor"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT OR REPLACE INTO document_embeddings (document_id, embedding) VALUES (?, ?)",
                (document_id, json.dumps(embedding))
            )
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Embeddings: {e}")

    def get_all_embeddings(self) -> List[Dict]:
        """Holt alle Embeddings für Duplikat-Check"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT document_id, embedding FROM document_embeddings")
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                try:
                    result.append({
                        'doc_id': row['document_id'],
                        'embedding': json.loads(row['embedding'])
                    })
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Embedding-Parsing fehlgeschlagen: {e}")
                    pass
            
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Fehler beim Laden der Embeddings: {e}")
            return []

    def log_audit_event(self, user_id: str, action: str, resource_id: Optional[str] = None, details: Optional[dict] = None):
        """Loggt ein Audit-Event"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audit_log (user_id, action, resource_id, details)
                VALUES (?, ?, ?, ?)
            ''', (user_id, action, resource_id, json.dumps(details) if details else None))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Fehler beim Audit-Log: {e}")

    def log_audit_event(self, user_id: str, action: str, resource_id: Optional[str] = None, details: Optional[dict] = None):
        """Loggt ein Audit-Event"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audit_log (user_id, action, resource_id, details)
                VALUES (?, ?, ?, ?)
            ''', (user_id, action, resource_id, json.dumps(details) if details else None))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Fehler beim Audit-Log: {e}")
