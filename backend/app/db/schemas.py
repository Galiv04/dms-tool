from datetime import datetime, timedelta
from app.utils.datetime_utils import get_utc_now, ensure_utc

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
import re

# Enum per Pydantic (devono corrispondere a quelli in models.py)
class ApprovalType(str, Enum):
    ALL = "all"
    ANY = "any"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class RecipientStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

# User Schemas (esistenti)
class UserBase(BaseModel):
    email: str
    display_name: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    display_name: Optional[str]
    role: UserRole
    created_at: datetime
    updated_at: Optional[datetime]

# Document Schemas (esistenti)
class DocumentBase(BaseModel):
    filename: str
    content_type: str
    size: float

class DocumentCreate(BaseModel):
    filename: str
    content_type: str

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    owner_id: int
    filename: str
    original_filename: str
    content_type: str
    size: float
    file_hash: str
    created_at: datetime
    updated_at: Optional[datetime]

class DocumentListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    owner_id: int
    filename: str
    original_filename: str
    content_type: str
    size: float
    created_at: datetime

class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    message: str

# Approval Schemas (aggiornati per coerenza)
class ApprovalRecipientBase(BaseModel):
    recipient_email: str = Field(..., description="Email del destinatario")
    recipient_name: Optional[str] = Field(None, description="Nome del destinatario")

    @field_validator('recipient_email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Formato email non valido')
        return v.lower().strip()

class ApprovalRecipientCreate(ApprovalRecipientBase):
    pass

class ApprovalRecipientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    recipient_email: str
    recipient_name: Optional[str]
    status: RecipientStatus
    responded_at: Optional[datetime]
    expires_at: Optional[datetime]
    decision: Optional[str]
    comments: Optional[str]
    email_sent_at: Optional[datetime]
    approval_token: str

class ApprovalRequestBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Titolo richiesta approvazione")
    description: Optional[str] = Field(None, max_length=2000, description="Descrizione dettagliata")
    approval_type: ApprovalType = Field(default=ApprovalType.ALL, description="Tipo approvazione: all o any")
    expires_at: Optional[datetime] = Field(None, description="Scadenza approvazione")
    requester_comments: Optional[str] = Field(None, max_length=1000, description="Commenti del richiedente")

class ApprovalRequestCreate(ApprovalRequestBase):
    document_id: str = Field(..., description="ID del documento da approvare")
    recipients: List[ApprovalRecipientCreate] = Field(..., min_length=1, description="Lista destinatari approvazione")
    
    @field_validator('expires_at')
    @classmethod
    def validate_expiry(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and ensure_utc(v) <= get_utc_now():  # 🔧 Fix: usa ensure_utc e get_utc_now
            raise ValueError("La data di scadenza deve essere nel futuro")
        return v
    
    @field_validator('recipients')
    @classmethod
    def validate_recipients(cls, v: List[ApprovalRecipientCreate]) -> List[ApprovalRecipientCreate]:
        if not v:
            raise ValueError('Almeno un destinatario è richiesto')
        
        if len(v) > 20:
            raise ValueError('Massimo 20 destinatari per richiesta')
        
        emails = [r.recipient_email for r in v]
        if len(emails) != len(set(emails)):
            raise ValueError('Email destinatari duplicate non consentite')
        
        return v

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        return v.strip()

class ApprovalRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    document_id: str
    requester_id: int
    title: str
    description: Optional[str]
    approval_type: ApprovalType
    status: ApprovalStatus
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]
    completed_at: Optional[datetime]
    completion_reason: Optional[str]
    requester_comments: Optional[str]
    recipients: List[ApprovalRecipientResponse] = []

class RequesterInfo(BaseModel):
    """Info base del richiedente per ApprovalRequestListResponse"""
    id: int
    email: str
    display_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class DocumentInfo(BaseModel):
    """Info base del documento per ApprovalRequestListResponse"""
    id: str
    filename: str
    original_filename: str
    content_type: str
    model_config = ConfigDict(from_attributes=True)

class RecipientInfo(BaseModel):
    """Info base del recipient per ApprovalRequestListResponse"""
    id: str
    recipient_email: str
    recipient_name: Optional[str] = None
    status: RecipientStatus
    
    model_config = ConfigDict(from_attributes=True)
    
class ApprovalRequestListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    document_id: str
    title: str
    approval_type: ApprovalType
    status: ApprovalStatus
    created_at: datetime
    expires_at: Optional[datetime]
    
    # Dati richiedente
    requester_id: int
    requester: Optional[RequesterInfo] = None
    
    # dati documento e recipients
    document: Optional[DocumentInfo] = None
    recipients: Optional[List[RecipientInfo]] = None
    
    recipient_count: Optional[int] = None
    approved_count: Optional[int] = None
    pending_count: Optional[int] = None

class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., description="Decisione: approved o rejected")
    comments: Optional[str] = Field(None, max_length=1000, description="Commenti sulla decisione")

    @field_validator('decision')
    @classmethod
    def validate_decision(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ['approved', 'rejected']:
            raise ValueError('Decisione deve essere "approved" o "rejected"')
        return v

    @field_validator('comments')
    @classmethod
    def validate_comments(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip()
        return v

class ApprovalDecisionResponse(BaseModel):
    message: str
    status: RecipientStatus
    approval_request_status: ApprovalStatus
    completed: bool

# Schemi per audit log
class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    action: str
    details: Optional[str]
    metadata_json: Optional[str]  # ← Coerente con models.py
    created_at: datetime
    user_id: Optional[int]
    ip_address: Optional[str]

# Schemi per dashboard e statistiche
class ApprovalDashboardStats(BaseModel):
    total_requests: int
    pending_requests: int
    approved_requests: int
    rejected_requests: int
    expired_requests: int
    my_pending_approvals: int

class ApprovalRequestUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    expires_at: Optional[datetime] = None
    requester_comments: Optional[str] = Field(None, max_length=1000)

    @field_validator('expires_at')
    @classmethod
    def validate_expiry(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v <= datetime.now():
            raise ValueError('La data di scadenza deve essere futura')
        return v

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip()
        return v

# Schema per email template
class EmailTemplate(BaseModel):
    recipient_email: str
    recipient_name: Optional[str]
    approval_request_title: str
    document_filename: str
    requester_name: str
    approval_token: str
    expires_at: Optional[datetime]
    approval_url: str

# Schema per bulk operations
class BulkApprovalAction(BaseModel):
    approval_request_ids: List[str] = Field(..., min_length=1, max_length=10)
    action: str = Field(..., description="Azione: cancel")
    reason: Optional[str] = Field(None, max_length=500)

    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ['cancel']:
            raise ValueError('Azione non supportata')
        return v

    @field_validator('approval_request_ids')
    @classmethod
    def validate_ids(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError('Almeno un ID richiesta è necessario')
        if len(v) > 10:
            raise ValueError('Massimo 10 richieste per operazione bulk')
        return v

