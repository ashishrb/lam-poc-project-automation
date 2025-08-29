from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, Float, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class VendorStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BLACKLISTED = "blacklisted"


class SOWStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"


class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    vendor_code = Column(String(50), unique=True, index=True)
    status = Column(Enum(VendorStatus), default=VendorStatus.ACTIVE)
    contact_person = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    tax_id = Column(String(50))
    payment_terms = Column(String(100))
    credit_limit = Column(Float)
    rating = Column(Float)  # 1-5 scale
    categories = Column(Text)  # JSON array of service categories
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    sows = relationship("SOW", back_populates="vendor")
    invoices = relationship("Invoice", back_populates="vendor")


class SOW(Base):
    __tablename__ = "sows"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(Enum(SOWStatus), default=SOWStatus.DRAFT)
    total_value = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    start_date = Column(Date)
    end_date = Column(Date)
    deliverables = Column(Text)  # JSON array of deliverables
    terms_conditions = Column(Text)
    payment_schedule = Column(Text)  # JSON payment milestones
    approved_by = Column(Integer, ForeignKey("users.id"))
    approval_date = Column(DateTime(timezone=True))
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    vendor = relationship("Vendor", back_populates="sows")
    project = relationship("Project")
    approver = relationship("User")
    tenant = relationship("Tenant")
    invoices = relationship("Invoice", back_populates="sow")


class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    sow_id = Column(Integer, ForeignKey("sows.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    invoice_number = Column(String(100), unique=True, index=True)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date)
    description = Column(Text)
    line_items = Column(Text)  # JSON array of invoice line items
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"))
    approval_date = Column(DateTime(timezone=True))
    payment_date = Column(DateTime(timezone=True))
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    vendor = relationship("Vendor", back_populates="invoices")
    sow = relationship("SOW", back_populates="invoices")
    project = relationship("Project")
    approver = relationship("User")
    tenant = relationship("Tenant")
