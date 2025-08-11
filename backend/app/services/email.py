import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import logging
from jinja2 import Environment, FileSystemLoader, Template

from app.configurations import settings
from app.db.models import ApprovalRequest, ApprovalRecipient, User
from app.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

class EmailService:
    """Service per l'invio di email nel sistema di approvazioni"""
    
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.smtp_use_tls = settings.smtp_use_tls
        self.email_from = settings.email_from
        self.approval_url_base = settings.approval_url_base
        
        # Setup Jinja2 per template
        self.template_dir = Path("templates/email")
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True
        )
    
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """
        Crea connessione SMTP con fallback SSL per compatibilità
        
        Returns:
            smtplib.SMTP: Connessione SMTP configurata
            
        Raises:
            Exception: Se la connessione fallisce
        """
        server = None
        last_error = None
        
        try:
            if self.smtp_use_tls:
                # ✅ Tentativo 1: SSL strict (produzione)
                try:
                    logger.info("Attempting SMTP connection with strict SSL...")
                    context_strict = ssl.create_default_context()
                    server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                    server.starttls(context=context_strict)
                    
                except ssl.SSLError as ssl_error:
                    logger.warning(f"Strict SSL failed: {ssl_error}")
                    last_error = ssl_error
                    
                    # ✅ Tentativo 2: SSL permissivo (sviluppo/test)
                    logger.info("Attempting SMTP connection with permissive SSL...")
                    context_permissive = ssl.create_default_context()
                    context_permissive.check_hostname = False
                    context_permissive.verify_mode = ssl.CERT_NONE
                    
                    server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                    server.starttls(context=context_permissive)
                    
                    logger.warning("Using permissive SSL context (not recommended for production)")
            else:
                # ✅ SSL diretto
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            
            # ✅ Login
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            logger.info(f"SMTP connection established to {self.smtp_server}:{self.smtp_port}")
            return server
            
        except Exception as e:
            if server:
                try:
                    server.quit()
                except:
                    pass
            
            logger.error(f"All SMTP connection attempts failed. Last error: {e}")
            raise last_error or e

    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Invia email con supporto HTML e allegati
        
        Args:
            to_email: Destinatario
            subject: Oggetto email
            html_body: Corpo HTML
            text_body: Corpo testo alternativo
            attachments: Lista allegati
            
        Returns:
            bool: True se invio riuscito
        """
        if not settings.email_enabled:
            logger.info(f"Email disabled - would send to {to_email}: {subject}")
            return True
        
        try:
            # Crea messaggio
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.email_from
            message["To"] = to_email
            
            # Aggiungi corpo testo se fornito
            if text_body:
                text_part = MIMEText(text_body, "plain")
                message.attach(text_part)
            
            # Aggiungi corpo HTML
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            # Aggiungi allegati se presenti
            if attachments:
                for attachment in attachments:
                    self._add_attachment(message, attachment)
            
            # Invia email
            with self._create_smtp_connection() as server:
                server.send_message(message)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _add_attachment(self, message: MIMEMultipart, attachment: Dict[str, Any]):
        """
        Aggiunge allegato al messaggio email
        
        Args:
            message: Messaggio email
            attachment: Dict con filename, content, content_type
        """
        try:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment["content"])
            encoders.encode_base64(part)
            
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {attachment['filename']}"
            )
            
            message.attach(part)
            
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment.get('filename')}: {e}")
    
    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Renderizza template Jinja2
        
        Args:
            template_name: Nome del template
            context: Variabili per il template
            
        Returns:
            str: HTML renderizzato
        """
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            # Fallback a template semplice
            return self._create_fallback_template(template_name, context)
    
    def _create_fallback_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Crea template fallback se il template file non esiste
        
        Args:
            template_name: Nome template
            context: Contesto
            
        Returns:
            str: HTML fallback
        """
        if "approval_request" in template_name:
            # ✅ Fix: Usa recipient_name se disponibile, altrimenti requester_name
            recipient_name = context.get('recipient_name') or context.get('requester_name', 'N/A')
            requester_name = context.get('requester_name') or context.get('recipient_name', 'N/A')
            
            return f"""
            <html>
                <body>
                    <h2>Richiesta di Approvazione</h2>
                    <p>Ciao <strong>{recipient_name}</strong>,</p>
                    <p>Hai ricevuto una nuova richiesta di approvazione:</p>
                    <p><strong>Titolo:</strong> {context.get('title', 'N/A')}</p>
                    <p><strong>Documento:</strong> {context.get('document_filename', 'N/A')}</p>
                    <p><strong>Richiedente:</strong> {requester_name}</p>
                    <p><a href="{context.get('approval_url', '#')}">Approva/Rifiuta</a></p>
                </body>
            </html>
            """
        elif "completion" in template_name:
            # ✅ Fix: Usa requester_name se disponibile, altrimenti recipient_name per completamento
            user_name = context.get('requester_name') or context.get('recipient_name', 'N/A')
            
            return f"""
            <html>
                <body>
                    <h2>Approvazione Completata</h2>
                    <p>Ciao <strong>{user_name}</strong>,</p>
                    <p>La tua richiesta di approvazione è stata completata:</p>
                    <p><strong>Titolo:</strong> {context.get('title', 'N/A')}</p>
                    <p><strong>Stato:</strong> {context.get('final_status', 'N/A')}</p>
                </body>
            </html>
            """
        elif "reminder" in template_name:
            # ✅ Fix: Aggiungi supporto per reminder template
            recipient_name = context.get('recipient_name') or context.get('requester_name', 'N/A')
            
            return f"""
            <html>
                <body>
                    <h2>Reminder Approvazione</h2>
                    <p>Ciao <strong>{recipient_name}</strong>,</p>
                    <p>Ti ricordiamo che hai una richiesta di approvazione in attesa:</p>
                    <p><strong>Titolo:</strong> {context.get('title', 'N/A')}</p>
                    <p><strong>Documento:</strong> {context.get('document_filename', 'N/A')}</p>
                    <p><a href="{context.get('approval_url', '#')}">Vai alla Richiesta</a></p>
                </body>
            </html>
            """
        else:
            return f"""
            <html>
                <body>
                    <h2>Notifica Sistema</h2>
                    <p>Hai ricevuto una notifica dal sistema di gestione documenti.</p>
                    <p><strong>App:</strong> {context.get('app_name', 'Document Management System')}</p>
                </body>
            </html>
            """

    def send_approval_request_email(
        self,
        approval_request: ApprovalRequest,
        recipient: ApprovalRecipient
    ) -> bool:
        """
        Invia email di richiesta approvazione a un destinatario
        
        Args:
            approval_request: Richiesta di approvazione
            recipient: Destinatario specifico
            
        Returns:
            bool: True se invio riuscito
        """
        try:
            # Costruisci URL approvazione
            approval_url = f"{self.approval_url_base}/{recipient.approval_token}"
            
            # Contesto per template
            context = {
                "recipient_name": recipient.recipient_name,
                "recipient_email": recipient.recipient_email,
                "title": approval_request.title,
                "description": approval_request.description,
                "requester_name": approval_request.requester.display_name or approval_request.requester.email,
                "document_filename": approval_request.document.original_filename,
                "document_size": approval_request.document.size,
                "approval_type": approval_request.approval_type.value,
                "expires_at": recipient.expires_at,
                "created_at": approval_request.created_at,
                "requester_comments": approval_request.requester_comments,
                "approval_url": approval_url,
                "approval_token": recipient.approval_token,
                "app_name": settings.app_name
            }
            
            # Renderizza template
            html_body = self._render_template("approval_request.html", context)
            
            # Oggetto email
            subject = f"[{settings.app_name}] Richiesta Approvazione: {approval_request.title}"
            
            # Corpo testo alternativo
            text_body = f"""
