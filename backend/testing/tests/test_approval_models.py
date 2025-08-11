import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup

import pytest
import uuid
from datetime import datetime, timedelta
from app.db.models import (
    ApprovalRequest, ApprovalRecipient, AuditLog, Document, User, 
    UserRole, ApprovalType, ApprovalStatus, RecipientStatus
)
from app.utils.security import hash_password

@pytest.mark.db
class TestApprovalModels:
    """Test completi per i modelli database delle approvazioni"""
    
    def test_create_approval_request_basic(self, db_session):
        """Test creazione richiesta approvazione base"""
        # Genera ID univoco
        unique_id = str(uuid.uuid4())[:8]
        
        # ✅ Crea utente PRIMA e commit esplicito
        user = User(
            email=f"approver_{unique_id}@test.com",
            password_hash=hash_password("testpass"),
            display_name=f"Test Approver {unique_id}",
            role=UserRole.USER
        )
        db_session.add(user)
        db_session.commit()  # ← COMMIT ESPLICITO per ottenere user.id
        db_session.refresh(user)  # ← REFRESH per assicurarsi che user.id sia popolato
        
        # Verifica che user.id esista
        assert user.id is not None, "User ID should not be None after commit"
        
        # ✅ Crea documento con owner_id valido
        document = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,  # ← Ora user.id è garantito essere valido
            filename="test_approval_doc.pdf",
            original_filename="test_approval_doc.pdf",
            storage_path=f"/fake/path/{unique_id}",
            content_type="application/pdf",
            size=1024.0,
            file_hash="fakehash123456"
        )
        db_session.add(document)
        db_session.commit()  # ← COMMIT ESPLICITO per ottenere document.id
        db_session.refresh(document)
        
        # Verifica che document sia stato creato correttamente
        assert document.id is not None
        assert document.owner_id == user.id
        
        # ✅ Crea approval request
        approval_request = ApprovalRequest(
            document_id=document.id,
            requester_id=user.id,
            title="Test Approval Request",
            description="Descrizione di test per la richiesta di approvazione",
            approval_type=ApprovalType.ALL,
            expires_at=datetime.now() + timedelta(days=7),
            requester_comments="Commenti del richiedente per il test"
        )
        
        db_session.add(approval_request)
        db_session.commit()
        db_session.refresh(approval_request)
        
        # Verifiche finali
        assert approval_request.id is not None
        assert len(approval_request.id) == 36  # UUID format
        assert approval_request.title == "Test Approval Request"
        assert approval_request.status == ApprovalStatus.PENDING
        assert approval_request.approval_type == ApprovalType.ALL
        assert approval_request.document_id == document.id
        assert approval_request.requester_id == user.id
    
    def test_create_approval_request_any_type(self, db_session):
        """Test creazione richiesta con tipo ANY"""
        unique_id = str(uuid.uuid4())[:8]
        
        # ✅ Pattern: User -> commit -> Document -> commit -> ApprovalRequest
        user = User(
            email=f"requester_any_{unique_id}@test.com",
            password_hash=hash_password("testpass"),
            display_name="Any Type Requester"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        document = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            filename="any_type_doc.pdf",
            original_filename="any_type_doc.pdf",
            storage_path="/fake/any/path",
            content_type="application/pdf",
            size=2048.0,
            file_hash="anyhash789"
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        approval_request = ApprovalRequest(
            document_id=document.id,
            requester_id=user.id,
            title="Any Type Approval",
            approval_type=ApprovalType.ANY,
            expires_at=datetime.now() + timedelta(days=3)
        )
        
        db_session.add(approval_request)
        db_session.commit()
        
        assert approval_request.approval_type == ApprovalType.ANY
        assert approval_request.title == "Any Type Approval"
    
    def test_create_approval_recipients_multiple(self, db_session):
        """Test creazione multipli destinatari approvazione"""
        unique_id = str(uuid.uuid4())[:8]
        
        # ✅ Setup completo con commit espliciti
        user = User(
            email=f"requester_multi_{unique_id}@test.com",
            password_hash=hash_password("testpass"),
            display_name=f"Multi Requester {unique_id}"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        document = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            filename="multi_recipients.pdf",
            original_filename="multi_recipients.pdf", 
            storage_path="/fake/multi/path",
            content_type="application/pdf",
            size=1536.0,
            file_hash="multihash123"
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        approval_request = ApprovalRequest(
            document_id=document.id,
            requester_id=user.id,
            title="Multi Recipients Test",
            approval_type=ApprovalType.ALL
        )
        db_session.add(approval_request)
        db_session.commit()
        db_session.refresh(approval_request)
        
        # Crea destinatari
        recipients_data = [
            ("approver1@test.com", "Approver One", 5),
            ("approver2@test.com", "Approver Two", 3),
            ("approver3@test.com", None, 7),
            ("manager@test.com", "Manager User", 2)
        ]
        
        recipients = []
        for email, name, expire_days in recipients_data:
            recipient = ApprovalRecipient(
                approval_request_id=approval_request.id,
                recipient_email=email,
                recipient_name=name,
                expires_at=datetime.now() + timedelta(days=expire_days)
            )
            recipients.append(recipient)
        
        db_session.add_all(recipients)
        db_session.commit()
        
        # Verifiche
        saved_recipients = db_session.query(ApprovalRecipient).filter(
            ApprovalRecipient.approval_request_id == approval_request.id
        ).all()
        
        assert len(saved_recipients) == 4
        assert all(r.status == RecipientStatus.PENDING for r in saved_recipients)
        assert all(r.approval_token is not None for r in saved_recipients)
    
    def test_approval_decision_workflow_all_approve(self, db_session):
        """Test workflow decisione con tipo ALL - tutti approvano"""
        unique_id = str(uuid.uuid4())[:8]
        
        # ✅ Setup con commit pattern
        user = User(
            email=f"decision_all_{unique_id}@test.com", 
            password_hash=hash_password("testpass"),
            display_name="Decision Test User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        document = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            filename="decision_all_test.pdf",
            original_filename="decision_all_test.pdf",
            storage_path="/fake/decision/path", 
            content_type="application/pdf",
            size=1024.0,
            file_hash="decisionhash123"
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        approval_request = ApprovalRequest(
            document_id=document.id,
            requester_id=user.id,
            title="ALL Type Decision Test",
            approval_type=ApprovalType.ALL
        )
        db_session.add(approval_request)
        db_session.commit()
        db_session.refresh(approval_request)
        
        # Crea destinatari
        recipients = []
        for i in range(3):
            recipient = ApprovalRecipient(
                approval_request_id=approval_request.id,
                recipient_email=f"approver{i+1}@test.com",
                recipient_name=f"Approver {i+1}"
            )
            recipients.append(recipient)
        
        db_session.add_all(recipients)
        db_session.commit()
        
        # Simula approvazioni
        for i, recipient in enumerate(recipients):
            recipient.status = RecipientStatus.APPROVED
            recipient.decision = "approved"
            recipient.comments = f"Approved by approver {i+1}"
            recipient.responded_at = datetime.now()
        
        db_session.commit()
        
        # Verifiche
        approved_count = len([r for r in recipients if r.status == RecipientStatus.APPROVED])
        assert approved_count == 3
    
    def test_approval_decision_workflow_any_reject(self, db_session):
        """Test workflow decisione con tipo ANY - uno rifiuta"""
        unique_id = str(uuid.uuid4())[:8]
        
        # ✅ Setup con commit pattern
        user = User(
            email=f"decision_any_{unique_id}@test.com",
            password_hash=hash_password("testpass")
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        document = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            filename="decision_any_test.pdf",
            original_filename="decision_any_test.pdf",
            storage_path="/fake/any/decision/path",
            content_type="application/pdf",
            size=2048.0,
            file_hash="anydecisionhash"
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        approval_request = ApprovalRequest(
            document_id=document.id,
            requester_id=user.id,
            title="ANY Type Decision Test",
            approval_type=ApprovalType.ANY
        )
        db_session.add(approval_request)
        db_session.commit()
        db_session.refresh(approval_request)
        
        # Crea destinatari
        recipient1 = ApprovalRecipient(
            approval_request_id=approval_request.id,
            recipient_email="first@test.com",
            recipient_name="First Approver"
        )
        recipient2 = ApprovalRecipient(
            approval_request_id=approval_request.id,
            recipient_email="second@test.com", 
            recipient_name="Second Approver"
        )
        db_session.add_all([recipient1, recipient2])
        db_session.commit()
        
        # Primo rifiuta
        recipient1.status = RecipientStatus.REJECTED
        recipient1.decision = "rejected"
        recipient1.comments = "Needs significant improvements"
        recipient1.responded_at = datetime.now()
        
        db_session.commit()
        
        # Verifiche
        assert recipient1.status == RecipientStatus.REJECTED
        assert recipient2.status == RecipientStatus.PENDING
    
    def test_approval_recipient_token_uniqueness(self, db_session):
        """Test unicità dei token di approvazione"""
        unique_id = str(uuid.uuid4())[:8]
        
        # ✅ Setup con commit pattern
        user = User(
            email=f"token_test_{unique_id}@test.com",
            password_hash=hash_password("testpass")
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        document = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            filename="token_test.pdf",
            original_filename="token_test.pdf",
            storage_path="/fake/token/path",
            content_type="application/pdf",
            size=1024.0,
            file_hash="tokenhash"
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        approval_request = ApprovalRequest(
            document_id=document.id,
            requester_id=user.id,
            title="Token Uniqueness Test"
        )
        db_session.add(approval_request)
        db_session.commit()
        db_session.refresh(approval_request)
        
        # Crea molti destinatari
        recipients = []
        for i in range(10):
            recipient = ApprovalRecipient(
                approval_request_id=approval_request.id,
                recipient_email=f"token_user_{i}@test.com",
                recipient_name=f"Token User {i}"
            )
            recipients.append(recipient)
        
        db_session.add_all(recipients)
        db_session.commit()
        
        # Verifica unicità token
        tokens = [r.approval_token for r in recipients]
        assert len(tokens) == 10
        assert len(set(tokens)) == 10  # Tutti diversi
    
    def test_audit_log_creation_comprehensive(self, db_session):
        """Test creazione audit log completo"""
        unique_id = str(uuid.uuid4())[:8]
        
        # ✅ Setup con commit pattern
        user = User(
            email=f"audit_{unique_id}@test.com",
            password_hash=hash_password("testpass"),
            display_name=f"Audit User {unique_id}"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        document = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            filename="audit_test.pdf",
            original_filename="audit_test.pdf",
            storage_path="/fake/audit/path",
            content_type="application/pdf", 
            size=1024.0,
            file_hash="audithash123"
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        approval_request = ApprovalRequest(
            document_id=document.id,
            requester_id=user.id,
            title="Audit Log Test",
            description="Test per audit logging"
        )
        db_session.add(approval_request)
        db_session.commit()
        db_session.refresh(approval_request)
        
        # Crea audit logs
        audit_logs = [
            AuditLog(
                approval_request_id=approval_request.id,
                user_id=user.id,
                action="approval_request_created",
                details="Richiesta approvazione creata via API",
                metadata_json='{"client": "web", "version": "1.0"}',
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 (TestClient)"
            ),
            AuditLog(
                approval_request_id=approval_request.id,
                user_id=user.id,
                action="recipients_added",
                details="Aggiunti 3 destinatari alla richiesta",
                metadata_json='{"recipients_count": 3}',
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 (TestClient)"
            )
        ]
        
        db_session.add_all(audit_logs)
        db_session.commit()
        
        # Verifiche
        saved_logs = db_session.query(AuditLog).filter(
            AuditLog.approval_request_id == approval_request.id
        ).all()
        
        assert len(saved_logs) == 2
        assert any(log.action == "approval_request_created" for log in saved_logs)
    
    def test_recipient_expiration_handling(self, db_session):
        """Test gestione scadenza destinatari"""
        unique_id = str(uuid.uuid4())[:8]
        
        # ✅ Setup con commit pattern
        user = User(
            email=f"expiration_{unique_id}@test.com",
            password_hash=hash_password("testpass")
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        document = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            filename="expiration_test.pdf",
            original_filename="expiration_test.pdf",
            storage_path="/fake/expiration/path",
            content_type="application/pdf",
            size=1024.0,
            file_hash="exphash123"
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        approval_request = ApprovalRequest(
            document_id=document.id,
            requester_id=user.id,
            title="Expiration Test"
        )
        db_session.add(approval_request)
        db_session.commit()
        db_session.refresh(approval_request)
        
        # Crea destinatari con scadenze
        now = datetime.now()
        recipients = [
            ApprovalRecipient(
                approval_request_id=approval_request.id,
                recipient_email="expired@test.com",
                expires_at=now - timedelta(days=1),
                status=RecipientStatus.EXPIRED
            ),
            ApprovalRecipient(
                approval_request_id=approval_request.id,
                recipient_email="expiring_soon@test.com",
                expires_at=now + timedelta(hours=1),
                status=RecipientStatus.PENDING
            )
        ]
        
        db_session.add_all(recipients)
        db_session.commit()
        
        # Verifiche
        expired_count = db_session.query(ApprovalRecipient).filter(
            ApprovalRecipient.status == RecipientStatus.EXPIRED,
            ApprovalRecipient.approval_request_id == approval_request.id
        ).count()
        
        assert expired_count == 1
    
    def test_relationships_cascade_delete(self, db_session):
        """Test eliminazione a cascata delle relationships"""
        unique_id = str(uuid.uuid4())[:8]
        
        # ✅ Setup con commit pattern
        user = User(
            email=f"cascade_{unique_id}@test.com",
            password_hash=hash_password("testpass")
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        document = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            filename="cascade_test.pdf",
            original_filename="cascade_test.pdf",
            storage_path="/fake/cascade/path",
            content_type="application/pdf",
            size=1024.0,
            file_hash="cascadehash"
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        approval_request = ApprovalRequest(
            document_id=document.id,
            requester_id=user.id,
            title="Cascade Delete Test"
        )
        db_session.add(approval_request)
        db_session.commit()
        db_session.refresh(approval_request)
        
        # Aggiungi recipients
        recipients = []
        for i in range(3):
            recipient = ApprovalRecipient(
                approval_request_id=approval_request.id,
                recipient_email=f"cascade{i}@test.com"
            )
            recipients.append(recipient)
        
        db_session.add_all(recipients)
        db_session.commit()
        
        # Verifica creazione
        assert len(approval_request.recipients) == 3
        
        # Test cascade delete
        approval_request_id = approval_request.id
        db_session.delete(approval_request)
        db_session.commit()
        
        # Verifica eliminazione
        remaining_recipients = db_session.query(ApprovalRecipient).filter(
            ApprovalRecipient.approval_request_id == approval_request_id
        ).all()
        assert len(remaining_recipients) == 0


def run_approval_models_tests():
    """Test standalone per modelli approvazioni"""
    print("🔧 Testing Approval Models (Complete)...")
    print("=" * 60)
    
    from app.db.base import SessionLocal
    
    db = SessionLocal()
    
    try:
        unique_id = str(uuid.uuid4())[:8]
        
        print("\n1️⃣ Test creazione modelli base...")
        
        # ✅ Crea utente PRIMA
        user = User(
            email=f"standalone_approval_{unique_id}@test.com",
            password_hash=hash_password("testpass"),
            display_name="Standalone Test User",
            role=UserRole.ADMIN
        )
        db.add(user)
        db.commit()  # ← COMMIT QUI per ottenere user.id
        db.refresh(user)  # ← Assicurati che user.id sia popolato
        
        print(f"✅ Utente creato con ID: {user.id}")
        
        # ✅ Ora crea documento con owner_id valido
        document_id = str(uuid.uuid4())
        document = Document(
            id=document_id,
            owner_id=user.id,  # ← Ora user.id è valido
            filename="standalone_test.pdf",
            original_filename="standalone_test.pdf",
            storage_path="/fake/standalone/path",
            content_type="application/pdf",
            size=2048.0, 
            file_hash="standalonehash123"
        )
        db.add(document)
        db.commit()
        print("✅ Documento creato")
        
        # ... rest of the test logic
        
    except Exception as e:
        print(f"❌ Errore test models: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = run_approval_models_tests()
    exit(0 if success else 1)
