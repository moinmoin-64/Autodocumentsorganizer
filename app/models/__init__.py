"""
SQLAlchemy Models
ORM-Modelle für alle Datenbank-Tabellen
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Table, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# Association Table für Tags
document_tags = Table(
    'document_tags',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'))
)

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(500), nullable=False)
    filepath = Column(String(1000), nullable=False, unique=True)
    category = Column(String(100))
    subcategory = Column(String(100))
    date_document = Column(DateTime)
    date_added = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text)
    keywords = Column(Text) # Stored as JSON string
    full_text = Column(Text)
    ocr_confidence = Column(Float)
    processing_time = Column(Float)
    content_hash = Column(String(64))
    amount = Column(Float)
    currency = Column(String(10))
    
    # Relationships
    tags = relationship('Tag', secondary=document_tags, back_populates='documents')
    audit_logs = relationship('AuditLog', back_populates='document', cascade="all, delete-orphan")

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    color = Column(String(7))  # Hex color
    created_at = Column(DateTime, default=datetime.utcnow)
    
    documents = relationship('Document', secondary=document_tags, back_populates='tags')

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(100))
    action = Column(String(50))
    document_id = Column(Integer, ForeignKey('documents.id'))
    details = Column(Text) # JSON string
    
    document = relationship('Document', back_populates='audit_logs')

class SavedSearch(Base):
    __tablename__ = 'saved_searches'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), default='default')
    name = Column(String(200), nullable=False)
    query = Column(Text)
    filters = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

class Budget(Base):
    __tablename__ = 'budgets'

    id = Column(Integer, primary_key=True)
    category = Column(String(100), nullable=False)
    month = Column(String(7), nullable=False) # YYYY-MM
    budget_amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
