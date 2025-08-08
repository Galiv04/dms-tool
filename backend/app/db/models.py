from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.base import Base


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELED = "canceled"


class RecipientStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    documents = relationship("Document", back_populates="owner")
    approval_requests_created = relationship("ApprovalRequest", back_populates="created_by")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size = Column(Float, nullable=False)  # Size in bytes
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("User", back_populates="documents")
    approval_requests = relationship("ApprovalRequest", back_populates="document")


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="approval_requests")
    created_by = relationship("User", back_populates="approval_requests_created")
    recipients = relationship("ApprovalRecipient", back_populates="approval_request")


class ApprovalRecipient(Base):
    __tablename__ = "approval_recipients"

    id = Column(Integer, primary_key=True, index=True)
    approval_request_id = Column(String, ForeignKey("approval_requests.id"), nullable=False)
    recipient_email = Column(String, nullable=False)
    status = Column(Enum(RecipientStatus), default=RecipientStatus.PENDING)
    token = Column(String, unique=True, nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    note = Column(Text, nullable=True)

    # Relationships
    approval_request = relationship("ApprovalRequest", back_populates="recipients")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)  # "document", "approval_request", etc.
    entity_id = Column(String, nullable=False)
    action = Column(String, nullable=False)  # "create", "upload", "approve", "reject"
    payload_json = Column(Text, nullable=True)  # JSON serialized data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
