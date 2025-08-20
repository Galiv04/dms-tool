import uuid
import json
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
from datetime import datetime, timezone, timedelta
from app.utils.datetime_utils import format_datetime_for_api, get_utc_now, ensure_utc
import logging


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
            expires_at=ensure_utc(
                request_data.expires_at) if request_data.expires_at else None,
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
                expires_at=ensure_utc(
                    request_data.expires_at) if request_data.expires_at else None
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
                "expires_at": format_datetime_for_api(request_data.expires_at) if request_data.expires_at else None
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
        """
        # Trova il recipient tramite token
        recipient = self.db.query(ApprovalRecipient).filter(
            ApprovalRecipient.approval_token == approval_token
        ).first()

        if not recipient:
            raise NotFoundError("Token di approvazione non valido")

        # Verifica che il token non sia scaduto
        if recipient.expires_at:
            # Fix robusto per timezone comparison
            expires_dt = recipient.expires_at
            current_dt = get_utc_now()

            # Se expires_dt è naive, assumilo come UTC
            if expires_dt.tzinfo is None:
                expires_utc = expires_dt.replace(tzinfo=timezone.utc)
            else:
                expires_utc = expires_dt.astimezone(timezone.utc)

            # current_dt è già UTC da get_utc_now()
            current_utc = current_dt

            if expires_utc < current_utc:
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
        recipient.responded_at = get_utc_now()
        recipient.ip_address = client_ip
        recipient.user_agent = user_agent

        self.db.commit()

        # 📧 Invia email di notifica al richiedente
        try:
            from app.services.email import EmailService

            if EmailService.enabled:
                approval_request = recipient.approval_request

                decision_email_data = {
                    'title': approval_request.title,
                    'document_filename': approval_request.document.original_filename,
                    'recipient_name': recipient.recipient_name or recipient.recipient_email,
                    'recipient_email': recipient.recipient_email,
                    'decision': decision_data.decision,
                    'comments': decision_data.comments,
                    'decided_at': get_utc_now().strftime('%d/%m/%Y %H:%M'),
                    'approval_completed': final_status != ApprovalStatus.PENDING,
                    'final_status': final_status.value if final_status != ApprovalStatus.PENDING else None
                }

                # Invio email in background tramite thread (per non bloccare la risposta)
                import threading
                email_thread = threading.Thread(
                    target=EmailService.send_approval_decision_email,
                    args=(
                        approval_request.requester.email,
                        approval_request.requester.display_name or approval_request.requester.email,
                        decision_email_data
                    )
                )
                email_thread.daemon = True
                email_thread.start()

        except Exception as e:
            logging.error(
                f"Failed to send decision notification email: {str(e)}")

        # Carica la approval request
        approval_request = recipient.approval_request

        # Crea audit log per la decisione
        self._create_audit_log(
            approval_request_id=approval_request.id,
            user_id=None,
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
        """
        approval_request = self.db.query(ApprovalRequest).filter(
            ApprovalRequest.id == request_id
        ).first()

        if not approval_request:
            raise NotFoundError(
                f"Richiesta di approvazione {request_id} non trovata")

        # Controllo autorizzazione
        if user_id and approval_request.requester_id != user_id:
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
        """Lista le richieste di approvazione dell'utente"""

        # 🔧 FIX: Aggiungi joinedload per includere tutti i dati necessari
        from sqlalchemy.orm import joinedload

        query = self.db.query(ApprovalRequest)\
            .options(
                joinedload(ApprovalRequest.requester),
                # ← AGGIUNGI per documento
                joinedload(ApprovalRequest.document),
                # ← AGGIUNGI per recipients
                joinedload(ApprovalRequest.recipients)
        )\
            .filter(ApprovalRequest.requester_id == user_id)

        if status_filter:
            query = query.filter(ApprovalRequest.status == status_filter)

        query = query.order_by(ApprovalRequest.created_at.desc())
        query = query.offset(offset).limit(limit)

        requests = query.all()

        # 🔧 FIX: Costruisci la risposta con tutti i dati
        result = []
        for req in requests:
            recipients = req.recipients
            approved_count = len(
                [r for r in recipients if r.status == RecipientStatus.APPROVED])
            pending_count = len(
                [r for r in recipients if r.status == RecipientStatus.PENDING])

            # 🔧 Costruisci il dizionario con tutti i dati necessari
            req_dict = {
                "id": req.id,
                "document_id": req.document_id,
                "title": req.title,
                "approval_type": req.approval_type,
                "status": req.status,
                "created_at": req.created_at,
                "expires_at": req.expires_at,
                "requester_id": req.requester_id,
                "recipient_count": len(recipients),
                "approved_count": approved_count,
                "pending_count": pending_count
            }

            # 🔧 Aggiungi dati requester
            if req.requester:
                req_dict["requester"] = {
                    "id": req.requester.id,
                    "email": req.requester.email,
                    "display_name": req.requester.display_name
                }

            # 🔧 AGGIUNGI dati documento
            if req.document:
                req_dict["document"] = {
                    "id": req.document.id,
                    "filename": req.document.filename,
                    "original_filename": req.document.original_filename,
                    "content_type": req.document.content_type
                }

            # 🔧 AGGIUNGI dati recipients
            if recipients:
                req_dict["recipients"] = [
                    {
                        "id": r.id,
                        "recipient_email": r.recipient_email,
                        "recipient_name": r.recipient_name,
                        "status": r.status,
                        "approval_token": r.approval_token,
                        "comments": r.comments,  # 🆕 AGGIUNGI QUESTO
                        "responded_at": r.responded_at,
                        "decision": r.decision
                    }
                    for r in recipients
                ]

            req_data = ApprovalRequestListResponse.model_validate(req_dict)
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
        approval_request.completed_at = get_utc_now()
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
        """
        # Forza refresh per evitare dati stale
        self.db.expire_all()

        pending_recipients = self.db.query(ApprovalRecipient).filter(
            ApprovalRecipient.recipient_email == email,
            ApprovalRecipient.status == RecipientStatus.PENDING
        ).all()

        results = []
        expired_recipients = []  # Colleziona recipients scaduti per batch update

        for recipient in pending_recipients:
            # Verifica che il recipient sia effettivamente pending
            if recipient.status != RecipientStatus.PENDING:
                continue  # Skip se non è più pending

            request = recipient.approval_request
            document = request.document

            # Controlla scadenza usando ensure_utc per confronto consistente
            is_expired = (
                recipient.expires_at and ensure_utc(recipient.expires_at) < get_utc_now())

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
                # 🔧 FIX: format_datetime_for_api
                "created_at": format_datetime_for_api(request.created_at),
                # 🔧 FIX: format_datetime_for_api
                "expires_at": format_datetime_for_api(recipient.expires_at),
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
                            "expired_at": format_datetime_for_api(get_utc_now()),
                            "original_expires_at": format_datetime_for_api(recipient.expires_at) if recipient.expires_at else None
                        }
                    )
            except Exception as e:
                self.db.rollback()
                print(
                    f"Warning: Errore durante aggiornamento recipients scaduti: {e}")

        return results

    def _evaluate_approval_request_status(self, approval_request: ApprovalRequest) -> Tuple[ApprovalStatus, str]:
        """
        Valuta lo stato finale di una richiesta di approvazione basato sui recipients
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
            approval_request.completed_at = get_utc_now()
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

    def create_approval_request(
        self,
        request_data: ApprovalRequestCreate,
        requester_id: int,
        client_ip: str = None,
        user_agent: str = None
    ) -> ApprovalRequestResponse:
        """
        Crea una nuova richiesta di approvazione con destinatari e invio email
        """
        logger = logging.getLogger(__name__)
        logger.info(
            f"🚀 Creating approval request: '{request_data.title}' for user {requester_id}")

        # Verifica che il documento esista e appartenga al richiedente
        logger.debug(
            f"🔍 Verifying document {request_data.document_id} ownership")
        document = self.db.query(Document).filter(
            Document.id == request_data.document_id,
            Document.owner_id == requester_id
        ).first()

        if not document:
            logger.error(
                f"❌ Document {request_data.document_id} not found or not owned by user {requester_id}")
            raise NotFoundError(
                f"Documento {request_data.document_id} non trovato o non autorizzato")

        logger.info(f"✅ Document verified: {document.original_filename}")

        # Verifica che non ci siano già richieste PENDING per questo documento
        logger.debug(
            f"🔍 Checking for existing pending requests for document {request_data.document_id}")
        existing_pending = self.db.query(ApprovalRequest).filter(
            ApprovalRequest.document_id == request_data.document_id,
            ApprovalRequest.status == ApprovalStatus.PENDING
        ).first()

        if existing_pending:
            logger.error(
                f"❌ Existing pending request found: {existing_pending.id}")
            raise ValidationError(
                f"Esiste già una richiesta di approvazione in corso per questo documento")

        logger.info("✅ No existing pending requests found")

        # Crea la richiesta di approvazione
        logger.debug("🔧 Creating ApprovalRequest instance")
        approval_request = ApprovalRequest(
            document_id=request_data.document_id,
            requester_id=requester_id,
            title=request_data.title,
            description=request_data.description,
            approval_type=request_data.approval_type,
            expires_at=ensure_utc(
                request_data.expires_at) if request_data.expires_at else None,
            requester_comments=request_data.requester_comments
        )

        self.db.add(approval_request)
        self.db.commit()
        self.db.refresh(approval_request)

        logger.info(
            f"✅ ApprovalRequest created with ID: {approval_request.id}")

        # Crea i destinatari
        logger.debug(f"🔧 Creating {len(request_data.recipients)} recipients")
        recipients = []
        for i, recipient_data in enumerate(request_data.recipients, 1):
            logger.debug(
                f"  📧 Creating recipient {i}: {recipient_data.recipient_email}")
            recipient = ApprovalRecipient(
                approval_request_id=approval_request.id,
                recipient_email=recipient_data.recipient_email,
                recipient_name=recipient_data.recipient_name,
                expires_at=ensure_utc(
                    request_data.expires_at) if request_data.expires_at else None
            )
            recipients.append(recipient)

        self.db.add_all(recipients)
        self.db.commit()

        # Refresh per caricare i recipients con token generati
        self.db.refresh(approval_request)

        logger.info(f"✅ Created {len(recipients)} recipients with tokens")
        for recipient in approval_request.recipients:
            logger.debug(
                f"  📧 {recipient.recipient_email} → Token: {recipient.approval_token[:8]}...")

        email_results = {}
        try:
            logger.info("📧 Starting bulk email sending process")

            # 🔧 CREA ISTANZA EmailService invece di usare singleton
            email_service = EmailService()

            if email_service.enabled:
                logger.info("✅ Email service is enabled, sending emails...")
                email_results = email_service.send_bulk_approval_emails(
                    approval_request)

                successful_emails = sum(email_results.values())
                total_emails = len(email_results)

                logger.info(
                    f"📊 Email sending results: {successful_emails}/{total_emails} successful")

                # Log dettagliato per ogni email
                for email, success in email_results.items():
                    status_icon = "✅" if success else "❌"
                    logger.info(f"  {status_icon} {email}")

                # Audit log per invio email
                self._create_audit_log(
                    approval_request_id=approval_request.id,
                    user_id=requester_id,
                    action="approval_emails_sent",
                    details=f"Email inviate a {total_emails} destinatari: {successful_emails} successi, {total_emails - successful_emails} errori",
                    metadata={
                        "email_results": email_results,
                        "successful_emails": successful_emails,
                        "total_emails": total_emails,
                        "recipients": [r.recipient_email for r in approval_request.recipients]
                    },
                    ip_address=client_ip,
                    user_agent=user_agent
                )

            else:
                logger.warning("⚠️ Email service is disabled in configuration")
                email_results = {
                    r.recipient_email: False for r in approval_request.recipients}

        except Exception as e:
            logger.error(f"❌ Error during bulk email sending: {str(e)}")
            logger.exception("Full email error traceback:")

            # Log errore ma non fallire la creazione della richiesta
            self._create_audit_log(
                approval_request_id=approval_request.id,
                user_id=requester_id,
                action="approval_emails_failed",
                details=f"Errore critico invio email: {str(e)}",
                metadata={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "recipients_count": len(approval_request.recipients)
                },
                ip_address=client_ip,
                user_agent=user_agent
            )

            # Setta tutti i risultati email come falliti
            email_results = {
                r.recipient_email: False for r in approval_request.recipients}

        # Crea audit log principale per creazione
        logger.debug("📝 Creating main audit log for request creation")
        self._create_audit_log(
            approval_request_id=approval_request.id,
            user_id=requester_id,
            action="approval_request_created",
            details=f"Richiesta di approvazione creata: '{request_data.title}'",
            metadata={
                "document_id": request_data.document_id,
                "document_filename": document.original_filename,
                "approval_type": request_data.approval_type.value,
                "recipients_count": len(recipients),
                "expires_at": format_datetime_for_api(request_data.expires_at) if request_data.expires_at else None,
                "email_sending_enabled": EmailService.enabled if 'EmailService' in locals() else False,
                "emails_sent_successfully": sum(email_results.values()) if email_results else 0
            },
            ip_address=client_ip,
            user_agent=user_agent
        )

        # Audit log per i destinatari aggiunti
        recipient_emails = [r.recipient_email for r in recipients]
        logger.debug(
            f"📝 Creating recipients audit log for {len(recipient_emails)} recipients")
        self._create_audit_log(
            approval_request_id=approval_request.id,
            user_id=requester_id,
            action="recipients_added",
            details=f"Aggiunti {len(recipients)} destinatari alla richiesta",
            metadata={
                "recipients": recipient_emails,
                "tokens_generated": [r.approval_token for r in approval_request.recipients],
                "email_results": email_results
            },
            ip_address=client_ip,
            user_agent=user_agent
        )

        # Preparazione risposta finale
        response = ApprovalRequestResponse.model_validate(approval_request)

        # Log finale con riassunto
        logger.info("🎉 Approval request creation completed successfully!")
        logger.info(f"  📋 Request ID: {approval_request.id}")
        logger.info(f"  📄 Document: {document.original_filename}")
        logger.info(f"  👥 Recipients: {len(recipients)}")
        logger.info(
            f"  📧 Emails sent: {sum(email_results.values())}/{len(email_results)}")
        logger.info(f"  🏷️ Title: {request_data.title}")

        return response

    def delete_approval_request(
        self,
        request_id: str,
        user_id: int,
        client_ip: str = None
    ) -> Dict[str, str]:
        """
        Elimina definitivamente una richiesta di approvazione

        Args:
            request_id: ID della richiesta
            user_id: ID dell'utente (deve essere il richiedente)
            client_ip: IP per audit

        Returns:
            Dict con messaggio di conferma

        Raises:
            NotFoundError: Se la richiesta non esiste
            PermissionDeniedError: Se l'utente non è il richiedente
            ValidationError: Se la richiesta non può essere eliminata
        """
        approval_request = self.db.query(ApprovalRequest).filter(
            ApprovalRequest.id == request_id
        ).first()

        if not approval_request:
            raise NotFoundError(
                f"Richiesta di approvazione {request_id} non trovata")

        if approval_request.requester_id != user_id:
            raise PermissionDeniedError(
                "Non sei autorizzato a eliminare questa richiesta")

        if approval_request.status != ApprovalStatus.PENDING:
            raise ValidationError(
                f"Non è possibile eliminare una richiesta in stato {approval_request.status.value}"
            )

        # Audit log prima dell'eliminazione
        self._create_audit_log(
            approval_request_id=approval_request.id,
            user_id=user_id,
            action="approval_request_deleted",
            details=f"Richiesta di approvazione '{approval_request.title}' eliminata dal richiedente",
            metadata={
                "title": approval_request.title,
                "document_filename": approval_request.document.original_filename if approval_request.document else None,
                "recipients_count": len(approval_request.recipients),
                "deletion_reason": "user_requested"
            },
            ip_address=client_ip
        )

        # Salva il titolo prima dell'eliminazione
        title = approval_request.title

        # Elimina la richiesta (CASCADE eliminerà automaticamente recipients e audit logs)
        self.db.delete(approval_request)
        self.db.commit()

        return {
            "message": f"Richiesta di approvazione '{title}' eliminata con successo",
            "request_id": request_id,
            "status": "deleted"
        }
