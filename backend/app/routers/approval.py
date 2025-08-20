from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session, joinedload

from app.db.base import get_db
from app.db.schemas import (
    ApprovalRequestCreate, ApprovalRequestResponse, ApprovalRequestListResponse,
    ApprovalDecisionRequest, ApprovalDecisionResponse, ApprovalDashboardStats,
    UserResponse, ApprovalRequestListResponse
)
from app.db.models import User, ApprovalStatus, Document, ApprovalRecipient, ApprovalRequest, RecipientStatus
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

# ===== ENDPOINTS PER MODAL CREAZIONE APPROVAZIONI =====


@router.get("/users", response_model=List[UserResponse])
async def get_available_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[UserResponse]:
    """
    Ottieni lista utenti disponibili per assegnare approvazioni
    Esclude l'utente corrente dalla lista
    """
    users = db.query(User).filter(
        User.id != current_user.id  # Escludi l'utente corrente
    ).all()
    return users


@router.get("/documents", response_model=List[dict])
async def get_user_documents_for_approval(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    Ottieni documenti dell'utente corrente disponibili per creare approvazioni
    """
    documents = db.query(Document).filter(
        Document.owner_id == current_user.id
    ).all()

    return [
        {
            "id": doc.id,
            "filename": doc.original_filename,
            "content_type": doc.content_type,
            "size": doc.size,
            "created_at": doc.created_at.isoformat()
        }
        for doc in documents
    ]


@router.post("/validate", response_model=dict)
async def validate_approval_data(
    request_data: ApprovalRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Valida i dati per creazione approvazione senza effettivamente crearla
    Utile per validazione real-time nel frontend
    """
    try:
        # Verifica che il documento esista e appartenga all'utente
        document = db.query(Document).filter(
            Document.id == request_data.document_id,
            Document.owner_id == current_user.id
        ).first()

        if not document:
            return {
                "valid": False,
                "errors": ["Document not found or not owned by user"]
            }

        # Verifica che le email dei destinatari siano valide (già validato da Pydantic)
        recipient_emails = [r.recipient_email for r in request_data.recipients]

        # Verifica duplicati (già validato da Pydantic, ma double-check)
        if len(recipient_emails) != len(set(recipient_emails)):
            return {
                "valid": False,
                "errors": ["Duplicate recipient emails found"]
            }

        return {
            "valid": True,
            "document_name": document.original_filename,
            "recipient_count": len(request_data.recipients),
            "approval_type": request_data.approval_type.value
        }

    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"]
        }

# ===== ENDPOINTS CORE APPROVAZIONI =====


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
    status_filter: Optional[ApprovalStatus] = Query(
        None, description="Filtra per stato"),
    limit: int = Query(
        50, ge=1, le=100, description="Numero massimo risultati"),
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


