"""
Test email service con server SMTP reale
Invia email alla tua casella per verifica
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.email import EmailService
from app.configurations import settings
from datetime import datetime, timedelta
import uuid

def test_email_configuration():
    """Test configurazione email reale"""
    print("🔍 Test configurazione email reale...")
    print("=" * 50)
    
    email_service = EmailService()
    
    # Mostra configurazione corrente
    print(f"📧 Email enabled: {settings.email_enabled}")
    print(f"🌐 SMTP server: {settings.smtp_server}:{settings.smtp_port}")
    print(f"👤 SMTP username: {settings.smtp_username}")
    print(f"📬 Email from: {settings.email_from}")
    print(f"🔐 TLS enabled: {settings.smtp_use_tls}")
    print(f"🔑 Password set: {bool(settings.smtp_password)}")
    
    if not settings.email_enabled:
        print("⚠️ Email è disabilitato! Abilita EMAIL_ENABLED=True nel .env")
        return False
    
    if not settings.smtp_username or not settings.smtp_password:
        print("⚠️ Credenziali SMTP mancanti!")
        return False
    
    # Test connessione SMTP
    print(f"\n🔌 Testing SMTP connection...")
    config_test = email_service.test_email_configuration()
    
    if config_test["smtp_connection"]:
        print("✅ Connessione SMTP riuscita!")
        return True
    else:
        print(f"❌ Connessione SMTP fallita: {config_test.get('error', 'Unknown error')}")
        return False

def send_test_email(recipient_email: str):
    """
    Invia email di test alla tua casella
    
    Args:
        recipient_email: La tua email dove ricevere il test
    """
    print(f"\n📧 Invio email di test a: {recipient_email}")
    print("=" * 50)
    
    try:
        email_service = EmailService()
        
        # ✅ Contesto per email di test
        context = {
            "recipient_name": "Test Recipient",
            "title": "Test Email Service - Funzionamento Reale",
            "description": "Questo è un test per verificare l'invio email con server SMTP reale",
            "requester_name": "Sistema DMS",
            "document_filename": "test_document.pdf",
            "approval_type": "any",
            "expires_at": datetime.now() + timedelta(days=7),
            "approval_url": f"{settings.approval_url_base}/test-token-123",
            "approval_token": "test-token-123",
            "app_name": settings.app_name,
            "created_at": datetime.now()
        }
        
        # ✅ Render template HTML
        html_body = email_service._render_template("approval_request.html", context)
        
        # ✅ Soggetto email
        subject = f"[{settings.app_name}] 🧪 Test Email Service - {datetime.now().strftime('%H:%M:%S')}"
        
        # ✅ Corpo testo alternativo
        text_body = f"""
Test Email Service - DMS

Ciao Test Recipient,

Questo è un test per verificare il funzionamento del servizio email con server SMTP reale.

Dettagli Test:
- Titolo: {context['title']}
- Inviato da: {settings.email_from}
- Destinatario: {recipient_email}
- Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Se ricevi questa email, il servizio funziona correttamente! ✅

