import uuid
import json
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.models import (
    ApprovalRequest, ApprovalRecipient, AuditLog, Document, User,
    ApprovalType, ApprovalStatus, RecipientStatus
)
from app.db.schemas import (
    ApprovalRequestCreate, ApprovalDecisionRequest,
    ApprovalRequestResponse, ApprovalRequestListResponse
)
from app.utils.exceptions import ValidationError, NotFoundError, PermissionDeniedError
from app.services.email import EmailService


class ApprovalService:
    """Service per la gestione completa del workflow di approvazione"""

    def __init__(self, db: Session):
        self.db = db

    def create_approval_request(
        self,
        request_data: ApprovalRequestCreate,
        requester_id: int,
        client_ip: str = None,
        user_agent: str = None
    ) -> ApprovalRequestResponse:
        """
        Crea una nuova richiesta di approvazione con destinatari
        
        Args:
            request_data: Dati della richiesta di approvazione
            requester_id: ID dell'utente che fa la richiesta
            client_ip: IP del client per audit
            user_agent: User agent per audit
        
        Returns:
            ApprovalRequestResponse: Richiesta di approvazione creata
            
        Raises:
            NotFoundError: Se il documento non esiste o non appartiene al richiedente
            ValidationError: Se i dati non sono validi
        """
        # Verifica che il documento esista e appartenga al richiedente
        document = self.db.query(Document).filter(
            Document.id == request_data.document_id,
            Document.owner_id == requester_id
        ).first()

        if not document:
            raise NotFoundError(
                f"Documento {request_data.document_id} non trovato o non autorizzato")

        # Verifica che non ci siano già richieste PENDING per questo documento
        existing_pending = self.db.query(ApprovalRequest).filter(
            ApprovalRequest.document_id == request_data.document_id,
            ApprovalRequest.status == ApprovalStatus.PENDING
        ).first()

        if existing_pending:
            raise ValidationError(
                f"Esiste già una richiesta di approvazione in corso per questo documento"
            )

        # Crea la richiesta di approvazione
        approval_request = ApprovalRequest(
            document_id=request_data.document_id,
            requester_id=requester_id,
            title=request_data.title,
            description=request_data.description,
            approval_type=request_data.approval_type,
            expires_at=request_data.expires_at,
            requester_comments=request_data.requester_comments
        )

        self.db.add(approval_request)
        self.db.commit()
        self.db.refresh(approval_request)

        # Crea i destinatari
        recipients = []
        for recipient_data in request_data.recipients:
            recipient = ApprovalRecipient(
                approval_request_id=approval_request.id,
                recipient_email=recipient_data.recipient_email,
                recipient_name=recipient_data.recipient_name,
                expires_at=request_data.expires_at  # Stessa scadenza della richiesta
            )
            recipients.append(recipient)

        self.db.add_all(recipients)
        self.db.commit()

        # Refresh per caricare i recipients
        self.db.refresh(approval_request)

        # Crea audit log
        self._create_audit_log(
            approval_request_id=approval_request.id,
            user_id=requester_id,
            action="approval_request_created",
            details=f"Richiesta di approvazione creata: '{request_data.title}'",
            metadata={
                "document_id": request_data.document_id,
                "document_filename": document.filename,
                "approval_type": request_data.approval_type.value,
                "recipients_count": len(recipients),
                "expires_at": request_data.expires_at.isoformat() if request_data.expires_at else None
            },
            ip_address=client_ip,
            user_agent=user_agent
        )

        # Audit log per ogni destinatario
        recipient_emails = [r.recipient_email for r in recipients]
        self._create_audit_log(
            approval_request_id=approval_request.id,
            user_id=requester_id,
            action="recipients_added",
            details=f"Aggiunti {len(recipients)} destinatari alla richiesta",
            metadata={
                "recipients": recipient_emails,
                "tokens_generated": [r.approval_token for r in recipients]
            },
            ip_address=client_ip,
            user_agent=user_agent
        )

        return ApprovalRequestResponse.model_validate(approval_request)

    def process_approval_decision(
        self,
        approval_token: str,
        decision_data: ApprovalDecisionRequest,
        client_ip: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        Processa una decisione di approvazione tramite token
        
        Args:
            approval_token: Token univoco del destinatario
            decision_data: Decisione (approved/rejected) e commenti
            client_ip: IP del client per audit
            user_agent: User agent per audit
        
        Returns:
            Dict con stato della decisione e stato finale della richiesta
            
        Raises:
            NotFoundError: Se il token non esiste
            ValidationError: Se il token è scaduto o già utilizzato
        """
        # Trova il recipient tramite token
        recipient = self.db.query(ApprovalRecipient).filter(
            ApprovalRecipient.approval_token == approval_token
        ).first()

        if not recipient:
            raise NotFoundError("Token di approvazione non valido")

        # Verifica che il token non sia scaduto
        if recipient.expires_at and recipient.expires_at < datetime.now():
            recipient.status = RecipientStatus.EXPIRED
            self.db.commit()
            raise ValidationError("Il token di approvazione è scaduto")

        # Verifica che non abbia già risposto
        if recipient.status != RecipientStatus.PENDING:
            raise ValidationError(
                f"Hai già risposto a questa richiesta (stato: {recipient.status.value})")

        # Aggiorna il recipient con la decisione
        recipient.status = (
            RecipientStatus.APPROVED if decision_data.decision == "approved"
            else RecipientStatus.REJECTED
        )
        recipient.decision = decision_data.decision
        recipient.comments = decision_data.comments
        recipient.responded_at = datetime.now()
        recipient.ip_address = client_ip
        recipient.user_agent = user_agent

        self.db.commit()

        # Carica la approval request
        approval_request = recipient.approval_request

        # Crea audit log per la decisione
        self._create_audit_log(
            approval_request_id=approval_request.id,
            user_id=None,  # Decisione esterna, non da utente autenticato
            action=f"recipient_{decision_data.decision}",
            details=f"Destinatario {recipient.recipient_email} ha {decision_data.decision} la richiesta",
            metadata={
                "recipient_email": recipient.recipient_email,
                "recipient_name": recipient.recipient_name,
                "decision": decision_data.decision,
                "comments": decision_data.comments,
                "token": approval_token
            },
            ip_address=client_ip,
            user_agent=user_agent
        )

        # Controlla se la richiesta è completata e aggiorna lo stato
        final_status, completion_reason = self._evaluate_approval_request_status(
            approval_request)

        response_data = {
            "message": f"Decisione '{decision_data.decision}' registrata con successo",
            "recipient_status": recipient.status,
            "recipient_email": recipient.recipient_email,
            "approval_request_id": approval_request.id,
            "approval_request_title": approval_request.title,
            "approval_request_status": final_status,
            "completed": final_status != ApprovalStatus.PENDING
        }

        if final_status != ApprovalStatus.PENDING:
            response_data["completion_reason"] = completion_reason

        return response_data

    def get_approval_request(self, request_id: str, user_id: int = None) -> ApprovalRequestResponse:
        """
        Recupera una richiesta di approvazione con tutti i dettagli
        
        Args:
            request_id: ID della richiesta
            user_id: ID utente per controlli di autorizzazione (opzionale)
        
        Returns:
            ApprovalRequestResponse: Richiesta completa
            
        Raises:
            NotFoundError: Se la richiesta non esiste
            PermissionDeniedError: Se l'utente non è autorizzato
        """
        approval_request = self.db.query(ApprovalRequest).filter(
            ApprovalRequest.id == request_id
        ).first()

        if not approval_request:
            raise NotFoundError(
                f"Richiesta di approvazione {request_id} non trovata")

        # Controllo autorizzazione (solo il richiedente può vedere tutti i dettagli)
        if user_id and approval_request.requester_id != user_id:
            # TODO: Implementare logica per admin o destinatari che possono vedere dettagli limitati
            raise PermissionDeniedError(
                "Non sei autorizzato a visualizzare questa richiesta")

        return ApprovalRequestResponse.model_validate(approval_request)

    def list_approval_requests(
        self,
        user_id: int,
        status_filter: Optional[ApprovalStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ApprovalRequestListResponse]:
        """
        Lista le richieste di approvazione dell'utente
        
        Args:
            user_id: ID dell'utente richiedente
            status_filter: Filtro opzionale per stato
            limit: Numero massimo di risultati
            offset: Offset per paginazione
        
        Returns:
            List[ApprovalRequestListResponse]: Lista richieste
        """
        query = self.db.query(ApprovalRequest).filter(
            ApprovalRequest.requester_id == user_id
        )

        if status_filter:
            query = query.filter(ApprovalRequest.status == status_filter)

        query = query.order_by(ApprovalRequest.created_at.desc())
        query = query.offset(offset).limit(limit)

        requests = query.all()

        # Aggiungi contatori per ogni richiesta
        result = []
        for req in requests:
            req_data = ApprovalRequestListResponse.model_validate(req)

            # Calcola contatori
            recipients = req.recipients
            req_data.recipient_count = len(recipients)
            req_data.approved_count = len(
                [r for r in recipients if r.status == RecipientStatus.APPROVED])
            req_data.pending_count = len(
                [r for r in recipients if r.status == RecipientStatus.PENDING])

            result.append(req_data)

        return result

    def cancel_approval_request(
        self,
        request_id: str,
        user_id: int,
        reason: str = None,
        client_ip: str = None,
        user_agent: str = None
    ) -> Dict[str, str]:
        """
        Cancella una richiesta di approvazione (solo se PENDING)
        
        Args:
            request_id: ID della richiesta
            user_id: ID dell'utente (deve essere il richiedente)
            reason: Motivo della cancellazione
            client_ip: IP per audit
            user_agent: User agent per audit
        
        Returns:
            Dict con messaggio di conferma
            
        Raises:
            NotFoundError: Se la richiesta non esiste
            PermissionDeniedError: Se l'utente non è il richiedente
            ValidationError: Se la richiesta non è più cancellabile
        """
        approval_request = self.db.query(ApprovalRequest).filter(
            ApprovalRequest.id == request_id
        ).first()

        if not approval_request:
            raise NotFoundError(
                f"Richiesta di approvazione {request_id} non trovata")

        if approval_request.requester_id != user_id:
            raise PermissionDeniedError(
                "Non sei autorizzato a cancellare questa richiesta")

        if approval_request.status != ApprovalStatus.PENDING:
            raise ValidationError(
                f"Non è possibile cancellare una richiesta in stato {approval_request.status.value}")

        # Aggiorna stato richiesta
        approval_request.status = ApprovalStatus.CANCELLED
        approval_request.completed_at = datetime.now()
        approval_request.completion_reason = "cancelled_by_requester"

        # Segna tutti i recipients come expired
        for recipient in approval_request.recipients:
            if recipient.status == RecipientStatus.PENDING:
                recipient.status = RecipientStatus.EXPIRED

        self.db.commit()

        # Audit log
        self._create_audit_log(
            approval_request_id=approval_request.id,
            user_id=user_id,
            action="approval_request_cancelled",
            details=f"Richiesta di approvazione cancellata dal richiedente",
            metadata={
                "reason": reason or "No reason provided",
                "cancelled_recipients": len([r for r in approval_request.recipients if r.status == RecipientStatus.EXPIRED])
            },
            ip_address=client_ip,
            user_agent=user_agent
        )

        return {
            "message": f"Richiesta di approvazione '{approval_request.title}' cancellata con successo",
            "request_id": request_id,
            "status": approval_request.status.value
        }

    def get_pending_approvals_for_email(self, email: str) -> List[Dict[str, Any]]:
        """
        Recupera tutte le richieste di approvazione in attesa per un email
        Utile per dashboard destinatari e notifiche
        
        Args:
            email: Email del destinatario
        
        Returns:
            List[Dict]: Lista richieste pending per questo email
        """
        pending_recipients = self.db.query(ApprovalRecipient).filter(
            ApprovalRecipient.recipient_email == email,
            ApprovalRecipient.status == RecipientStatus.PENDING
        ).all()

        results = []
        expired_recipients = []  # Colleziona recipients scaduti per batch update

        for recipient in pending_recipients:
            request = recipient.approval_request
            document = request.document

            # Controlla scadenza
            is_expired = (
                recipient.expires_at and recipient.expires_at < datetime.now())
            if is_expired:
                # Non aggiornare immediatamente, raccoglie per batch update
                expired_recipients.append(recipient)
                continue

            results.append({
                "approval_request_id": request.id,
                "title": request.title,
                "description": request.description,
                "requester_name": request.requester.display_name or request.requester.email,
                "document_filename": document.original_filename,
                "document_id": document.id,
                "approval_type": request.approval_type.value,
                "created_at": request.created_at,
                "expires_at": recipient.expires_at,
                "approval_token": recipient.approval_token,
                "recipient_name": recipient.recipient_name,
                "requester_comments": request.requester_comments
            })

        # Batch update dei recipients scaduti alla fine
        if expired_recipients:
            for recipient in expired_recipients:
                recipient.status = RecipientStatus.EXPIRED

            try:
                self.db.commit()

                # Audit log per recipients scaduti
                for recipient in expired_recipients:
                    self._create_audit_log(
                        approval_request_id=recipient.approval_request_id,
                        user_id=None,
                        action="recipient_expired",
                        details=f"Recipient {recipient.recipient_email} scaduto automaticamente",
                        metadata={
                            "recipient_email": recipient.recipient_email,
                            "expired_at": datetime.now().isoformat(),
                            "original_expires_at": recipient.expires_at.isoformat() if recipient.expires_at else None
                        }
                    )
            except Exception as e:
                self.db.rollback()
                # Log dell'errore ma non bloccare l'operazione principale
                print(
                    f"Warning: Errore durante aggiornamento recipients scaduti: {e}")

        return results

    def _evaluate_approval_request_status(self, approval_request: ApprovalRequest) -> Tuple[ApprovalStatus, str]:
        """
        Valuta lo stato finale di una richiesta di approvazione basato sui recipients
        
        Args:
            approval_request: Richiesta da valutare
        
        Returns:
            Tuple[ApprovalStatus, str]: Stato finale e motivo
        """
        recipients = approval_request.recipients

        approved_count = len(
            [r for r in recipients if r.status == RecipientStatus.APPROVED])
        rejected_count = len(
            [r for r in recipients if r.status == RecipientStatus.REJECTED])
        pending_count = len(
            [r for r in recipients if r.status == RecipientStatus.PENDING])
        expired_count = len(
            [r for r in recipients if r.status == RecipientStatus.EXPIRED])

        # Logica di approvazione basata sul tipo
        if approval_request.approval_type == ApprovalType.ALL:
            # ALL: Tutti devono approvare
            if rejected_count > 0:
                new_status = ApprovalStatus.REJECTED
                reason = "at_least_one_rejection"
            elif approved_count == len(recipients):
                new_status = ApprovalStatus.APPROVED
                reason = "all_approved"
            elif pending_count == 0 and expired_count > 0:
                # Nessuno in attesa, ma qualcuno scaduto
                new_status = ApprovalStatus.REJECTED
                reason = "expired_recipients"
            else:
                # Ancora in attesa
                return approval_request.status, None

        elif approval_request.approval_type == ApprovalType.ANY:
            # ANY: Basta uno che approva
            if approved_count > 0:
                new_status = ApprovalStatus.APPROVED
                reason = "at_least_one_approval"
            elif pending_count == 0:
                # Nessuno in attesa: tutti hanno rifiutato o sono scaduti
                new_status = ApprovalStatus.REJECTED
                reason = "all_rejected_or_expired"
            else:
                # Ancora in attesa
                return approval_request.status, None
        else:
            # Tipo non riconosciuto
            return approval_request.status, None

        # Aggiorna la richiesta se lo stato è cambiato
        if new_status != approval_request.status:
            approval_request.status = new_status
            approval_request.completed_at = datetime.now()
            approval_request.completion_reason = reason

            self.db.commit()

            # Audit log per completamento
            self._create_audit_log(
                approval_request_id=approval_request.id,
                user_id=None,  # Completamento automatico
                action="approval_request_completed",
                details=f"Richiesta di approvazione completata con stato: {new_status.value}",
                metadata={
                    "final_status": new_status.value,
                    "completion_reason": reason,
                    "approved_count": approved_count,
                    "rejected_count": rejected_count,
                    "expired_count": expired_count,
                    "approval_type": approval_request.approval_type.value
                }
            )

        return new_status, reason

    def _create_audit_log(
        self,
        approval_request_id: str,
        user_id: Optional[int],
        action: str,
        details: str,
        metadata: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> AuditLog:
        """
        Crea un audit log per tracciare le azioni sul workflow
        
        Args:
            approval_request_id: ID della richiesta
            user_id: ID utente (None per azioni di sistema)
            action: Tipo di azione
            details: Descrizione dell'azione
            metadata: Dati aggiuntivi in formato dict
            ip_address: IP del client
            user_agent: User agent
        
        Returns:
            AuditLog: Log creato
        """
        audit_log = AuditLog(
            approval_request_id=approval_request_id,
            user_id=user_id,
            action=action,
            details=details,
            metadata_json=json.dumps(metadata) if metadata else None,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.add(audit_log)
        self.db.commit()

        return audit_log

    def get_approval_statistics(self, user_id: int) -> Dict[str, int]:
        """
        Ottieni statistiche delle richieste di approvazione per un utente
        
        Args:
            user_id: ID dell'utente
        
        Returns:
            Dict con contatori delle richieste
        """
        from sqlalchemy import func

        # Statistiche come richiedente
        stats = {}

        for status in ApprovalStatus:
            count = self.db.query(func.count(ApprovalRequest.id)).filter(
                ApprovalRequest.requester_id == user_id,
                ApprovalRequest.status == status
            ).scalar()
            stats[f"requested_{status.value}"] = count

        # Statistiche come destinatario
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            pending_as_recipient = self.db.query(func.count(ApprovalRecipient.id)).filter(
                ApprovalRecipient.recipient_email == user.email,
                ApprovalRecipient.status == RecipientStatus.PENDING
            ).scalar()

            stats["pending_as_recipient"] = pending_as_recipient

        return stats

    def create_approval_request_with_email(
        self,
        request_data: ApprovalRequestCreate,
        requester_id: int,
        client_ip: str = None,
        user_agent: str = None,
        send_emails: bool = True
    ) -> Tuple[ApprovalRequestResponse, Dict[str, bool]]:
        """
        Crea richiesta di approvazione e invia email ai destinatari
        
        Args:
            request_data: Dati della richiesta
            requester_id: ID del richiedente
            client_ip: IP per audit
            user_agent: User agent per audit
            send_emails: Se inviare email ai destinatari
        
        Returns:
            Tuple[ApprovalRequestResponse, Dict[str, bool]]: Richiesta creata e risultati email
        """
        # Crea la richiesta di approvazione
        approval_response = self.create_approval_request(
            request_data=request_data,
            requester_id=requester_id,
            client_ip=client_ip,
            user_agent=user_agent
        )

        email_results = {}

        if send_emails:
            try:
                # Invia email ai destinatari
                email_service = EmailService()

                # Recupera la richiesta dal database per avere tutte le relazioni
                approval_request = self.db.query(ApprovalRequest).filter(
                    ApprovalRequest.id == approval_response.id
                ).first()

                email_results = email_service.send_bulk_approval_emails(
                    approval_request)

                # Audit log per invio email
                self._create_audit_log(
                    approval_request_id=approval_response.id,
                    user_id=requester_id,
                    action="approval_emails_sent",
                    details=f"Email inviate a {len(email_results)} destinatari",
                    metadata={
                        "email_results": email_results,
                        "successful_emails": sum(email_results.values()),
                        "total_emails": len(email_results)
                    },
                    ip_address=client_ip,
                    user_agent=user_agent
                )

            except Exception as e:
                # Log errore ma non fallire la creazione della richiesta
                self._create_audit_log(
                    approval_request_id=approval_response.id,
                    user_id=requester_id,
                    action="approval_emails_failed",
                    details=f"Errore invio email: {str(e)}",
                    metadata={"error": str(e)},
                    ip_address=client_ip,
                    user_agent=user_agent
                )

        return approval_response, email_results

def get_pending_approvals_for_email(self, email: str) -> List[Dict[str, Any]]:
    """
    Recupera tutte le richieste di approvazione in attesa per un email
    Utile per dashboard destinatari e notifiche
    
    Args:
        email: Email del destinatario
    
    Returns:
        List[Dict]: Lista richieste pending per questo email
    """
    # ✅ Forza refresh per evitare dati stale
    self.db.expire_all()

    pending_recipients = self.db.query(ApprovalRecipient).filter(
        ApprovalRecipient.recipient_email == email,
        ApprovalRecipient.status == RecipientStatus.PENDING
    ).all()

    results = []
    expired_recipients = []

    for recipient in pending_recipients:
        # ✅ Verifica che il recipient sia effettivamente pending
        if recipient.status != RecipientStatus.PENDING:
            continue  # Skip se non è più pending

        request = recipient.approval_request
        document = request.document

        # Controlla scadenza
        is_expired = (
            recipient.expires_at and recipient.expires_at < datetime.now())
        if is_expired:
            expired_recipients.append(recipient)
            continue

        results.append({
            "approval_request_id": request.id,
            "title": request.title,
            "description": request.description,
            "requester_name": request.requester.display_name or request.requester.email,
            "document_filename": document.original_filename,
            "document_id": document.id,
            "approval_type": request.approval_type.value,
            "created_at": request.created_at,
            "expires_at": recipient.expires_at,
            "approval_token": recipient.approval_token,
            "recipient_name": recipient.recipient_name,
            "requester_comments": request.requester_comments
        })

    # Batch update dei recipients scaduti
    if expired_recipients:
        for recipient in expired_recipients:
            recipient.status = RecipientStatus.EXPIRED

        try:
            self.db.commit()

            for recipient in expired_recipients:
                self._create_audit_log(
                    approval_request_id=recipient.approval_request_id,
                    user_id=None,
                    action="recipient_expired",
                    details=f"Recipient {recipient.recipient_email} scaduto automaticamente",
                    metadata={
                        "recipient_email": recipient.recipient_email,
                        "expired_at": datetime.now().isoformat(),
                        "original_expires_at": recipient.expires_at.isoformat() if recipient.expires_at else None
                    }
                )
        except Exception as e:
            self.db.rollback()
            print(
                f"Warning: Errore durante aggiornamento recipients scaduti: {e}")

    return results