@router.get("/for-me", response_model=List[ApprovalRequestListResponse])
async def get_approval_requests_for_me(
    current_user: User = Depends(get_current_user),
    approval_service: ApprovalService = Depends(get_approval_service)
) -> List[ApprovalRequestListResponse]:
    """
    Lista le richieste di approvazione dove l'utente corrente è destinatario
    """
    # Query per trovare ApprovalRecipient con la tua email
    recipients = approval_service.db.query(ApprovalRecipient)\
        .options(
            joinedload(ApprovalRecipient.approval_request)
        .joinedload(ApprovalRequest.document),
            joinedload(ApprovalRecipient.approval_request)
        .joinedload(ApprovalRequest.requester)
    )\
        .filter(ApprovalRecipient.recipient_email == current_user.email)\
        .all()

    # Estrai le approval_requests uniche
    approval_requests = []
    seen_ids = set()

    for recipient in recipients:
        req = recipient.approval_request
        if req and req.id not in seen_ids:
            seen_ids.add(req.id)
            approval_requests.append(req)

    # Converti in ApprovalRequestListResponse usando la logica esistente
    result = []
    for req in approval_requests:
        recipients_data = req.recipients
        approved_count = len(
            [r for r in recipients_data if r.status == RecipientStatus.APPROVED])
        pending_count = len(
            [r for r in recipients_data if r.status == RecipientStatus.PENDING])

        req_dict = {
            "id": req.id,
            "document_id": req.document_id,
            "title": req.title,
            "approval_type": req.approval_type,
            "status": req.status,
            "created_at": req.created_at,
            "expires_at": req.expires_at,
            "requester_id": req.requester_id,
            "recipient_count": len(recipients_data),
            "approved_count": approved_count,
            "pending_count": pending_count
        }

        # Aggiungi dati requester
        if req.requester:
            req_dict["requester"] = {
                "id": req.requester.id,
                "email": req.requester.email,
                "display_name": req.requester.display_name
            }

        # Aggiungi dati documento
        if req.document:
            req_dict["document"] = {
                "id": req.document.id,
                "filename": req.document.filename,
                "original_filename": req.document.original_filename,
                "content_type": req.document.content_type
            }

        # Aggiungi dati recipients
        if recipients_data:
            req_dict["recipients"] = [
                {
                    "id": r.id,
                    "recipient_email": r.recipient_email,
                    "recipient_name": r.recipient_name,
                    "status": r.status,
                    "approval_token": r.approval_token,
                    "comments": r.comments,  # 🆕 AGGIUNGI QUESTO
                    "responded_at": r.responded_at,  # Bonus: anche timestamp
                    "decision": r.decision  # Bonus: anche decisione
                }
                for r in recipients_data
            ]

        result.append(ApprovalRequestListResponse.model_validate(req_dict))

    return result


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

# ===== GESTIONE APPROVAZIONI =====

# Aggiungi schema per il body della cancellazione


class CancelApprovalRequest(BaseModel):
    reason: Optional[str] = None


@router.post("/{request_id}/cancel")
async def cancel_approval_request(
    request_id: str,
    request: Request,
    cancel_data: CancelApprovalRequest = CancelApprovalRequest(),
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
            reason=cancel_data.reason,
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


@router.post("/decide/{approval_token}")
async def decide_approval(approval_token: str, decision: ApprovalDecisionRequest, db: Session = Depends(get_db)):
    recipient = db.query(ApprovalRecipient).filter_by(
        approval_token=approval_token).first()
    if not recipient or recipient.status != 'pending':
        raise HTTPException(...)
    recipient.status = decision.decision  # "approved" or "rejected"
    recipient.comments = decision.comments
    recipient.responded_at = datetime.now()
    # Avanza anche lo stato globale se necessario ...
    db.commit()


@router.post("/submit/{approval_token}", response_model=ApprovalDecisionResponse)
async def submit_approval_decision(
    approval_token: str,
    decision_data: ApprovalDecisionRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Submit approval decision using token"""
    try:
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent")

        approval_service = ApprovalService(db)
        result = approval_service.process_approval_decision(
            approval_token=approval_token,
            decision_data=decision_data,
            client_ip=client_ip,
            user_agent=user_agent
        )

        return ApprovalDecisionResponse(
            message=result["message"],
            status=result["recipient_status"],
            approval_request_status=result["approval_request_status"],
            completed=result["completed"]
        )

    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore server: {str(e)}")


# ===== DASHBOARD E STATISTICHE =====


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

# ===== UTILITY E INFO =====


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

        recipient = approval_service.db.query(ApprovalRecipient).filter(
            ApprovalRecipient.approval_token == approval_token
        ).first()

        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token di approvazione non valido"
            )

        # Verifica scadenza
        is_expired = (
            recipient.expires_at and recipient.expires_at < datetime.now())
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


@router.delete("/{approval_id}", response_model=Dict[str, str])
def delete_approval_request(
    approval_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Elimina una richiesta di approvazione
    Solo il richiedente può eliminare le proprie richieste PENDING
    """
    approval_service = ApprovalService(db)

    try:
        result = approval_service.delete_approval_request(
            approval_id,
            current_user.id,
            request.client.host if request and hasattr(
                request, 'client') else None
        )
        return result

    except NotFoundError:
        raise HTTPException(
            status_code=404, detail="Approval request not found")
    except PermissionDeniedError:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this approval request")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