---
{settings.app_name}
Sistema di Test Email
        """
        
        print(f"📝 Soggetto: {subject}")
        print(f"📤 Da: {settings.email_from}")
        print(f"📥 A: {recipient_email}")
        print(f"📏 Lunghezza HTML: {len(html_body)} caratteri")
        
        # ✅ Invio email
        print(f"\n🚀 Invio in corso...")
        
        success = email_service._send_email(
            to_email=recipient_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
        
        if success:
            print("✅ Email inviata con successo!")
            print(f"📮 Controlla la tua casella: {recipient_email}")
            print(f"⏰ L'email dovrebbe arrivare entro pochi minuti")
            return True
        else:
            print("❌ Errore nell'invio email")
            return False
            
    except Exception as e:
        print(f"💥 Errore durante invio: {e}")
        import traceback
        traceback.print_exc()
        return False

def send_multiple_email_types(recipient_email: str):
    """
    Invia tutti i tipi di email disponibili per test completo
    
    Args:
        recipient_email: La tua email dove ricevere i test
    """
    print(f"\n📧 Test multipli tipi email a: {recipient_email}")
    print("=" * 50)
    
    email_service = EmailService()
    results = {}
    
    # ✅ Test 1: Richiesta Approvazione
    try:
        approval_context = {
            "recipient_name": "Test User",
            "title": "Documento Test Approvazione",
            "description": "Test richiesta approvazione con server reale",
            "requester_name": "Test Requester",
            "document_filename": "test_approval.pdf",
            "approval_type": "all",
            "expires_at": datetime.now() + timedelta(days=7),
            "approval_url": f"{settings.approval_url_base}/test-approval-123",
            "app_name": settings.app_name
        }
        
        html_body = email_service._render_template("approval_request.html", approval_context)
        
        success = email_service._send_email(
            to_email=recipient_email,
            subject=f"[TEST 1/3] Richiesta Approvazione - {datetime.now().strftime('%H:%M')}", 
            html_body=html_body
        )
        
        results["approval_request"] = success
        print(f"📋 Test 1 - Richiesta Approvazione: {'✅' if success else '❌'}")
        
    except Exception as e:
        results["approval_request"] = False
        print(f"📋 Test 1 - Error: {e}")
    
    # ✅ Test 2: Completamento Approvazione
    try:
        completion_context = {
            "requester_name": "Test User",
            "title": "Documento Test Completato",
            "document_filename": "test_completion.pdf",
            "final_status": "approved",
            "completion_reason": "all_approved",
            "completed_at": datetime.now(),
            "created_at": datetime.now() - timedelta(hours=2),
            "approved_count": 2,
            "rejected_count": 0,
            "total_recipients": 2,
            "approval_type": "all",
            "app_name": settings.app_name
        }
        
        html_body = email_service._render_template("approval_completion.html", completion_context)
        
        success = email_service._send_email(
            to_email=recipient_email,
            subject=f"[TEST 2/3] Approvazione Completata - {datetime.now().strftime('%H:%M')}", 
            html_body=html_body
        )
        
        results["completion"] = success
        print(f"✅ Test 2 - Completamento: {'✅' if success else '❌'}")
        
    except Exception as e:
        results["completion"] = False
        print(f"✅ Test 2 - Error: {e}")
    
    # ✅ Test 3: Reminder
    try:
        reminder_context = {
            "recipient_name": "Test User",
            "title": "Documento Test Reminder",
            "document_filename": "test_reminder.pdf",
            "requester_name": "Test Requester",
            "days_left": 2,
            "expires_at": datetime.now() + timedelta(days=2),
            "approval_url": f"{settings.approval_url_base}/test-reminder-123",
            "app_name": settings.app_name
        }
        
        html_body = email_service._render_template("approval_reminder.html", reminder_context)
        
        success = email_service._send_email(
            to_email=recipient_email,
            subject=f"[TEST 3/3] Reminder Approvazione - {datetime.now().strftime('%H:%M')}", 
            html_body=html_body
        )
        
        results["reminder"] = success
        print(f"⏰ Test 3 - Reminder: {'✅' if success else '❌'}")
        
    except Exception as e:
        results["reminder"] = False
        print(f"⏰ Test 3 - Error: {e}")
    
    # ✅ Risultati finali
    successful_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\n📊 Risultati Test Email:")
    print(f"✅ Successi: {successful_tests}/{total_tests}")
    
    for test_name, success in results.items():
        print(f"   - {test_name}: {'✅ OK' if success else '❌ FAILED'}")
    
    print(f"\n📮 Controlla la tua casella: {recipient_email}")
    print(f"🔍 Dovresti aver ricevuto {successful_tests} email di test")
    
    return results

def main():
    """Test principale email service reale"""
    print("🧪 TEST EMAIL SERVICE CON SERVER REALE")
    print("=" * 60)
    
    # ✅ Input email destinatario
    recipient_email = input("\n📧 Inserisci la tua email per ricevere i test: ").strip()
    
    if not recipient_email or "@" not in recipient_email:
        print("❌ Email non valida!")
        return
    
    # ✅ Test configurazione
    if not test_email_configuration():
        print("\n💥 Configurazione email non valida! Controlla le impostazioni.")
        return
    
    # ✅ Menu test
    print(f"\n🎯 Scegli tipo di test:")
    print("1. Test semplice (1 email)")
    print("2. Test completo (3 tipi di email)")
    print("3. Solo verifica configurazione")
    
    choice = input("\nScelta (1/2/3): ").strip()
    
    if choice == "1":
        send_test_email(recipient_email)
    elif choice == "2":
        send_multiple_email_types(recipient_email)
    elif choice == "3":
        print("✅ Configurazione già verificata sopra!")
    else:
        print("❌ Scelta non valida!")
        
    print(f"\n🏁 Test completato!")

if __name__ == "__main__":
    main()
