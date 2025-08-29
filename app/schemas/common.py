from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Optional
from datetime import datetime

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints"""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: Optional[str] = Field("asc", description="Sort order (asc/desc)")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    timestamp: datetime
    version: str
    database: str
    redis: str
    chroma: str


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class SuccessResponse(BaseModel):
    """Success response"""
    message: str
    data: Optional[dict] = None


class FilterParams(BaseModel):
    """Generic filter parameters"""
    search: Optional[str] = Field(None, description="Search term")
    filters: Optional[dict] = Field(None, description="Additional filters")
    date_from: Optional[datetime] = Field(None, description="Start date")
    date_to: Optional[datetime] = Field(None, description="End date")
