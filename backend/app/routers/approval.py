from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.schemas import (
    ApprovalRequestCreate, ApprovalRequestResponse, ApprovalRequestListResponse,
    ApprovalDecisionRequest, ApprovalDecisionResponse, ApprovalDashboardStats
)
from app.db.models import User, ApprovalStatus
from app.services.approval import ApprovalService
from app.utils.security import get_current_user
from app.utils.exceptions import NotFoundError, ValidationError, PermissionDeniedError
from pydantic import BaseModel

router = APIRouter(prefix="/approvals", tags=["approvals"])

def get_approval_service(db: Session = Depends(get_db)) -> ApprovalService:
    """Dependency per ottenere il service approvazioni"""
    return ApprovalService(db)

def get_client_info(request: Request) -> Dict[str, str]:
    """Estrae informazioni client per audit logging"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent")
    }

@router.post("/", response_model=ApprovalRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_approval_request(
    request_data: ApprovalRequestCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    approval_service: ApprovalService = Depends(get_approval_service)
) -> ApprovalRequestResponse:
    """
    Crea una nuova richiesta di approvazione
    
    - **document_id**: ID del documento da approvare
    - **title**: Titolo della richiesta
    - **description**: Descrizione opzionale
    - **approval_type**: "all" (tutti devono approvare) o "any" (basta uno)
    - **recipients**: Lista destinatari con email e nome
    - **expires_at**: Data scadenza opzionale
    - **requester_comments**: Commenti del richiedente
    """
    try:
        client_info = get_client_info(request)
        
        response = approval_service.create_approval_request(
            request_data=request_data,
            requester_id=current_user.id,
            client_ip=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        return response
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[ApprovalRequestListResponse])
async def list_approval_requests(
    status_filter: Optional[ApprovalStatus] = Query(None, description="Filtra per stato"),
    limit: int = Query(50, ge=1, le=100, description="Numero massimo risultati"),
    offset: int = Query(0, ge=0, description="Offset per paginazione"),
    current_user: User = Depends(get_current_user),
    approval_service: ApprovalService = Depends(get_approval_service)
) -> List[ApprovalRequestListResponse]:
    """
    Lista le richieste di approvazione dell'utente autenticato
    
    - **status_filter**: Filtra per stato (pending, approved, rejected, cancelled)
    - **limit**: Numero massimo di risultati (1-100)
    - **offset**: Offset per paginazione
    """
    return approval_service.list_approval_requests(
        user_id=current_user.id,
        status_filter=status_filter,
        limit=limit,
        offset=offset
    )

@router.get("/{request_id}", response_model=ApprovalRequestResponse)
async def get_approval_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    approval_service: ApprovalService = Depends(get_approval_service)
) -> ApprovalRequestResponse:
    """
    Recupera i dettagli di una richiesta di approvazione specifica
    
    - **request_id**: ID della richiesta di approvazione
    """
    try:
        return approval_service.get_approval_request(
            request_id=request_id,
            user_id=current_user.id
        )
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

# Aggiungi schema per il body della cancellazione
class CancelApprovalRequest(BaseModel):
    reason: Optional[str] = None

@router.post("/{request_id}/cancel")
async def cancel_approval_request(
    request_id: str,
    request: Request,
    cancel_data: CancelApprovalRequest = CancelApprovalRequest(),  # ← Body JSON opzionale
    current_user: User = Depends(get_current_user),
    approval_service: ApprovalService = Depends(get_approval_service)
) -> Dict[str, str]:
    """
    Cancella una richiesta di approvazione (solo se PENDING)
    
    - **request_id**: ID della richiesta da cancellare
    - **reason**: Motivo opzionale della cancellazione (nel body JSON)
    """
    try:
        client_info = get_client_info(request)
        
        return approval_service.cancel_approval_request(
            request_id=request_id,
            user_id=current_user.id,
            reason=cancel_data.reason,  # ← Usa reason dal body
            client_ip=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/decide/{approval_token}", response_model=ApprovalDecisionResponse)
async def process_approval_decision(
    approval_token: str,
    decision_data: ApprovalDecisionRequest,
    request: Request,
    approval_service: ApprovalService = Depends(get_approval_service)
) -> ApprovalDecisionResponse:
    """
    Processa una decisione di approvazione tramite token
    QUESTO ENDPOINT NON RICHIEDE AUTENTICAZIONE (token-based)
    
    - **approval_token**: Token univoco del destinatario
    - **decision**: "approved" o "rejected"
    - **comments**: Commenti opzionali sulla decisione
    """
    try:
        client_info = get_client_info(request)
        
        result = approval_service.process_approval_decision(
            approval_token=approval_token,
            decision_data=decision_data,
            client_ip=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        # Converti il risultato del service in schema Pydantic
        return ApprovalDecisionResponse(
            message=result["message"],
            status=result["recipient_status"],
            approval_request_status=result["approval_request_status"],
            completed=result["completed"]
        )
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/dashboard/pending")
async def get_pending_approvals_dashboard(
    email: str = Query(..., description="Email del destinatario"),
    approval_service: ApprovalService = Depends(get_approval_service)
) -> List[Dict[str, Any]]:
    """
    Dashboard per destinatari: recupera tutte le approvazioni pending per un email
    QUESTO ENDPOINT NON RICHIEDE AUTENTICAZIONE (per link email)
    
    - **email**: Email del destinatario per cui recuperare le approvazioni pending
    """
    return approval_service.get_pending_approvals_for_email(email)

@router.get("/dashboard/stats", response_model=ApprovalDashboardStats)
async def get_approval_statistics(
    current_user: User = Depends(get_current_user),
    approval_service: ApprovalService = Depends(get_approval_service)
) -> ApprovalDashboardStats:
    """
    Statistiche dashboard approvazioni per l'utente autenticato
    
    Restituisce contatori per:
    - Richieste create dall'utente (per stato)
    - Approvazioni pending per l'utente come destinatario
    """
    stats = approval_service.get_approval_statistics(current_user.id)
    
    return ApprovalDashboardStats(
        total_requests=sum([
            stats.get("requested_pending", 0),
            stats.get("requested_approved", 0),
            stats.get("requested_rejected", 0),
            stats.get("requested_cancelled", 0)
        ]),
        pending_requests=stats.get("requested_pending", 0),
        approved_requests=stats.get("requested_approved", 0),
        rejected_requests=stats.get("requested_rejected", 0),
        expired_requests=0,  # TODO: Implementare logica per expired
        my_pending_approvals=stats.get("pending_as_recipient", 0)
    )

@router.get("/token/{approval_token}/info")
async def get_approval_token_info(
    approval_token: str,
    approval_service: ApprovalService = Depends(get_approval_service)
) -> Dict[str, Any]:
    """
    Recupera informazioni su un token di approvazione senza processare decisioni
    Utile per preview prima della decisione
    QUESTO ENDPOINT NON RICHIEDE AUTENTICAZIONE
    
    - **approval_token**: Token di approvazione da verificare
    """
    try:
        # Utilizza metodo interno del service per ottenere info del token
        from app.db.models import ApprovalRecipient
        from datetime import datetime
        
        recipient = approval_service.db.query(ApprovalRecipient).filter(
            ApprovalRecipient.approval_token == approval_token
        ).first()
        
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token di approvazione non valido"
            )
        
        # Verifica scadenza
        is_expired = (recipient.expires_at and recipient.expires_at < datetime.now())
        has_responded = recipient.status.value != "pending"
        
        approval_request = recipient.approval_request
        document = approval_request.document
        
        return {
            "valid": not is_expired and not has_responded,
            "expired": is_expired,
            "already_responded": has_responded,
            "current_status": recipient.status.value,
            "approval_request": {
                "id": approval_request.id,
                "title": approval_request.title,
                "description": approval_request.description,
                "approval_type": approval_request.approval_type.value,
                "requester_name": approval_request.requester.display_name or approval_request.requester.email,
                "requester_comments": approval_request.requester_comments,
                "created_at": approval_request.created_at,
                "expires_at": recipient.expires_at
            },
            "document": {
                "id": document.id,
                "filename": document.original_filename,
                "content_type": document.content_type,
                "size": document.size
            },
            "recipient": {
                "email": recipient.recipient_email,
                "name": recipient.recipient_name,
                "responded_at": recipient.responded_at,
                "comments": recipient.comments
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nel recupero informazioni token: {str(e)}"
        )

@router.get("/audit/{request_id}")
async def get_approval_audit_trail(
    request_id: str,
    current_user: User = Depends(get_current_user),
    approval_service: ApprovalService = Depends(get_approval_service)
) -> List[Dict[str, Any]]:
    """
    Recupera l'audit trail completo di una richiesta di approvazione
    Solo per il richiedente o amministratori
    
    - **request_id**: ID della richiesta di approvazione
    """
    try:
        # Verifica che l'utente possa accedere alla richiesta
        approval_request = approval_service.get_approval_request(
            request_id=request_id,
            user_id=current_user.id
        )
        
        # Recupera audit logs
        from app.db.models import AuditLog
        audit_logs = approval_service.db.query(AuditLog).filter(
            AuditLog.approval_request_id == request_id
        ).order_by(AuditLog.created_at.desc()).all()
        
        return [
            {
                "id": log.id,
                "action": log.action,
                "details": log.details,
                "user_id": log.user_id,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at,
                "metadata": log.metadata_json
            }
            for log in audit_logs
        ]
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
