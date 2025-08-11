import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup

import pytest
import uuid
from datetime import datetime, timedelta
from app.services.approval import ApprovalService
from app.db.schemas import ApprovalRequestCreate, ApprovalRecipientCreate, ApprovalDecisionRequest
from app.db.models import (
    User, Document, ApprovalRequest, ApprovalRecipient, AuditLog,
    UserRole, ApprovalType, ApprovalStatus, RecipientStatus
)
from app.utils.security import hash_password
from app.utils.exceptions import NotFoundError, ValidationError, PermissionDeniedError

@pytest.mark.db
class TestApprovalService:
    """Test per ApprovalService con isolamento database"""
    
    @pytest.fixture
    def approval_service(self, db_session):
        """Fixture per il service con sessione database"""
        return ApprovalService(db_session)
    
    @pytest.fixture
    def sample_user_and_document(self, db_session):
        """Fixture per creare utente e documento di test UNIVOCI per ogni test"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Crea utente
        user = User(
            email=f"test_approval_service_{unique_id}@test.com",
            password_hash=hash_password("testpass"),
            display_name=f"Test User {unique_id}",
            role=UserRole.USER
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Crea documento UNIVOCO per ogni test
        document = Document(
            id=str(uuid.uuid4()),  # ✅ UUID univoco
            owner_id=user.id,
            filename=f"test_doc_{unique_id}.pdf",
            original_filename=f"test_doc_{unique_id}.pdf",
            storage_path=f"/fake/path/{unique_id}",
            content_type="application/pdf",
            size=1024.0,
            file_hash=f"hash_{unique_id}"
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        return user, document
    
    def test_create_approval_request_success(self, approval_service, sample_user_and_document):
        """Test creazione richiesta approvazione con successo"""
        user, document = sample_user_and_document
        
        # Dati richiesta con email univoche
        unique_id = str(uuid.uuid4())[:8]
        request_data = ApprovalRequestCreate(
            document_id=document.id,
            title="Test Approval Request",
            description="Richiesta di test per il service",
            approval_type=ApprovalType.ALL,
            expires_at=datetime.now() + timedelta(days=7),
            recipients=[
                ApprovalRecipientCreate(
                    recipient_email=f"approver1_{unique_id}@test.com",  # ✅ Email univoca
                    recipient_name="Test Approver 1"
                ),
                ApprovalRecipientCreate(
                    recipient_email=f"approver2_{unique_id}@test.com",  # ✅ Email univoca
                    recipient_name="Test Approver 2"
                )
            ],
            requester_comments="Commenti del richiedente"
        )
        
        # Crea richiesta
        response = approval_service.create_approval_request(
            request_data=request_data,
            requester_id=user.id,
            client_ip="192.168.1.1",
            user_agent="TestAgent/1.0"
        )
        
        # Verifiche
        assert response.id is not None
        assert response.title == "Test Approval Request"
        assert response.approval_type == ApprovalType.ALL
        assert response.status == ApprovalStatus.PENDING
        assert response.requester_id == user.id
        assert response.document_id == document.id
        assert len(response.recipients) == 2
        
        # Verifica recipients
        for recipient in response.recipients:
            assert recipient.status == RecipientStatus.PENDING
            assert recipient.approval_token is not None
            assert len(recipient.approval_token) == 36  # UUID format
    
    def test_create_approval_request_document_not_found(self, approval_service, sample_user_and_document):
        """Test creazione con documento inesistente"""
        user, document = sample_user_and_document
        
        unique_id = str(uuid.uuid4())[:8]
        request_data = ApprovalRequestCreate(
            document_id=str(uuid.uuid4()),  # ID inesistente
            title="Test Request",
            recipients=[
                ApprovalRecipientCreate(
                    recipient_email=f"test_{unique_id}@test.com",
                    recipient_name="Test User"
                )
            ]
        )
        
        with pytest.raises(NotFoundError) as exc_info:
            approval_service.create_approval_request(
                request_data=request_data,
                requester_id=user.id
            )
        
        assert "non trovato o non autorizzato" in str(exc_info.value)
    
    def test_create_approval_request_duplicate_pending(self, approval_service, sample_user_and_document):
        """Test creazione con richiesta già pending per lo stesso documento"""
        user, document = sample_user_and_document
        
        unique_id = str(uuid.uuid4())[:8]
        
        # Crea prima richiesta
        request_data = ApprovalRequestCreate(
            document_id=document.id,
            title="First Request",
            recipients=[
                ApprovalRecipientCreate(recipient_email=f"test1_{unique_id}@test.com")
            ]
        )
        
        approval_service.create_approval_request(
            request_data=request_data,
            requester_id=user.id
        )
        
        # Tenta seconda richiesta per stesso documento
        request_data2 = ApprovalRequestCreate(
            document_id=document.id,
            title="Second Request",
            recipients=[
                ApprovalRecipientCreate(recipient_email=f"test2_{unique_id}@test.com")
            ]
        )
        
        with pytest.raises(ValidationError) as exc_info:
            approval_service.create_approval_request(
                request_data=request_data2,
                requester_id=user.id
            )
        
        assert "già una richiesta di approvazione in corso" in str(exc_info.value)
    
    def test_process_approval_decision_approved(self, approval_service, sample_user_and_document):
        """Test decisione di approvazione positiva"""
        user, document = sample_user_and_document
        
        unique_id = str(uuid.uuid4())[:8]
        
        # Crea richiesta con un solo destinatario (tipo ANY)
        request_data = ApprovalRequestCreate(
            document_id=document.id,
            title="Single Approver Request",
            approval_type=ApprovalType.ANY,
            recipients=[
                ApprovalRecipientCreate(
                    recipient_email=f"single_approver_{unique_id}@test.com",
                    recipient_name="Single Approver"
                )
            ]
        )
        
        response = approval_service.create_approval_request(
            request_data=request_data,
            requester_id=user.id
        )
        
        # Prendi il token del primo (unico) recipient
        approval_token = response.recipients[0].approval_token
        
        # Processa decisione positiva
        decision_data = ApprovalDecisionRequest(
            decision="approved",
            comments="Documento approvato senza problemi"
        )
        
        decision_response = approval_service.process_approval_decision(
            approval_token=approval_token,
            decision_data=decision_data,
            client_ip="192.168.1.2",
            user_agent="ApproverAgent/1.0"
        )
        
        # ✅ Fix: Verifica il messaggio corretto che viene effettivamente restituito
        assert decision_response["recipient_status"] == RecipientStatus.APPROVED
        assert decision_response["approval_request_status"] == ApprovalStatus.APPROVED
        assert decision_response["completed"] is True
        # ✅ Verifica il messaggio effettivo invece di "approvato senza problemi"
        assert "registrata con successo" in decision_response["message"]
    
    def test_process_approval_decision_rejected_all_type(self, approval_service, sample_user_and_document):
        """Test decisione di rifiuto con tipo ALL (deve rifiutare tutta la richiesta)"""
        user, document = sample_user_and_document
        
        unique_id = str(uuid.uuid4())[:8]
        
        # Crea richiesta con tipo ALL e 2 destinatari
        request_data = ApprovalRequestCreate(
            document_id=document.id,
            title="ALL Type Request",
            approval_type=ApprovalType.ALL,
            recipients=[
                ApprovalRecipientCreate(recipient_email=f"approver1_{unique_id}@test.com"),
                ApprovalRecipientCreate(recipient_email=f"approver2_{unique_id}@test.com")
            ]
        )
        
        response = approval_service.create_approval_request(
            request_data=request_data,
            requester_id=user.id
        )
        
        # Il primo approver rifiuta
        approval_token = response.recipients[0].approval_token
        
        decision_data = ApprovalDecisionRequest(
            decision="rejected",
            comments="Documento non soddisfa i requisiti"
        )
        
        decision_response = approval_service.process_approval_decision(
            approval_token=approval_token,
            decision_data=decision_data
        )
        
        # Verifiche - con tipo ALL, un singolo rifiuto rifiuta tutto
        assert decision_response["recipient_status"] == RecipientStatus.REJECTED
        assert decision_response["approval_request_status"] == ApprovalStatus.REJECTED
        assert decision_response["completed"] is True
        assert decision_response["completion_reason"] == "at_least_one_rejection"
    
    def test_process_approval_decision_invalid_token(self, approval_service):
        """Test decisione con token non valido"""
        decision_data = ApprovalDecisionRequest(
            decision="approved",
            comments="Test"
        )
        
        with pytest.raises(NotFoundError) as exc_info:
            approval_service.process_approval_decision(
                approval_token="invalid-token-12345",
                decision_data=decision_data
            )
        
        assert "Token di approvazione non valido" in str(exc_info.value)
    
    def test_process_approval_decision_expired_token(self, approval_service, sample_user_and_document, db_session):
        """Test decisione con token scaduto"""
        user, document = sample_user_and_document
        
        unique_id = str(uuid.uuid4())[:8]
        
        # ✅ Fix: Prima crea la richiesta con data futura, poi modifica manualmente la scadenza nel DB
        request_data = ApprovalRequestCreate(
            document_id=document.id,
            title="Expired Request",
            expires_at=datetime.now() + timedelta(days=7),  # ✅ Inizia con data futura valida
            recipients=[
                ApprovalRecipientCreate(recipient_email=f"expired_{unique_id}@test.com")
            ]
        )
        
        response = approval_service.create_approval_request(
            request_data=request_data,
            requester_id=user.id
        )
        
        # ✅ Usa la stessa sessione del test invece di crearne una nuova
        recipient = db_session.query(ApprovalRecipient).filter(
            ApprovalRecipient.approval_token == response.recipients[0].approval_token
        ).first()
        
        # ✅ Verifica che il recipient sia stato trovato
        assert recipient is not None, f"Recipient non trovato con token {response.recipients[0].approval_token}"
        
        # ✅ Ora modifica la scadenza nel passato
        recipient.expires_at = datetime.now() - timedelta(hours=1)
        db_session.commit()
        
        # ✅ Test della decisione con token scaduto
        approval_token = response.recipients[0].approval_token
        
        decision_data = ApprovalDecisionRequest(
            decision="approved",
            comments="Too late"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            approval_service.process_approval_decision(
                approval_token=approval_token,
                decision_data=decision_data
            )
        
        assert "è scaduto" in str(exc_info.value)

    
    def test_get_approval_request_success(self, approval_service, sample_user_and_document):
        """Test recupero richiesta approvazione"""
        user, document = sample_user_and_document
        
        unique_id = str(uuid.uuid4())[:8]
        
        # Crea richiesta
        request_data = ApprovalRequestCreate(
            document_id=document.id,
            title="Test Get Request",
            recipients=[
                ApprovalRecipientCreate(recipient_email=f"getter_{unique_id}@test.com")
            ]
        )
        
        created_response = approval_service.create_approval_request(
            request_data=request_data,
            requester_id=user.id
        )
        
        # Recupera richiesta
        retrieved_response = approval_service.get_approval_request(
            request_id=created_response.id,
            user_id=user.id
        )
        
        # Verifiche
        assert retrieved_response.id == created_response.id
        assert retrieved_response.title == "Test Get Request"
        assert len(retrieved_response.recipients) == 1
    
    def test_get_approval_request_not_found(self, approval_service):
        """Test recupero richiesta inesistente"""
        with pytest.raises(NotFoundError) as exc_info:
            approval_service.get_approval_request(
                request_id=str(uuid.uuid4()),
                user_id=1
            )
        
        assert "non trovata" in str(exc_info.value)
    
    def test_list_approval_requests(self, approval_service, sample_user_and_document):
        """Test lista richieste approvazione utente"""
        user, document = sample_user_and_document
        
        unique_id = str(uuid.uuid4())[:8]
        
        # ✅ Fix: Crea documenti separati per ogni richiesta per evitare conflitti
        documents = []
        for i in range(3):
            doc = Document(
                id=str(uuid.uuid4()),
                owner_id=user.id,
                filename=f"list_doc_{unique_id}_{i}.pdf",
                original_filename=f"list_doc_{unique_id}_{i}.pdf",
                storage_path=f"/fake/list/{unique_id}_{i}",
                content_type="application/pdf",
                size=1024.0,
                file_hash=f"listhash_{unique_id}_{i}"
            )
            approval_service.db.add(doc)
            documents.append(doc)
        
        approval_service.db.commit()
        
        # Crea diverse richieste su documenti diversi
        titles = ["Request 1", "Request 2", "Request 3"]
        for i, title in enumerate(titles):
            request_data = ApprovalRequestCreate(
                document_id=documents[i].id,  # ✅ Documento diverso per ogni richiesta
                title=title,
                recipients=[
                    ApprovalRecipientCreate(
                        recipient_email=f"list_test_{title.lower().replace(' ', '_')}_{unique_id}@test.com"
                    )
                ]
            )
            approval_service.create_approval_request(
                request_data=request_data,
                requester_id=user.id
            )
        
        # Lista richieste
        requests_list = approval_service.list_approval_requests(user_id=user.id)
        
        # Verifiche
        assert len(requests_list) >= 3
        retrieved_titles = [req.title for req in requests_list]
        for title in titles:
            assert title in retrieved_titles
        
        # Verifica contatori
        for req in requests_list:
            assert req.recipient_count > 0
            assert req.approved_count >= 0
            assert req.pending_count >= 0
    
    def test_cancel_approval_request_success(self, approval_service, sample_user_and_document):
        """Test cancellazione richiesta approvazione"""
        user, document = sample_user_and_document
        
        unique_id = str(uuid.uuid4())[:8]
        
        # Crea richiesta
        request_data = ApprovalRequestCreate(
            document_id=document.id,
            title="Request to Cancel",
            recipients=[
                ApprovalRecipientCreate(recipient_email=f"cancel_test_{unique_id}@test.com")
            ]
        )
        
        response = approval_service.create_approval_request(
            request_data=request_data,
            requester_id=user.id
        )
        
        # Cancella richiesta
        cancel_response = approval_service.cancel_approval_request(
            request_id=response.id,
            user_id=user.id,
            reason="Test cancellation",
            client_ip="192.168.1.3"
        )
        
        # Verifiche
        assert cancel_response["status"] == "cancelled"
        assert "cancellata con successo" in cancel_response["message"]
        
        # Verifica che la richiesta sia stata aggiornata
        updated_request = approval_service.get_approval_request(
            request_id=response.id,
            user_id=user.id
        )
        assert updated_request.status == ApprovalStatus.CANCELLED
    
    def test_get_pending_approvals_for_email_isolated(self, approval_service, sample_user_and_document):
        """Test recupero approvazioni pending per email specifico - isolato"""
        user, document = sample_user_and_document
        
        # Usa email univoco per evitare interferenze con test precedenti
        unique_id = str(uuid.uuid4())[:8]
        target_email = f"pending_isolated_{unique_id}@test.com"
        
        # ✅ Fix: Crea documenti separati per evitare conflitti
        documents = []
        for i in range(2):
            doc = Document(
                id=str(uuid.uuid4()),
                owner_id=user.id,
                filename=f"pending_doc_{unique_id}_{i}.pdf",
                original_filename=f"pending_doc_{unique_id}_{i}.pdf",
                storage_path=f"/fake/pending/{unique_id}_{i}",
                content_type="application/pdf",
                size=1024.0,
                file_hash=f"pendinghash_{unique_id}_{i}"
            )
            approval_service.db.add(doc)
            documents.append(doc)
        
        approval_service.db.commit()
        
        # Crea richieste per questo email su documenti diversi
        for i in range(2):
            request_data = ApprovalRequestCreate(
                document_id=documents[i].id,
                title=f"Pending Request {i+1}",
                recipients=[
                    ApprovalRecipientCreate(
                        recipient_email=target_email,
                        recipient_name=f"Pending User {i+1}"
                    )
                ]
            )
            approval_service.create_approval_request(
                request_data=request_data,
                requester_id=user.id
            )
        
        # Recupera pending per email
        pending_list = approval_service.get_pending_approvals_for_email(target_email)
        
        # Verifiche
        assert len(pending_list) == 2
        for pending in pending_list:
            assert pending["requester_name"] in [user.display_name, user.email]
            assert pending["approval_token"] is not None
            assert "Pending Request" in pending["title"]
    
    def test_approval_statistics(self, approval_service, sample_user_and_document):
        """Test statistiche approvazioni"""
        user, document = sample_user_and_document
        
        unique_id = str(uuid.uuid4())[:8]
        
        # ✅ Fix: Crea documenti separati per evitare conflitti
        documents = []
        for i in range(2):
            doc = Document(
                id=str(uuid.uuid4()),
                owner_id=user.id,
                filename=f"stats_doc_{unique_id}_{i}.pdf",
                original_filename=f"stats_doc_{unique_id}_{i}.pdf",
                storage_path=f"/fake/stats/{unique_id}_{i}",
                content_type="application/pdf",
                size=1024.0,
                file_hash=f"statshash_{unique_id}_{i}"
            )
            approval_service.db.add(doc)
            documents.append(doc)
        
        approval_service.db.commit()
        
        # Crea qualche richiesta su documenti diversi
        for i in range(2):
            request_data = ApprovalRequestCreate(
                document_id=documents[i].id,
                title=f"Stats Request {i+1}",
                recipients=[
                    ApprovalRecipientCreate(recipient_email=f"stats{i+1}_{unique_id}@test.com")
                ]
            )
            approval_service.create_approval_request(
                request_data=request_data,
                requester_id=user.id
            )
        
        # Ottieni statistiche
        stats = approval_service.get_approval_statistics(user.id)
        
        # Verifiche
        assert "requested_pending" in stats
        assert "requested_approved" in stats
        assert "requested_rejected" in stats
        assert "requested_cancelled" in stats
        assert stats["requested_pending"] >= 2

# Test standalone con cleanup completo (unchanged)
def run_approval_service_tests():
    """Test standalone per ApprovalService con isolamento completo"""
    print("🔧 Testing Approval Service...")
    print("=" * 50)
    
    from app.db.base import SessionLocal
    
    db = SessionLocal()
    
    try:
        unique_id = str(uuid.uuid4())[:8]
        
        print(f"\n🧹 Cleanup preliminare per test isolation...")
        
        # ✅ CLEANUP PRELIMINARE - Rimuove tutti i dati di test precedenti
        # Questo garantisce test isolation completo
        
        # 1. Rimuovi tutti i recipients con email di test
        test_emails = [
            'service_approver1@test.com',
            'service_approver2@test.com'
        ]
        
        for email in test_emails:
            old_recipients = db.query(ApprovalRecipient).filter(
                ApprovalRecipient.recipient_email == email
            ).all()
            
            print(f"  Rimuovendo {len(old_recipients)} old recipients per {email}")
            
            for recipient in old_recipients:
                # Rimuovi audit logs collegati
                old_audits = db.query(AuditLog).filter(
                    AuditLog.approval_request_id == recipient.approval_request_id
                ).all()
                for audit in old_audits:
                    db.delete(audit)
                
                # Rimuovi approval request collegata
                old_request = db.query(ApprovalRequest).filter(
                    ApprovalRequest.id == recipient.approval_request_id
                ).first()
                if old_request:
                    db.delete(old_request)
                
                # Rimuovi recipient
                db.delete(recipient)
        
        # 2. Rimuovi utenti di test precedenti
        old_users = db.query(User).filter(
            User.email.like('%standalone_service_%')
        ).all()
        
        print(f"  Rimuovendo {len(old_users)} old users")
        
        for user in old_users:
            # Rimuovi documenti dell'utente
            old_docs = db.query(Document).filter(Document.owner_id == user.id).all()
            for doc in old_docs:
                db.delete(doc)
            
            db.delete(user)
        
        # Commit cleanup
        db.commit()
        print("✅ Cleanup preliminare completato")
        
        print("\n1️⃣ Test setup service...")
        
        # Crea servizio
        approval_service = ApprovalService(db)
        print("✅ ApprovalService creato")
        
        # Crea utente e documento con ID univoco
        user = User(
            email=f"standalone_service_{unique_id}@test.com",
            password_hash=hash_password("testpass"),
            display_name=f"Standalone Service User {unique_id}"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        document = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            filename=f"service_test_{unique_id}.pdf",
            original_filename=f"service_test_{unique_id}.pdf",
            storage_path=f"/fake/service/{unique_id}",
            content_type="application/pdf",
            size=1024.0,
            file_hash=f"servicehash_{unique_id}"
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        print("✅ Utente e documento creati per test service")
        
        print("\n2️⃣ Test creazione richiesta...")
        
        # Test creazione richiesta con email UNIVOCHE per questo test
        request_data = ApprovalRequestCreate(
            document_id=document.id,
            title="Standalone Service Test Request",
            description="Test richiesta tramite service standalone",
            approval_type=ApprovalType.ALL,
            expires_at=datetime.now() + timedelta(days=5),
            recipients=[
                ApprovalRecipientCreate(
                    recipient_email=f"service_approver1_{unique_id}@test.com",  # ← EMAIL UNIVOCA
                    recipient_name="Service Approver 1"
                ),
                ApprovalRecipientCreate(
                    recipient_email=f"service_approver2_{unique_id}@test.com",  # ← EMAIL UNIVOCA
                    recipient_name="Service Approver 2"
                )
            ],
            requester_comments="Commenti standalone service test"
        )
        
        response = approval_service.create_approval_request(
            request_data=request_data,
            requester_id=user.id,
            client_ip="127.0.0.1",
            user_agent="StandaloneServiceTest/1.0"
        )
        
        assert response.id is not None
        assert len(response.recipients) == 2
        print(f"✅ Richiesta creata: {response.id[:8]}...")
        
        print("\n3️⃣ Test decisione approvazione...")
        
        # Test decisione primo approver
        first_token = response.recipients[0].approval_token
        decision_data = ApprovalDecisionRequest(
            decision="approved",
            comments="Prima approvazione via service test"
        )
        
        decision_response = approval_service.process_approval_decision(
            approval_token=first_token,
            decision_data=decision_data,
            client_ip="127.0.0.1",
            user_agent="StandaloneApprover/1.0"
        )
        
        assert decision_response["recipient_status"] == RecipientStatus.APPROVED
        assert decision_response["completed"] is False
        print("✅ Prima decisione processata")
        
        # Test decisione secondo approver
        second_token = response.recipients[1].approval_token
        decision_data2 = ApprovalDecisionRequest(
            decision="approved",
            comments="Seconda approvazione via service test"
        )
        
        decision_response2 = approval_service.process_approval_decision(
            approval_token=second_token,
            decision_data=decision_data2
        )
        
        assert decision_response2["approval_request_status"] == ApprovalStatus.APPROVED
        assert decision_response2["completed"] is True
        print("✅ Seconda decisione processata - richiesta completata")
        
        print("\n4️⃣ Test lista e statistiche...")
        
        # Test lista richieste
        requests_list = approval_service.list_approval_requests(user.id)
        assert len(requests_list) >= 1
        assert any(req.title == "Standalone Service Test Request" for req in requests_list)
        print(f"✅ Lista richieste: {len(requests_list)} trovate")
        
        # Test statistiche
        stats = approval_service.get_approval_statistics(user.id)
        assert "requested_pending" in stats
        assert "requested_approved" in stats
        print(f"✅ Statistiche: {stats}")
        
        print("\n5️⃣ Test recupero pending per email...")
        
        # ✅ Test con EMAIL UNIVOCA per questo test
        target_email = f"service_approver1_{unique_id}@test.com"
        print(f"🔍 Controllo pending per email: {target_email}")
        
        # Forza refresh della sessione per evitare dati stale
        db.expire_all()
        
        pending = approval_service.get_pending_approvals_for_email(target_email)
        
        print(f"📊 Pending trovati: {len(pending)}")
        for p in pending:
            print(f"  - Richiesta: {p['title']}, Token: {p['approval_token'][:8]}...")
        
        # ✅ Ora deve essere 0 perché l'email è univoca e ha già approvato
        assert len(pending) == 0, f"Trovati {len(pending)} pending per {target_email} invece di 0"
        
        print("✅ Pending approvals recuperati correttamente")
        
        print("\n6️⃣ Cleanup finale...")
        
        # ✅ Cleanup completo e ordinato
        # Prima elimina audit logs
        audit_logs = db.query(AuditLog).filter(AuditLog.approval_request_id == response.id).all()
        for log in audit_logs:
            db.delete(log)
        
        # Poi elimina recipients
        recipients = db.query(ApprovalRecipient).filter(ApprovalRecipient.approval_request_id == response.id).all()
        for recipient in recipients:
            db.delete(recipient)
        
        # Poi elimina approval request
        approval_req = db.query(ApprovalRequest).filter(ApprovalRequest.id == response.id).first()
        if approval_req:
            db.delete(approval_req)
        
        # Infine elimina documento e utente
        db.delete(document)
        db.delete(user)
        
        # Commit finale
        db.commit()
        print("✅ Cleanup finale completato")
        
        print("\n🎉 Tutti i test approval service completati!")
        return True
        
    except Exception as e:
        print(f"❌ Errore test service: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = run_approval_service_tests()
    exit(0 if success else 1)
