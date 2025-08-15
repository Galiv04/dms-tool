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
        """Crea connessione SMTP con fallback SSL per compatibilità"""
        server = None
        last_error = None
        
        try:
            if self.smtp_use_tls:
                # Tentativo 1: SSL strict (produzione)
                try:
                    logger.info("Attempting SMTP connection with strict SSL...")
                    context_strict = ssl.create_default_context()
                    server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                    server.starttls(context=context_strict)
                except ssl.SSLError as ssl_error:
                    logger.warning(f"Strict SSL failed: {ssl_error}")
                    last_error = ssl_error
                    # Tentativo 2: SSL permissivo (sviluppo/test)
                    logger.info("Attempting SMTP connection with permissive SSL...")
                    context_permissive = ssl.create_default_context()
                    context_permissive.check_hostname = False
                    context_permissive.verify_mode = ssl.CERT_NONE
                    server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                    server.starttls(context=context_permissive)
                    logger.warning("Using permissive SSL context (not recommended for production)")
            else:
                # SSL diretto
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)

            # Login
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
        """Invia email con supporto HTML e allegati"""
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
        """Aggiunge allegato al messaggio email"""
        try:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment["content"])
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", f"attachment; filename= {attachment['filename']}"
            )
            message.attach(part)
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment.get('filename')}: {e}")

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Renderizza template Jinja2"""
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            # Fallback a template semplice
            return self._create_fallback_template(template_name, context)

    def _create_fallback_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Template moderni con stile inline minimalista"""
        
        # CSS base per tutti i template
        base_style = """
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background: #f8f9fa; margin: 0; padding: 20px; }
            .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; }
            .content { padding: 30px; }
            .button { display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 10px 5px; }
            .button.success { background: #28a745; }
            .button.danger { background: #dc3545; }
            .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }
            .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
            .badge.pending { background: #fff3cd; color: #856404; }
            .badge.approved { background: #d4edda; color: #155724; }
            .badge.rejected { background: #f8d7da; color: #721c24; }
        </style>
        """
        
        if "approval_request" in template_name:
            recipient_name = context.get('recipient_name', 'Utente')
            title = context.get('title', 'Richiesta Approvazione')
            requester_name = context.get('requester_name', 'Sistema')
            document_filename = context.get('document_filename', 'Documento')
            approval_url = context.get('approval_url', '#')
            expires_at = context.get('expires_at', '')
            
            return f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8">{base_style}</head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📋 Nuova Richiesta di Approvazione</h1>
                    </div>
                    <div class="content">
                        <p>Ciao <strong>{recipient_name}</strong>,</p>
                        <p>Hai ricevuto una nuova richiesta di approvazione che richiede la tua attenzione:</p>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="margin-top: 0; color: #667eea;">📄 {title}</h3>
                            <p><strong>Documento:</strong> {document_filename}</p>
                            <p><strong>Richiedente:</strong> {requester_name}</p>
                            {f'<p><strong>Scadenza:</strong> {expires_at}</p>' if expires_at else ''}
                            <span class="badge pending">IN ATTESA</span>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{approval_url}" class="button success">✅ Approva</a>
                            <a href="{approval_url}" class="button danger">❌ Rifiuta</a>
                        </div>
                        
                        <p style="color: #666; font-size: 14px;">
                            💡 Clicca sui pulsanti sopra per prendere una decisione, oppure 
                            <a href="{approval_url}">visualizza i dettagli completi</a>.
                        </p>
                    </div>
                    <div class="footer">
                        <p>📧 Email automatica dal sistema {context.get('app_name', 'DMS')}</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        elif "completion" in template_name:
            requester_name = context.get('requester_name', 'Utente')
            title = context.get('title', 'Richiesta')
            final_status = context.get('final_status', 'completata')
            approved_count = context.get('approved_count', 0)
            total_recipients = context.get('total_recipients', 0)
            
            status_icon = "✅" if final_status == "approved" else "❌" if final_status == "rejected" else "⏰"
            status_class = "approved" if final_status == "approved" else "rejected"
            
            return f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8">{base_style}</head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{status_icon} Approvazione Completata</h1>
                    </div>
                    <div class="content">
                        <p>Ciao <strong>{requester_name}</strong>,</p>
                        <p>La tua richiesta di approvazione è stata completata!</p>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="margin-top: 0; color: #667eea;">📄 {title}</h3>
                            <span class="badge {status_class}">{status_icon} {final_status.upper()}</span>
                            
                            <div style="margin-top: 15px;">
                                <strong>📊 Risultati:</strong>
                                <ul style="margin: 10px 0;">
                                    <li>✅ Approvazioni: {approved_count}</li>
                                    <li>👥 Totale destinatari: {total_recipients}</li>
                                </ul>
                            </div>
                        </div>
                        
                        <p style="color: #666;">
                            Puoi visualizzare tutti i dettagli nella tua dashboard delle approvazioni.
                        </p>
                    </div>
                    <div class="footer">
                        <p>📧 Email automatica dal sistema {context.get('app_name', 'DMS')}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
        elif "reminder" in template_name:
            recipient_name = context.get('recipient_name', 'Utente')
            title = context.get('title', 'Richiesta')
            days_left = context.get('days_left', 0)
            approval_url = context.get('approval_url', '#')
            
            urgency_color = "#dc3545" if days_left <= 1 else "#ffc107" if days_left <= 3 else "#28a745"
            
            return f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8">{base_style}</head>
            <body>
                <div class="container">
                    <div class="header" style="background: linear-gradient(135deg, {urgency_color} 0%, #fd7e14 100%);">
                        <h1>⏰ Reminder Approvazione</h1>
                    </div>
                    <div class="content">
                        <p>Ciao <strong>{recipient_name}</strong>,</p>
                        <p>Ti ricordiamo che hai una richiesta di approvazione <strong>in scadenza</strong>:</p>
                        
                        <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="margin-top: 0; color: #856404;">📄 {title}</h3>
                            <p style="font-size: 18px; color: {urgency_color}; font-weight: 600;">
                                ⏳ Scade tra {days_left} {'giorno' if days_left == 1 else 'giorni'}
                            </p>
                            <span class="badge pending">URGENTE</span>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{approval_url}" class="button success">✅ Approva Ora</a>
                            <a href="{approval_url}" class="button danger">❌ Rifiuta Ora</a>
                        </div>
                        
                        <p style="color: #856404; background: #fff3cd; padding: 15px; border-radius: 6px;">
                            ⚠️ <strong>Importante:</strong> Se non rispondi entro la scadenza, 
                            la richiesta verrà automaticamente rifiutata.
                        </p>
                    </div>
                    <div class="footer">
                        <p>📧 Reminder automatico dal sistema {context.get('app_name', 'DMS')}</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        # Fallback generico
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8">{base_style}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📧 Notifica Sistema</h1>
                </div>
                <div class="content">
                    <p>Hai ricevuto una notifica dal sistema di gestione documenti.</p>
                </div>
                <div class="footer">
                    <p>Sistema {context.get('app_name', 'DMS')}</p>
                </div>
            </div>
        </body>
        </html>
        """

    def send_approval_request_email(
        self,
        approval_request: ApprovalRequest,
        recipient: ApprovalRecipient
    ) -> bool:
        """Invia email di richiesta approvazione a un destinatario"""
        try:
            # Costruisci URL approvazione
            approval_url = f"{self.approval_url_base}/{recipient.approval_token}"

            # Contesto per template con nomi corretti
            context = {
                "recipient_name": recipient.recipient_name or recipient.recipient_email.split('@')[0],
                "recipient_email": recipient.recipient_email,
                "title": approval_request.title,
                "description": approval_request.description,
                "requester_name": approval_request.requester.display_name or approval_request.requester.email,
                "document_filename": approval_request.document.original_filename if approval_request.document else "N/A",
                "approval_type": approval_request.approval_type.value,
                "expires_at": recipient.expires_at.strftime('%d/%m/%Y %H:%M') if recipient.expires_at else '',
                "created_at": approval_request.created_at.strftime('%d/%m/%Y %H:%M'),
                "requester_comments": approval_request.requester_comments,
                "approval_url": approval_url,
                "app_name": settings.app_name or "Document Management System"
            }

            # Renderizza template
            html_body = self._render_template("approval_request.html", context)

            # Oggetto email
            subject = f"[{settings.app_name or 'DMS'}] 📋 Richiesta Approvazione: {approval_request.title}"

            # Corpo testo alternativo
            text_body = f"""
