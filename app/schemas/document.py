from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    document_type: str
    status: str = "draft"
    file_path: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    project_id: Optional[int] = None
    tags: Optional[List[str]] = None
    sensitivity_level: str = "public"


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    document_type: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    sensitivity_level: Optional[str] = None


class DocumentResponse(DocumentBase):
    id: int
    uploaded_by: int
    tenant_id: int
    embedding_status: str
    last_processed: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentChunkBase(BaseModel):
    chunk_index: int
    content: str
    content_hash: str
    embedding_id: Optional[str] = None
    page_number: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None


class DocumentChunkCreate(DocumentChunkBase):
    document_id: int


class DocumentChunkResponse(DocumentChunkBase):
    id: int
    document_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    size: int
