"""
Script per verificare le dipendenze dell'EmailService
"""

def check_dependencies():
    print("🔍 Verifica dipendenze EmailService...")
    
    try:
        print("\n1. Import base Python...")
        import smtplib
        import ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        print("✅ Email modules OK")
        
        print("\n2. Import pathlib...")
        from pathlib import Path
        print("✅ Pathlib OK")
        
        print("\n3. Import Jinja2...")
        from jinja2 import Environment, FileSystemLoader
        print("✅ Jinja2 OK")
        
        print("\n4. Import app modules...")
        import sys
        import os
        
        # Setup path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from app.configurations import settings
        print("✅ App config OK")
        
        print("\n5. Import app models...")
        from app.db.models import ApprovalRequest, ApprovalRecipient, User
        print("✅ App models OK")
        
        print("\n6. Test settings access...")
        print(f"   - Email enabled: {getattr(settings, 'email_enabled', 'NOT_SET')}")
        print(f"   - SMTP server: {getattr(settings, 'smtp_server', 'NOT_SET')}")
        print(f"   - Email from: {getattr(settings, 'email_from', 'NOT_SET')}")
        print("✅ Settings access OK")
        
        print("\n7. Import EmailService...")
        from app.services.email import EmailService
        print("✅ EmailService import OK")
        
        print("\n8. Create EmailService instance...")
        service = EmailService()
        print("✅ EmailService instance OK")
        
        print(f"\n📊 EmailService properties:")
        print(f"   - SMTP server: {service.smtp_server}")
        print(f"   - SMTP port: {service.smtp_port}")
        print(f"   - Email from: {service.email_from}")
        print(f"   - Template dir: {service.template_dir}")
        print(f"   - Template dir exists: {service.template_dir.exists()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_dependencies()
    if success:
        print("\n🎉 Tutte le dipendenze EmailService verificate!")
    else:
        print("\n💥 Problema con le dipendenze!")
    exit(0 if success else 1)