📋 RICHIESTA DI APPROVAZIONE

Ciao {context['recipient_name']},

Titolo: {approval_request.title}
Documento: {context['document_filename']}
Richiedente: {context['requester_name']}

👉 Rispondi qui: {approval_url}

Scadenza: {context['expires_at'] or 'Nessuna'}

---
{settings.app_name or 'DMS'}
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
        """Invia notifica di completamento al richiedente"""
        try:
            requester = approval_request.requester
            recipients = approval_request.recipients
            
            approved_count = len([r for r in recipients if r.status.value == "approved"])
            rejected_count = len([r for r in recipients if r.status.value == "rejected"])

            # Contesto per template
            context = {
                "requester_name": requester.display_name or requester.email,
                "title": approval_request.title,
                "description": approval_request.description,
                "document_filename": approval_request.document.original_filename if approval_request.document else "N/A",
                "final_status": approval_request.status.value,
                "completion_reason": approval_request.completion_reason,
                "completed_at": approval_request.completed_at.strftime('%d/%m/%Y %H:%M') if approval_request.completed_at else 'N/A',
                "created_at": approval_request.created_at.strftime('%d/%m/%Y %H:%M'),
                "approved_count": approved_count,
                "rejected_count": rejected_count,
                "total_recipients": len(recipients),
                "approval_type": approval_request.approval_type.value,
                "app_name": settings.app_name or "Document Management System"
            }

            # Renderizza template
            html_body = self._render_template("approval_completion.html", context)

            # Oggetto email basato su stato finale
            status_text = "Approvato" if approval_request.status.value == "approved" else "Rifiutato"
            subject = f"[{settings.app_name or 'DMS'}] {status_text}: {approval_request.title}"

            # Corpo testo alternativo
            text_body = f"""
📋 APPROVAZIONE COMPLETATA

Ciao {context['requester_name']},

La tua richiesta di approvazione è stata completata:

Titolo: {approval_request.title}
Stato Finale: {approval_request.status.value.upper()}

Statistiche:
- Approvazioni: {approved_count}/{len(recipients)}
- Rifiuti: {rejected_count}/{len(recipients)}

Completata il: {context['completed_at']}

---
{settings.app_name or 'DMS'}
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
        """Invia email di reminder per approvazione scadente"""
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
                "recipient_name": recipient.recipient_name or recipient.recipient_email.split('@')[0],
                "title": approval_request.title,
                "document_filename": approval_request.document.original_filename if approval_request.document else "N/A",
                "requester_name": approval_request.requester.display_name or approval_request.requester.email,
                "days_left": days_left,
                "expires_at": recipient.expires_at.strftime('%d/%m/%Y %H:%M') if recipient.expires_at else 'Nessuna scadenza',
                "approval_url": approval_url,
                "app_name": settings.app_name or "Document Management System"
            }

            # Renderizza template
            html_body = self._render_template("approval_reminder.html", context)

            # Oggetto email
            subject = f"[{settings.app_name or 'DMS'}] ⏰ Reminder: {approval_request.title}"

            # Corpo testo alternativo
            text_body = f"""
⏰ REMINDER APPROVAZIONE

Ciao {context['recipient_name']},

Hai una richiesta di approvazione in attesa che scade a breve:

Titolo: {approval_request.title}
Giorni rimanenti: {days_left}
Scade il: {context['expires_at']}

👉 Rispondi qui: {approval_url}

---
{settings.app_name or 'DMS'}
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
        """Invia email di approvazione a tutti i destinatari"""
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
        """Testa la configurazione email"""
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
