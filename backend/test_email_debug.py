#!/usr/bin/env python3

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_email_service():
    """Test completo del servizio email con debug"""
    print("🧪 TEST EMAIL SERVICE CON DEBUG COMPLETO")
    print("=" * 60)
    
    # 🔧 Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # 🔧 Import service
    from app.services.email import email_service
    
    # 🔍 Test 1: Configuration check
    print("\n📋 STEP 1: Verifica Configurazione")
    print("-" * 40)
    
    # 🔍 Test 2: SMTP connection
    print("\n🔌 STEP 2: Test Connessione SMTP")
    print("-" * 40)
    
    connection_result = email_service.test_smtp_connection()
    if not connection_result["success"]:
        print(f"❌ Test connessione fallito: {connection_result.get('error')}")
        return False
    
    print("✅ Connessione SMTP riuscita!")
    
    # 🔍 Test 3: Send test email
    print("\n📧 STEP 3: Invio Email di Test")
    print("-" * 40)
    
    # 🔧 Get recipient email
    recipient_email = input("\n📧 Inserisci la tua email per test: ").strip()
    if not recipient_email or "@" not in recipient_email:
        print("❌ Email non valida!")
        return False
    
    # 🔧 Prepare test data
    test_approval_data = {
        'title': 'Test Email Service - Debug',
        'description': 'Questo è un test per verificare il funzionamento del servizio email',
        'document_filename': 'test_document.pdf',
        'requester_name': 'Test System',
        'created_at': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'expires_at': None,
        'approval_token': 'test-token-12345'
    }
    
    # 🔧 Send test email
    success = email_service.send_approval_request_email(
        recipient_email=recipient_email,
        recipient_name="Test User",
        approval_data=test_approval_data
    )
    
    if success:
        print("✅ Email di test inviata!")
        print(f"📮 Controlla la tua casella: {recipient_email}")
        print("⏰ L'email dovrebbe arrivare entro pochi minuti")
        print("📁 Controlla anche la cartella spam/junk")
    else:
        print("❌ Invio email fallito! Controlla i log sopra per dettagli.")
    
    return success

if __name__ == "__main__":
    test_email_service()
