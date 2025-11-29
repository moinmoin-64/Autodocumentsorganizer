"""
SQLite → SQLAlchemy Migration
Migriert Daten von raw SQLite3 zu SQLAlchemy
"""
import sqlite3
import shutil
import os
from app.db_config import engine, Session, DATABASE_PATH, init_db
from app.models import Base, Document, Tag, AuditLog, SavedSearch, Budget
from datetime import datetime
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Führt Migration durch"""
    db_path = DATABASE_PATH
    backup_path = db_path + '.backup'
    raw_path = db_path + '.raw'

    if not os.path.exists(db_path):
        logger.info("Keine existierende Datenbank gefunden. Initialisiere neu...")
        init_db()
        return

    # 1. Backup erstellen
    logger.info(f"Erstelle Backup von {db_path} nach {backup_path}...")
    shutil.copy(db_path, backup_path)
    
    # 2. Verschiebe Original zu .raw (damit wir eine saubere neue DB erstellen können)
    logger.info(f"Verschiebe Original-DB nach {raw_path}...")
    shutil.move(db_path, raw_path)
    
    # 3. Erstelle neue Tabellen (in der nun leeren db_path Location)
    logger.info("Erstelle SQLAlchemy Tabellen...")
    init_db()
    
    # 4. Migriere Daten
    logger.info("Migriere Daten aus alter DB...")
    
    try:
        # Verbindung zur alten DB
        conn = sqlite3.connect(raw_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        session = Session()
        
        # --- Documents ---
        logger.info("Migriere Dokumente...")
        cursor.execute("SELECT * FROM documents")
        rows = cursor.fetchall()
        
        doc_map = {} # Old ID -> New Object (though we try to keep IDs)

        for row in rows:
            # Parse dates
            date_doc = None
            if row['date_document']:
                try:
                    date_doc = datetime.fromisoformat(row['date_document'])
                except ValueError:
                    pass
            
            date_added = datetime.utcnow()
            if row['date_added']:
                try:
                    date_added = datetime.fromisoformat(row['date_added'])
                except ValueError:
                    pass

            doc = Document(
                id=row['id'],
                filename=row['filename'],
                filepath=row['filepath'],
                category=row['category'],
                subcategory=row['subcategory'],
                date_document=date_doc,
                date_added=date_added,
                summary=row['summary'],
                keywords=row['keywords'], # Already JSON string in DB
                full_text=row['full_text'],
                ocr_confidence=row['confidence'],
                processing_time=row['processing_time'],
                content_hash=row['content_hash'],
                amount=row['amount'],
                currency=row['currency']
            )
            session.add(doc)
            doc_map[row['id']] = doc
        
        session.flush() # Ensure IDs are set

        # --- Tags ---
        # Note: Old schema had tags table with document_id. New schema has Tag model and association table.
        # We need to migrate tags to Tag objects and link them.
        logger.info("Migriere Tags...")
        cursor.execute("SELECT * FROM tags")
        tag_rows = cursor.fetchall()
        
        # Cache for existing tags to avoid duplicates
        tag_cache = {} 
        
        for row in tag_rows:
            tag_name = row['tag_name']
            doc_id = row['document_id']
            
            if tag_name not in tag_cache:
                # Check if tag already exists in session (or DB)
                existing_tag = session.query(Tag).filter_by(name=tag_name).first()
                if not existing_tag:
                    new_tag = Tag(name=tag_name)
                    session.add(new_tag)
                    tag_cache[tag_name] = new_tag
                else:
                    tag_cache[tag_name] = existing_tag
            
            tag_obj = tag_cache[tag_name]
            
            # Link to document
            # We need to find the document object in the session
            # Since we preserved IDs, we can try to fetch it
            doc = session.get(Document, doc_id)
            if doc:
                if tag_obj not in doc.tags:
                    doc.tags.append(tag_obj)
        
        # --- Saved Searches ---
        logger.info("Migriere Gespeicherte Suchen...")
        cursor.execute("SELECT * FROM saved_searches")
        for row in cursor.fetchall():
            search = SavedSearch(
                id=row['id'],
                user_id=row['user_id'],
                name=row['name'],
                filters=row['filters'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow()
            )
            session.add(search)

        # --- Budgets ---
        logger.info("Migriere Budgets...")
        cursor.execute("SELECT * FROM budgets")
        for row in cursor.fetchall():
            budget = Budget(
                id=row['id'],
                category=row['category'],
                month=row['month'],
                budget_amount=row['budget_amount'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow()
            )
            session.add(budget)

        # --- Audit Logs ---
        logger.info("Migriere Audit Logs...")
        cursor.execute("SELECT * FROM audit_log")
        for row in cursor.fetchall():
            log = AuditLog(
                id=row['id'],
                timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else datetime.utcnow(),
                user_id=row['user_id'],
                action=row['action'],
                document_id=int(row['resource_id']) if row['resource_id'] and row['resource_id'].isdigit() else None,
                details=row['details']
            )
            session.add(log)

        session.commit()
        logger.info("✅ Migration erfolgreich abgeschlossen!")
        
    except Exception as e:
        logger.error(f"❌ Fehler bei der Migration: {e}")
        session.rollback()
        # Restore backup
        logger.info("Stelle Backup wieder her...")
        session.close()
        if os.path.exists(db_path):
            os.remove(db_path)
        shutil.move(raw_path, db_path)
        raise e
    finally:
        session.close()
        conn.close()

if __name__ == '__main__':
    migrate()