Richiesta di Approvazione

Ciao {recipient.recipient_name},

Hai ricevuto una nuova richiesta di approvazione:

Titolo: {approval_request.title}
Documento: {approval_request.document.original_filename}
Richiedente: {approval_request.requester.display_name or approval_request.requester.email}

Per approvare o rifiutare, visita: {approval_url}

Scadenza: {recipient.expires_at.strftime('%d/%m/%Y %H:%M') if recipient.expires_at else 'Nessuna'}

---
{settings.app_name}
            """
            
            return self._send_email(
                to_email=recipient.recipient_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send approval request email to {recipient.recipient_email}: {e}")
            return False
    
    def send_completion_notification_email(
        self,
        approval_request: ApprovalRequest
    ) -> bool:
        """
        Invia notifica di completamento al richiedente
        
        Args:
            approval_request: Richiesta completata
            
        Returns:
            bool: True se invio riuscito
        """
        try:
            requester = approval_request.requester
            
            # Statistiche approvazione
            recipients = approval_request.recipients
            approved_count = len([r for r in recipients if r.status.value == "approved"])
            rejected_count = len([r for r in recipients if r.status.value == "rejected"])
            
            # Contesto per template
            context = {
                "requester_name": requester.display_name or requester.email,
                "title": approval_request.title,
                "description": approval_request.description,
                "document_filename": approval_request.document.original_filename,
                "final_status": approval_request.status.value,
                "completion_reason": approval_request.completion_reason,
                "completed_at": approval_request.completed_at,
                "created_at": approval_request.created_at,
                "approved_count": approved_count,
                "rejected_count": rejected_count,
                "total_recipients": len(recipients),
                "approval_type": approval_request.approval_type.value,
                "app_name": settings.app_name
            }
            
            # Renderizza template
            html_body = self._render_template("approval_completion.html", context)
            
            # Oggetto email basato su stato finale
            status_text = "Approvato" if approval_request.status.value == "approved" else "Rifiutato"
            subject = f"[{settings.app_name}] {status_text}: {approval_request.title}"
            
            # Corpo testo alternativo
            text_body = f"""
