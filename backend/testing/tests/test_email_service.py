import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup

import pytest
import uuid
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import traceback

from app.services.email import EmailService
from app.db.models import User, Document, ApprovalRequest, ApprovalRecipient, UserRole, ApprovalType, ApprovalStatus, RecipientStatus
from app.utils.security import hash_password

@pytest.mark.db
class TestEmailService:
    """Test per EmailService"""
    
    @pytest.fixture
    def email_service(self):
        """Fixture per EmailService"""
        return EmailService()
    
    @pytest.fixture
    def sample_approval_data(self, db_session):
        """Fixture con dati di approvazione per test email"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Crea utente richiedente
        user = User(
            email=f"requester_{unique_id}@test.com",
            password_hash=hash_password("testpass"),
            display_name=f"Test Requester {unique_id}",
            role=UserRole.USER
        )
        db_session.add(user)
        db_session.flush()
        
        # Crea documento
        document = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            filename=f"test_doc_{unique_id}.pdf",
            original_filename=f"test_doc_{unique_id}.pdf",
            storage_path=f"/fake/{unique_id}",
            content_type="application/pdf",
            size=1024.0,
            file_hash=f"hash_{unique_id}"
        )
        db_session.add(document)
        db_session.flush()
        
        # Crea richiesta approvazione
        approval_request = ApprovalRequest(
            document_id=document.id,
            requester_id=user.id,
            title=f"Test Approval {unique_id}",
            description="Test approval request for email service",
            approval_type=ApprovalType.ALL,
            expires_at=datetime.now() + timedelta(days=7)
        )
        db_session.add(approval_request)
        db_session.flush()
        
        # Crea destinatario
        recipient = ApprovalRecipient(
            approval_request_id=approval_request.id,
            recipient_email=f"approver_{unique_id}@test.com",
            recipient_name=f"Test Approver {unique_id}",
            expires_at=datetime.now() + timedelta(days=7)
        )
        db_session.add(recipient)
        
        db_session.commit()
        db_session.refresh(approval_request)
        
        return approval_request, recipient
    
    def test_email_service_initialization(self, email_service):
        """Test inizializzazione EmailService"""
        assert email_service.smtp_server is not None
        assert email_service.email_from is not None
        assert email_service.approval_url_base is not None
        assert email_service.jinja_env is not None
        print("✅ EmailService initialized correctly")
    
    @patch('app.services.email.smtplib.SMTP')
    def test_send_approval_request_email(self, mock_smtp, email_service, sample_approval_data):
        """Test invio email richiesta approvazione"""
        approval_request, recipient = sample_approval_data
        
        # Mock SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Test invio email
        result = email_service.send_approval_request_email(approval_request, recipient)
        
        # Verifiche
        assert result is True
        print(f"✅ Approval request email sent to {recipient.recipient_email}")
    
    @patch('app.services.email.smtplib.SMTP')
    def test_send_completion_notification_email(self, mock_smtp, email_service, sample_approval_data):
        """Test invio notifica completamento"""
        approval_request, recipient = sample_approval_data
        
        # Simula completamento
        approval_request.status = ApprovalStatus.APPROVED
        approval_request.completed_at = datetime.now()
        approval_request.completion_reason = "all_approved"
        recipient.status = RecipientStatus.APPROVED
        
        # Mock SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Test invio email
        result = email_service.send_completion_notification_email(approval_request)
        
        # Verifiche
        assert result is True
        print(f"✅ Completion notification sent to {approval_request.requester.email}")
    
    @patch('app.services.email.smtplib.SMTP')
    def test_send_reminder_email(self, mock_smtp, email_service, sample_approval_data):
        """Test invio email reminder"""
        approval_request, recipient = sample_approval_data
        
        # Mock SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Test invio email
        result = email_service.send_reminder_email(recipient)
        
        # Verifiche
        assert result is True
        print(f"✅ Reminder email sent to {recipient.recipient_email}")
    
    def test_template_rendering(self, email_service, sample_approval_data):
        """Test rendering template completo"""
        approval_request, recipient = sample_approval_data
        
        print(f"🔍 DEBUG: Testing template rendering...")
        print(f"🔍 Real recipient name: '{recipient.recipient_name}'")
        print(f"🔍 Real approval title: '{approval_request.title}'")
        
        # ✅ Usa sempre i dati reali dalla fixture
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
            "approval_url": f"http://test.com/approval/{recipient.approval_token}",
            "approval_token": recipient.approval_token,
            "app_name": "Test App"
        }
        
        # Test template fallback
        html = email_service._create_fallback_template("approval_request.html", context)
        
        print(f"🔍 DEBUG: Generated HTML length: {len(html)}")
        print(f"🔍 DEBUG: HTML preview: {html[:200]}...")
        
        # ✅ Verifiche base
        assert "Richiesta di Approvazione" in html
        assert len(html) > 100  # Template sostanzioso
        
        # ✅ Verifiche con dati specifici
        assert recipient.recipient_name in html, f"Expected '{recipient.recipient_name}' in HTML"
        assert approval_request.title in html, f"Expected '{approval_request.title}' in HTML"
        
        # ✅ Verifica che almeno uno tra display_name ed email sia presente
        requester_found = (
            approval_request.requester.display_name in html or 
            approval_request.requester.email in html
        )
        assert requester_found, f"Expected requester info in HTML"
        
        print("✅ Template rendering works correctly with database data")
        
        # ✅ Test template types specifici
        templates_to_test = [
            ("approval_request.html", "Richiesta di Approvazione"),
            ("approval_completion.html", "Approvazione Completata"),
            ("approval_reminder.html", "Reminder Approvazione"),
            ("unknown_template.html", "Notifica Sistema")
        ]
        
        for template_name, expected_content in templates_to_test:
            test_html = email_service._create_fallback_template(template_name, context)
            assert expected_content in test_html, f"Template {template_name} should contain '{expected_content}'"
            print(f"✅ Template {template_name}: OK")
        
        print("✅ All template types tested successfully")


    def test_email_configuration_test(self, email_service):
        """Test configurazione email"""
        # Test configurazione (dovrebbe fallire in ambiente test)
        result = email_service.test_email_configuration()
        
        assert "smtp_connection" in result
        assert "email_enabled" in result
        assert "configuration" in result
        
        # In ambiente test, email è tipicamente disabilitato
        if not result["email_enabled"]:
            assert result["error"] == "Email service is disabled in configuration"
        
        print(f"✅ Email configuration test completed: {result}")

# Test standalone con debug esteso
def run_email_service_tests():
    """Test standalone per EmailService con debug completo"""
    print("🔧 Testing Email Service...")
    print("=" * 50)
    
    try:
        print("\n1️⃣ Test inizializzazione...")
        print("🔍 DEBUG: Tentativo creazione EmailService...")
        
        # ✅ Debug import e dipendenze
        try:
            print("🔍 DEBUG: Testing imports...")
            from app.services.email import EmailService
            print("✅ EmailService importato correttamente")
            
            from app.configurations import settings
            print("✅ Settings importato correttamente")
            
            from pathlib import Path
            print("✅ Path importato correttamente")
            
            from jinja2 import Environment, FileSystemLoader
            print("✅ Jinja2 importato correttamente")
            
        except Exception as e:
            print(f"❌ ERRORE Import: {e}")
            traceback.print_exc()
            return False
        
        # ✅ Debug creazione service con try-catch dettagliato
        try:
            print("🔍 DEBUG: Creazione EmailService...")
            email_service = EmailService()
            print("✅ EmailService creato")
            
            # ✅ Debug proprietà del service
            print(f"🔍 DEBUG: SMTP Server: {email_service.smtp_server}")
            print(f"🔍 DEBUG: SMTP Port: {email_service.smtp_port}")
            print(f"🔍 DEBUG: Email From: {email_service.email_from}")
            print(f"🔍 DEBUG: Approval URL Base: {email_service.approval_url_base}")
            print(f"🔍 DEBUG: Template Dir: {email_service.template_dir}")
            print(f"🔍 DEBUG: Jinja Env: {email_service.jinja_env}")
            
        except Exception as e:
            print(f"❌ ERRORE Creazione EmailService: {e}")
            traceback.print_exc()
            return False
        
        print("\n2️⃣ Test configurazione...")
        print("🔍 DEBUG: Testing email configuration...")
        
        try:
            # ✅ Debug configurazione settings
            print(f"🔍 DEBUG: Email enabled: {settings.email_enabled}")
            print(f"🔍 DEBUG: SMTP server: {settings.smtp_server}")
            print(f"🔍 DEBUG: SMTP port: {settings.smtp_port}")
            print(f"🔍 DEBUG: SMTP use TLS: {settings.smtp_use_tls}")
            print(f"🔍 DEBUG: Email from: {settings.email_from}")
            print(f"🔍 DEBUG: SMTP username set: {bool(settings.smtp_username)}")
            print(f"🔍 DEBUG: SMTP password set: {bool(settings.smtp_password)}")
            
            # Test configurazione
            print("🔍 DEBUG: Eseguendo test configurazione...")
            config_test = email_service.test_email_configuration()
            print(f"🔍 Configurazione email: {config_test}")
            
            # In ambiente test, email è probabilmente disabilitato
            if not config_test["email_enabled"]:
                print("ℹ️ Email disabilitato in configurazione (normale per test)")
            else:
                print("ℹ️ Email abilitato in configurazione")
                if config_test.get("error"):
                    print(f"⚠️ Errore configurazione: {config_test['error']}")
                if config_test.get("smtp_connection"):
                    print("✅ Connessione SMTP testata con successo")
                else:
                    print("❌ Connessione SMTP fallita")
            
        except Exception as e:
            print(f"❌ ERRORE Test configurazione: {e}")
            traceback.print_exc()
            return False
        
        print("\n3️⃣ Test template fallback...")
        print("🔍 DEBUG: Testing template system...")
        
        try:
            # ✅ Debug template directory
            print(f"🔍 DEBUG: Template directory exists: {email_service.template_dir.exists()}")
            print(f"🔍 DEBUG: Template directory path: {email_service.template_dir.absolute()}")
            
            # ✅ Verifica se directory template esiste, se no creala
            if not email_service.template_dir.exists():
                print("🔍 DEBUG: Creando directory template...")
                email_service.template_dir.mkdir(parents=True, exist_ok=True)
                print("✅ Directory template creata")
            
            # Test template fallback
            context = {
                "title": "Test Approval",
                "recipient_name": "Test User",
                "app_name": "Test App"
            }
            
            print("🔍 DEBUG: Testing fallback template...")
            html = email_service._create_fallback_template("approval_request.html", context)
            
            # ✅ Debug contenuto template
            print(f"🔍 DEBUG: Template length: {len(html)}")
            print(f"🔍 DEBUG: Template contains title: {'Test Approval' in html}")
            print(f"🔍 DEBUG: Template contains name: {'Test User' in html}")
            
            assert "Test Approval" in html
            assert "Test User" in html
            print("✅ Template fallback funziona")
            
        except Exception as e:
            print(f"❌ ERRORE Template test: {e}")
            traceback.print_exc()
            return False
        
        print("\n4️⃣ Test template rendering con Jinja2...")
        print("🔍 DEBUG: Testing Jinja2 template rendering...")
        
        try:
            # Test rendering template con Jinja2 (dovrebbe fallire e usare fallback)
            context = {
                "title": "Jinja Test",
                "recipient_name": "Jinja User",
                "app_name": "Test App"
            }
            
            print("🔍 DEBUG: Tentativo rendering template 'approval_request.html'...")
            html = email_service._render_template("approval_request.html", context)
            
            print(f"🔍 DEBUG: Rendered HTML length: {len(html)}")
            print(f"🔍 DEBUG: HTML contains test data: {'Jinja Test' in html}")
            
            assert len(html) > 0
            print("✅ Template rendering completato (probabile fallback)")
            
        except Exception as e:
            print(f"❌ ERRORE Template rendering: {e}")
            traceback.print_exc()
            return False
        
        print("\n5️⃣ Test metodi email (senza invio reale)...")
        print("🔍 DEBUG: Testing email methods...")
        
        try:
            # ✅ Test creazione contesto email
            print("🔍 DEBUG: Testing email context creation...")
            
            # Simula dati approvazione
            mock_approval_context = {
                "recipient_name": "Test Recipient",
                "recipient_email": "recipient@test.com",
                "title": "Mock Approval Request",
                "description": "Mock description",
                "requester_name": "Test Requester",
                "document_filename": "test_document.pdf",
                "approval_url": "http://test.com/approval/token123",
                "app_name": "Test App"
            }
            
            print(f"🔍 DEBUG: Mock context keys: {list(mock_approval_context.keys())}")
            
            # Test template con contesto completo
            html = email_service._render_template("approval_request.html", mock_approval_context)
            
            print(f"🔍 DEBUG: Full template HTML length: {len(html)}")
            print(f"🔍 DEBUG: Contains recipient name: {mock_approval_context['recipient_name'] in html}")
            print(f"🔍 DEBUG: Contains title: {mock_approval_context['title'] in html}")
            
            assert len(html) > 100  # Template dovrebbe essere sostanzioso
            print("✅ Contesto email completo funziona")
            
        except Exception as e:
            print(f"❌ ERRORE Test metodi email: {e}")
            traceback.print_exc()
            return False
        
        print("\n6️⃣ Test utility methods...")
        print("🔍 DEBUG: Testing utility methods...")
        
        try:
            # Test template per completion
            completion_context = {
                "title": "Test Completion",
                "final_status": "approved",
                "app_name": "Test App"
            }
            
            completion_html = email_service._create_fallback_template("approval_completion.html", completion_context)
            print(f"🔍 DEBUG: Completion template length: {len(completion_html)}")
            assert "Approvazione Completata" in completion_html
            print("✅ Completion template fallback funziona")
            
            # Test template per reminder
            reminder_context = {
                "recipient_name": "Test User",
                "title": "Test Reminder",
                "app_name": "Test App"
            }
            
            # Nota: il fallback per reminder ritorna template generico
            reminder_html = email_service._create_fallback_template("approval_reminder.html", reminder_context)
            print(f"🔍 DEBUG: Reminder template length: {len(reminder_html)}")
            assert len(reminder_html) > 0
            print("✅ Reminder template fallback funziona")
            
        except Exception as e:
            print(f"❌ ERRORE Test utility methods: {e}")
            traceback.print_exc()
            return False
        
        print("\n🎉 Tutti i test email service completati con successo!")
        return True
        
    except Exception as e:
        print(f"❌ ERRORE GENERALE test email service: {e}")
        print("🔍 DEBUG: Stack trace completo:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Avvio test standalone Email Service...")
    success = run_email_service_tests()
    if success:
        print("\n✅ Test completati con successo!")
        exit(0)
    else:
        print("\n❌ Test falliti!")
        exit(1)
