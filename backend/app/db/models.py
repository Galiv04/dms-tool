from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.base import Base

# Enums per il sistema
class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class ApprovalType(str, enum.Enum):
    ALL = "all"     # Tutti devono approvare
    ANY = "any"     # Basta uno che approva

class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class RecipientStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

# Modelli database
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    documents = relationship("Document", back_populates="owner")
    requested_approvals = relationship("ApprovalRequest", back_populates="requester")
    audit_logs = relationship("AuditLog", back_populates="user")

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size = Column(Float, nullable=False)
    file_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="documents")
    approval_requests = relationship("ApprovalRequest", back_populates="document")

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # NON created_by_id
    
    # Configurazione workflow
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    approval_type = Column(SQLEnum(ApprovalType), nullable=False, default=ApprovalType.ALL)
    
    # Stati e timing
    status = Column(SQLEnum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadati
    completion_reason = Column(String, nullable=True)
    requester_comments = Column(Text, nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="approval_requests")
    requester = relationship("User", back_populates="requested_approvals")
    recipients = relationship("ApprovalRecipient", back_populates="approval_request", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="approval_request")

    # Scheduler
    completion_notification_sent = Column(DateTime, nullable=True)
    
class ApprovalRecipient(Base):
    __tablename__ = "approval_recipients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    approval_request_id = Column(String, ForeignKey("approval_requests.id"), nullable=False)
    recipient_email = Column(String, nullable=False)
    recipient_name = Column(String, nullable=True)  # NON nel DB attuale
    
    # Token per approvazione
    approval_token = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))  # NON "token"
    
    # Stati e timing
    status = Column(SQLEnum(RecipientStatus), nullable=False, default=RecipientStatus.PENDING)
    responded_at = Column(DateTime(timezone=True), nullable=True)  # NON "reviewed_at"
    expires_at = Column(DateTime(timezone=True), nullable=True)  # NON nel DB attuale
    
    # Risposta
    decision = Column(String, nullable=True)  # NON nel DB attuale
    comments = Column(Text, nullable=True)  # NON "note"
    ip_address = Column(String, nullable=True)  # NON nel DB attuale
    user_agent = Column(String, nullable=True)  # NON nel DB attuale
    
    # Tracking email
    email_sent_at = Column(DateTime(timezone=True), nullable=True)  # NON nel DB attuale
    email_opened_at = Column(DateTime(timezone=True), nullable=True)  # NON nel DB attuale
    
    # Relationships
    approval_request = relationship("ApprovalRequest", back_populates="recipients")
    
    # Scheduler
    last_reminder_sent = Column(DateTime, nullable=True)
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    approval_request_id = Column(String, ForeignKey("approval_requests.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Azione e dettagli
    action = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)  # ← Nome corretto (non "metadata")
    
    # Tracking
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships  
    approval_request = relationship("ApprovalRequest", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")
