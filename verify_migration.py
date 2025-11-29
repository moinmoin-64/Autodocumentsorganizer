"""
Verify Database Content
"""
from app.db_config import Session
from app.models import Document, Tag, AuditLog, SavedSearch, Budget
from sqlalchemy import func

def verify():
    session = Session()
    try:
        doc_count = session.query(func.count(Document.id)).scalar()
        tag_count = session.query(func.count(Tag.id)).scalar()
        audit_count = session.query(func.count(AuditLog.id)).scalar()
        
        print(f"Documents: {doc_count}")
        print(f"Tags: {tag_count}")
        print(f"Audit Logs: {audit_count}")
        
        # Check a sample document
        doc = session.query(Document).first()
        if doc:
            print(f"Sample Doc: {doc.filename} (ID: {doc.id})")
            print(f"  Tags: {[t.name for t in doc.tags]}")
            
    finally:
        session.close()

if __name__ == "__main__":
    verify()
