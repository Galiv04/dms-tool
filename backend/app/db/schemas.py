from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.db.models import UserRole, ApprovalStatus, RecipientStatus


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    display_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)  # ← Fix Pydantic V2
    
    id: int
    role: UserRole
    created_at: datetime


# Document Schemas
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
    owner_id: int  # ← Aggiungi questo campo
    filename: str
    original_filename: str
    content_type: str
    size: float
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    message: str


# Approval Schemas
class ApprovalRecipientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # ← Fix Pydantic V2
    
    id: int
    recipient_email: str
    status: RecipientStatus
    reviewed_at: Optional[datetime]
    note: Optional[str]


class ApprovalRequestCreate(BaseModel):
    document_id: str
    recipients: List[EmailStr]


class ApprovalRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # ← Fix Pydantic V2
    
    id: str
    document_id: str
    status: ApprovalStatus
    created_at: datetime
    recipients: List[ApprovalRecipientResponse]


class ApprovalDecision(BaseModel):
    decision: str  # "approved" or "rejected"
    note: Optional[str] = None
