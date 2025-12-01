"""
Database - SQLAlchemy Implementation
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import yaml
from sqlalchemy import or_, and_, func, desc
from app.db_config import get_db, engine
from app.models import Base, Document, Tag, AuditLog, SavedSearch, Budget, document_tags

logger = logging.getLogger(__name__)

class Database:
    """SQLAlchemy Database Manager"""

    def __init__(self, config_path: str = 'config.yaml'):
        """Initialisiert Datenbank"""
        # Config laden (für Kompatibilität)
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.warning(f"Config konnte nicht geladen werden: {e}. Nutze Defaults.")
            self.config = {}
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Laden der Config: {e}")
            self.config = {}
        
        # Sicherstellen, dass Tabellen existieren
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized with SQLAlchemy")

    def close(self):
        """Dummy method for compatibility"""
        pass

    # --- Documents ---

    def add_document(
        self,
        filepath: str,
        category: str,
        subcategory: str,
        document_data: dict,
        date_document: Optional[datetime] = None
    ) -> Optional[int]:
        """Fügt ein Dokument hinzu"""
        try:
            with get_db() as session:
                amount = document_data.get('validation', {}).get('amount')
                if amount is None and document_data.get('amounts'):
                    amount = document_data['amounts'][0]

                currency = document_data.get('validation', {}).get('currency', 'EUR')

                doc = Document(
                    filepath=filepath,
                    filename=document_data.get('filename', filepath.split('/')[-1]),
                    category=category,
                    subcategory=subcategory,
                    date_document=date_document,
                    summary=document_data.get('text', '')[:500],
                    keywords=json.dumps(document_data.get('keywords', [])),
                    full_text=document_data.get('text', ''),
                    ocr_confidence=document_data.get('confidence', 0),
                    processing_time=document_data.get('processing_time', 0),
                    content_hash=document_data.get('content_hash'),
                    amount=amount,
                    currency=currency
                )
                
                session.add(doc)
                session.flush()
                doc_id = doc.id
                
                logger.info(f"Dokument hinzugefügt: {filepath} (ID {doc_id})")
                return doc_id

        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Dokuments: {e}")
            return None

    def get_document(self, doc_id: int) -> Optional[dict]:
        """Holt Dokument per ID"""
        try:
            with get_db() as session:
                doc = session.get(Document, doc_id)
                if not doc:
                    return None
                return self._doc_to_dict(doc)
        except Exception as e:
            logger.error(f"Fehler beim Laden von Doc {doc_id}: {e}")
            return None
            
    # Alias for compatibility
    get_document_by_id = get_document

    def get_db_session(self):
        """Gibt eine DB-Session zurück (Context Manager)"""
        return get_db()

    def delete_document(self, doc_id: int) -> bool:
        """Löscht ein Dokument"""
        try:
            with get_db() as session:
                doc = session.get(Document, doc_id)
                if doc:
                    session.delete(doc)
                    return True
                return False
        except Exception as e:
            logger.error(f"Fehler beim Löschen von Doc {doc_id}: {e}")
            return False

    def update_document(self, doc_id: int, data: dict) -> bool:
        """Aktualisiert Dokument-Metadaten"""
        try:
            with get_db() as session:
                doc = session.get(Document, doc_id)
                if not doc:
                    return False
                
                if 'category' in data:
                    doc.category = data['category']
                if 'subcategory' in data:
                    doc.subcategory = data['subcategory']
                if 'date_document' in data:
                    if isinstance(data['date_document'], str):
                        try:
                            doc.date_document = datetime.fromisoformat(data['date_document'])
                        except:
                            pass
                    else:
                        doc.date_document = data['date_document']
                if 'summary' in data:
                    doc.summary = data['summary']
                if 'amount' in data:
                    doc.amount = data['amount']
                
                return True
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren von Doc {doc_id}: {e}")
            return False

    def search_documents(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        year: Optional[int] = None
    ) -> List[dict]:
        """Einfache Suche"""
        try:
            with get_db() as session:
                q = session.query(Document)

                if category:
                    q = q.filter(Document.category == category)

                if start_date:
                    q = q.filter(Document.date_document >= start_date)

                if end_date:
                    q = q.filter(Document.date_document <= end_date)
                    
                if year:
                    # SQLite specific or generic year filtering
                    # extract('year', Document.date_document) == year
                    q = q.filter(func.strftime('%Y', Document.date_document) == str(year))

                if query:
                    search = f"%{query}%"
                    q = q.filter(or_(
                        Document.filename.ilike(search),
                        Document.summary.ilike(search),
                        Document.keywords.ilike(search)
                    ))

                q = q.order_by(desc(Document.date_added)).limit(limit).offset(offset)
                
                results = []
                for doc in q.all():
                    results.append(self._doc_to_dict(doc))
                
                return results
        except Exception as e:
            logger.error(f"Fehler bei der Suche: {e}")
            return []

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
        """Erweiterte Suche"""
        try:
            with get_db() as session:
                q = session.query(Document)

                if query:
                    search = f"%{query}%"
                    q = q.filter(or_(
                        Document.full_text.ilike(search),
                        Document.filename.ilike(search)
                    ))

                if category:
                    q = q.filter(Document.category == category)

                if start_date:
                    q = q.filter(Document.date_document >= start_date)

                if end_date:
                    q = q.filter(Document.date_document <= end_date)

                if min_amount is not None:
                    q = q.filter(Document.amount >= min_amount)

                if max_amount is not None:
                    q = q.filter(Document.amount <= max_amount)

                if tags:
                    for tag_name in tags:
                        q = q.filter(Document.tags.any(Tag.name == tag_name))

                q = q.order_by(desc(Document.date_document)).limit(limit)

                results = []
                for doc in q.all():
                    results.append(self._doc_to_dict(doc))
                
                return results
        except Exception as e:
            logger.error(f"Fehler bei erweiterter Suche: {e}")
            return []

    # --- Tags ---

    def create_tag(self, name: str, color: str = '#808080') -> Optional[int]:
        """Erstellt neuen Tag"""
        try:
            with get_db() as session:
                name = name.lower()
                tag = session.query(Tag).filter_by(name=name).first()
                if not tag:
                    tag = Tag(name=name, color=color)
                    session.add(tag)
                    session.flush()
                return tag.id
        except Exception as e:
            logger.error(f"Fehler beim Erstellen von Tag: {e}")
            return None

    def delete_tag(self, tag_id: int) -> bool:
        """Löscht Tag"""
        try:
            with get_db() as session:
                tag = session.get(Tag, tag_id)
                if tag:
                    session.delete(tag)
                    return True
                return False
        except Exception as e:
            logger.error(f"Fehler beim Löschen von Tag: {e}")
            return False

    def get_all_tags(self) -> List[dict]:
        """Holt alle Tags"""
        try:
            with get_db() as session:
                tags = session.query(Tag).order_by(Tag.name).all()
                return [{'id': t.id, 'name': t.name, 'color': t.color} for t in tags]
        except Exception as e:
            logger.error(f"Fehler beim Laden aller Tags: {e}")
            return []

    def get_document_tags(self, document_id: int) -> List[dict]:
        """Holt Tags für Dokument"""
        try:
            with get_db() as session:
                doc = session.get(Document, document_id)
                if not doc:
                    return []
                return [{'id': t.id, 'name': t.name, 'color': t.color} for t in doc.tags]
        except Exception as e:
            logger.error(f"Fehler beim Laden der Tags: {e}")
            return []
            
    # Alias for compatibility
    get_tags = get_document_tags

    def add_tag_to_document(self, document_id: int, tag_id: int) -> bool:
        """Fügt existierenden Tag zu Dokument hinzu"""
        try:
            with get_db() as session:
                doc = session.get(Document, document_id)
                tag = session.get(Tag, tag_id)
                
                if doc and tag:
                    if tag not in doc.tags:
                        doc.tags.append(tag)
                    return True
                return False
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen von Tag zu Doc: {e}")
            return False

    def add_tag(self, document_id: int, tag_name: str) -> Optional[int]:
        """Legacy: Fügt Tag per Name hinzu (erstellt wenn nötig)"""
        try:
            with get_db() as session:
                doc = session.get(Document, document_id)
                if not doc:
                    return None
                
                tag_name = tag_name.lower()
                tag = session.query(Tag).filter_by(name=tag_name).first()
                
                if not tag:
                    tag = Tag(name=tag_name)
                    session.add(tag)
                
                if tag not in doc.tags:
                    doc.tags.append(tag)
                    session.commit()
                    return tag.id
                return tag.id
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen von Tag: {e}")
            return None

    def remove_tag_from_document(self, document_id: int, tag_id: int) -> bool:
        """Entfernt Tag von Dokument"""
        try:
            with get_db() as session:
                doc = session.get(Document, document_id)
                tag = session.get(Tag, tag_id)
                
                if doc and tag and tag in doc.tags:
                    doc.tags.remove(tag)
                    return True
                return False
        except Exception as e:
            logger.error(f"Fehler beim Entfernen von Tag: {e}")
            return False

    # --- Saved Searches ---

    def save_search(self, name: str, filters: dict, user_id: str = 'default') -> Optional[int]:
        """Speichert Suche"""
        try:
            with get_db() as session:
                search = SavedSearch(
                    user_id=user_id,
                    name=name,
                    filters=json.dumps(filters)
                )
                session.add(search)
                session.flush()
                return search.id
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Suche: {e}")
            return None

    def get_saved_searches(self, user_id: str = "default") -> List[dict]:
        """Lädt gespeicherte Suchen"""
        try:
            with get_db() as session:
                searches = session.query(SavedSearch).filter_by(user_id=user_id).order_by(desc(SavedSearch.created_at)).all()
                results = []
                for s in searches:
                    results.append({
                        'id': s.id,
                        'name': s.name,
                        'filters': json.loads(s.filters),
                        'created_at': s.created_at.isoformat()
                    })
                return results
        except Exception as e:
            logger.error(f"Fehler beim Laden der Suchen: {e}")
            return []

    def delete_saved_search(self, search_id: int) -> bool:
        """Löscht Suche"""
        try:
            with get_db() as session:
                s = session.get(SavedSearch, search_id)
                if s:
                    session.delete(s)
                    return True
                return False
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Suche: {e}")
            return False

    # --- Budgets & Stats ---

    def set_budget(self, category: str, month: str, amount: float) -> bool:
        """Setzt Budget"""
        try:
            with get_db() as session:
                budget = session.query(Budget).filter_by(category=category, month=month).first()
                if budget:
                    budget.budget_amount = amount
                else:
                    budget = Budget(category=category, month=month, budget_amount=amount)
                    session.add(budget)
                return True
        except Exception as e:
            logger.error(f"Fehler beim Setzen des Budgets: {e}")
            return False

    def get_budget(self, category: str, month: str) -> Optional[float]:
        """Holt Budget"""
        try:
            with get_db() as session:
                budget = session.query(Budget).filter_by(category=category, month=month).first()
                return budget.budget_amount if budget else None
        except Exception as e:
            logger.error(f"Fehler beim Laden des Budgets: {e}")
            return None

    def get_budget_status(self, category: str, month: str) -> dict:
        """Berechnet Budget-Status"""
        try:
            budget_amount = self.get_budget(category, month) or 0.0
            
            year, month_num = map(int, month.split('-'))
            
            with get_db() as session:
                import calendar
                _, last_day = calendar.monthrange(year, month_num)
                start_date = datetime(year, month_num, 1)
                end_date = datetime(year, month_num, last_day, 23, 59, 59)
                
                actual = session.query(func.sum(Document.amount)).filter(
                    Document.category == category,
                    Document.date_document >= start_date,
                    Document.date_document <= end_date
                ).scalar() or 0.0
                
                return {
                    "budget": budget_amount,
                    "actual": actual,
                    "remaining": budget_amount - actual,
                    "percent": (actual / budget_amount * 100) if budget_amount > 0 else 0
                }
        except Exception as e:
            logger.error(f"Fehler beim Budget-Status: {e}")
            return {"budget": 0, "actual": 0, "remaining": 0, "percent": 0}

    def get_monthly_expenses(self, year: int, month: int) -> dict:
        """Monatliche Ausgaben pro Kategorie"""
        try:
            import calendar
            _, last_day = calendar.monthrange(year, month)
            start_date = datetime(year, month, 1)
            end_date = datetime(year, month, last_day, 23, 59, 59)
            
            with get_db() as session:
                results = session.query(
                    Document.category, func.sum(Document.amount)
                ).filter(
                    Document.date_document >= start_date,
                    Document.date_document <= end_date,
                    Document.amount.isnot(None)
                ).group_by(Document.category).all()
                
                return {r[0]: r[1] for r in results}
        except Exception as e:
            logger.error(f"Fehler bei monatlichen Ausgaben: {e}")
            return {}

    def get_monthly_trends(self, year: int) -> dict:
        """Jahrestrends"""
        try:
            totals = {}
            with get_db() as session:
                for m in range(1, 13):
                    import calendar
                    _, last_day = calendar.monthrange(year, m)
                    start_date = datetime(year, m, 1)
                    end_date = datetime(year, m, last_day, 23, 59, 59)
                    
                    total = session.query(func.sum(Document.amount)).filter(
                        Document.date_document >= start_date,
                        Document.date_document <= end_date
                    ).scalar() or 0.0
                    
                    totals[m] = total
            return totals
        except Exception as e:
            logger.error(f"Fehler bei Trends: {e}")
            return {}

    def get_statistics(self) -> Dict:
        """Gesamtstatistiken"""
        try:
            with get_db() as session:
                total_docs = session.query(func.count(Document.id)).scalar()
                
                cat_counts = session.query(
                    Document.category, func.count(Document.id)
                ).group_by(Document.category).all()
                
                categories = {r[0]: r[1] for r in cat_counts}
                
                return {
                    'total_documents': total_docs,
                    'categories': categories,
                    'recent_uploads': []
                }
        except Exception as e:
            logger.error(f"Fehler bei Statistiken: {e}")
            return {'total_documents': 0, 'categories': {}}

    def log_audit_event(self, user_id: str, action: str, resource_id: Optional[str] = None, details: Optional[dict] = None):
        """Audit Log"""
        try:
            with get_db() as session:
                log = AuditLog(
                    user_id=user_id,
                    action=action,
                    document_id=int(resource_id) if resource_id and str(resource_id).isdigit() else None,
                    details=json.dumps(details) if details else None
                )
                session.add(log)
        except Exception as e:
            logger.error(f"Fehler beim Audit Log: {e}")

    def _doc_to_dict(self, doc: Document) -> dict:
        """Helper to convert Document model to dict"""
        try:
            keywords = json.loads(doc.keywords) if doc.keywords else []
        except:
            keywords = []
            
        tags = [{'id': t.id, 'name': t.name, 'color': t.color} for t in doc.tags]

        return {
            'id': doc.id,
            'filename': doc.filename,
            'filepath': doc.filepath,
            'category': doc.category,
            'subcategory': doc.subcategory,
            'date_document': doc.date_document.isoformat() if doc.date_document else None,
            'date_added': doc.date_added.isoformat() if doc.date_added else None,
            'summary': doc.summary,
            'keywords': keywords,
            'full_text': doc.full_text,
            'confidence': doc.ocr_confidence,
            'processing_time': doc.processing_time,
            'content_hash': doc.content_hash,
            'amount': doc.amount,
            'currency': doc.currency,
            'tags': tags
        }
