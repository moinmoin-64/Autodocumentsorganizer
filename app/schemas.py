from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field('#808080', pattern=r'^#[0-9a-fA-F]{6}$')

class TagCreate(TagBase):
    pass

class TagResponse(TagBase):
    id: int

class DocumentBase(BaseModel):
    filename: str
    category: str
    date_document: Optional[str] = None
    summary: Optional[str] = None

class DocumentResponse(DocumentBase):
    id: int
    upload_date: str
    file_path: str
    tags: List[TagResponse] = []
    
    class Config:
        from_attributes = True

class DocumentUpdate(BaseModel):
    filename: Optional[str] = None
    category: Optional[str] = None
    date_document: Optional[str] = None
    summary: Optional[str] = None

class SearchQuery(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = Field(100, ge=1, le=1000)

class StatsOverview(BaseModel):
    total_documents: int
    categories: Dict[str, int]
    recent_activity: List[Dict[str, Any]]

class PredictionResponse(BaseModel):
    category: str
    predictions: List[Dict[str, Any]]
