from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class VendorBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    vendor_type: Optional[str] = None
    rating: Optional[float] = None


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    vendor_type: Optional[str] = None
    rating: Optional[float] = None


class VendorResponse(VendorBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SOWBase(BaseModel):
    vendor_id: int
    project_id: int
    title: str
    description: Optional[str] = None
    total_value: float
    currency: str = "USD"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str = "draft"


class SOWCreate(SOWBase):
    pass


class SOWUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    total_value: Optional[float] = None
    currency: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None


class SOWResponse(SOWBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VendorListResponse(BaseModel):
    vendors: List[VendorResponse]
    total: int
    page: int
    size: int


class SOWListResponse(BaseModel):
    sows: List[SOWResponse]
    total: int
    page: int
    size: int