Approvazione Completata

Ciao {requester.display_name or requester.email},

La tua richiesta di approvazione è stata completata:

Titolo: {approval_request.title}
Documento: {approval_request.document.original_filename}
Stato Finale: {approval_request.status.value.upper()}

Statistiche:
- Approvazioni: {approved_count}/{len(recipients)}
- Rifiuti: {rejected_count}/{len(recipients)}

Completata il: {approval_request.completed_at.strftime('%d/%m/%Y %H:%M') if approval_request.completed_at else 'N/A'}

---
{settings.app_name}
            """
            
            return self._send_email(
                to_email=requester.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send completion email to {approval_request.requester.email}: {e}")
            return False
    
    def send_reminder_email(
        self,
        recipient: ApprovalRecipient
    ) -> bool:
        """
        Invia email di reminder per approvazione scadente
        
        Args:
            recipient: Destinatario con approvazione pending
            
        Returns:
            bool: True se invio riuscito
        """
        try:
            approval_request = recipient.approval_request
            approval_url = f"{self.approval_url_base}/{recipient.approval_token}"
            
            # Calcola giorni rimanenti
            days_left = 0
            if recipient.expires_at:
                delta = recipient.expires_at - datetime.now()
                days_left = max(0, delta.days)
            
            # Contesto per template
            context = {
                "recipient_name": recipient.recipient_name,
                "title": approval_request.title,
                "document_filename": approval_request.document.original_filename,
                "requester_name": approval_request.requester.display_name or approval_request.requester.email,
                "days_left": days_left,
                "expires_at": recipient.expires_at,
                "approval_url": approval_url,
                "app_name": settings.app_name
            }
            
            # Renderizza template
            html_body = self._render_template("approval_reminder.html", context)
            
            # Oggetto email
            subject = f"[{settings.app_name}] Reminder: {approval_request.title}"
            
            # Corpo testo alternativo
            text_body = f"""
Reminder Approvazione

Ciao {recipient.recipient_name},

Hai una richiesta di approvazione in attesa che scade a breve:

Titolo: {approval_request.title}
Documento: {approval_request.document.original_filename}
Richiedente: {approval_request.requester.display_name or approval_request.requester.email}

Giorni rimanenti: {days_left}
Scade il: {recipient.expires_at.strftime('%d/%m/%Y %H:%M') if recipient.expires_at else 'Nessuna scadenza'}

Per approvare o rifiutare, visita: {approval_url}

---
{settings.app_name}
            """
            
            return self._send_email(
                to_email=recipient.recipient_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send reminder email to {recipient.recipient_email}: {e}")
            return False
    
    def send_bulk_approval_emails(
        self,
        approval_request: ApprovalRequest
    ) -> Dict[str, bool]:
        """
        Invia email di approvazione a tutti i destinatari
        
        Args:
            approval_request: Richiesta di approvazione
            
        Returns:
            Dict[str, bool]: Risultati per ogni destinatario {email: success}
        """
        results = {}
        
        for recipient in approval_request.recipients:
            if recipient.status.value == "pending":
                success = self.send_approval_request_email(approval_request, recipient)
                results[recipient.recipient_email] = success
            else:
                logger.info(f"Skipping email for {recipient.recipient_email} - status: {recipient.status.value}")
        
        logger.info(f"Bulk email results: {sum(results.values())}/{len(results)} successful")
        return results
    
    def test_email_configuration(self) -> Dict[str, Any]:
        """
        Testa la configurazione email
        
        Returns:
            Dict con risultati del test
        """
        test_results = {
            "smtp_connection": False,
            "email_enabled": settings.email_enabled,
            "configuration": {
                "smtp_server": self.smtp_server,
                "smtp_port": self.smtp_port,
                "smtp_use_tls": self.smtp_use_tls,
                "email_from": self.email_from,
                "has_credentials": bool(self.smtp_username and self.smtp_password)
            },
            "error": None
        }
        
        if not settings.email_enabled:
            test_results["error"] = "Email service is disabled in configuration"
            return test_results
        
        try:
            # Test connessione SMTP
            with self._create_smtp_connection() as server:
                test_results["smtp_connection"] = True
                logger.info("SMTP connection test successful")
                
        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"SMTP connection test failed: {e}")
        
        return test_results
