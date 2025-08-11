import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup

import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.models import User, Document, UserRole, ApprovalType, ApprovalStatus
from app.utils.security import hash_password, create_access_token, verify_token, debug_token
from app.configurations import settings
from app.db.base import get_db

client = TestClient(app)

# ✅ Override della dependency get_db per i test
def get_test_db():
    """Override della dependency get_db per usare sessione di test"""
    from app.db.base import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.mark.db
class TestApprovalAPI:
    """Test per API endpoints approvazioni con gestione sessioni corretta"""
    
    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self, db_session):
        """Setup e cleanup automatico per ogni test"""
        print(f"\n🧹 Setup test - Session ID: {id(db_session)}")
        
        # ✅ Override della dependency per questo test
        app.dependency_overrides[get_db] = lambda: db_session
        
        yield  # Esegui il test
        
        # ✅ Cleanup esplicito
        try:
            # Rollback di tutte le transazioni pending
            db_session.rollback()
            
            # Cleanup delle entities create nel test
            unique_ids = getattr(self, '_test_unique_ids', [])
            for unique_id in unique_ids:
                # Rimuovi utenti di test
                users = db_session.query(User).filter(
                    User.email.like(f'%{unique_id}%')
                ).all()
                for user in users:
                    # Rimuovi documenti dell'utente
                    docs = db_session.query(Document).filter(Document.owner_id == user.id).all()
                    for doc in docs:
                        db_session.delete(doc)
                    db_session.delete(user)
            
            db_session.commit()
            print(f"🧹 Cleanup completato per {len(unique_ids)} unique_ids")
            
        except Exception as e:
            print(f"⚠️ Warning durante cleanup: {e}")
            db_session.rollback()
        finally:
            # ✅ Rimuovi override
            if get_db in app.dependency_overrides:
                del app.dependency_overrides[get_db]
            print(f"🧹 Test cleanup finished")
    
    @pytest.fixture
    def test_user_and_document(self, db_session):
        """Fixture per utente e documento di test con sessione condivisa"""
        unique_id = str(uuid.uuid4())[:8]
        
        # ✅ Registra unique_id per cleanup
        if not hasattr(self, '_test_unique_ids'):
            self._test_unique_ids = []
        self._test_unique_ids.append(unique_id)
        
        print(f"\n🔍 DEBUG: Creating test user and document with unique_id: {unique_id}")
        print(f"🔍 DEBUG: Using session ID: {id(db_session)}")
        
        try:
            # Crea utente con sessione condivisa
            user = User(
                email=f"api_test_{unique_id}@test.com",
                password_hash=hash_password("testpass"),
                display_name=f"API Test User {unique_id}",
                role=UserRole.USER
            )
            db_session.add(user)
            db_session.flush()  # ✅ Flush per ottenere l'ID senza commit
            
            print(f"🔍 DEBUG: Created user - ID: {user.id}, Email: {user.email}")
            
            # Crea documento
            document = Document(
                id=str(uuid.uuid4()),
                owner_id=user.id,
                filename=f"api_test_{unique_id}.pdf",
                original_filename=f"api_test_{unique_id}.pdf",
                storage_path=f"/fake/api/{unique_id}",
                content_type="application/pdf",
                size=1024.0,
                file_hash=f"apihash_{unique_id}"
            )
            db_session.add(document)
            db_session.flush()  # ✅ Flush per ottenere l'ID
            
            print(f"🔍 DEBUG: Created document - ID: {document.id}, Owner: {document.owner_id}")
            
            # ✅ Commit esplicito per rendere visibili i dati
            db_session.commit()
            
            # ✅ Refresh per assicurarsi che i dati siano aggiornati
            db_session.refresh(user)
            db_session.refresh(document)
            
            # ✅ Verifica che l'utente sia nel database
            verification_user = db_session.query(User).filter(User.email == user.email).first()
            assert verification_user is not None, f"User verification failed for {user.email}"
            print(f"🔍 DEBUG: User verification successful - Found user ID: {verification_user.id}")
            
            # Crea token
            token_data = {"sub": user.email}
            token = create_access_token(data=token_data)
            print(f"🔍 DEBUG: Token created - Length: {len(token)}")
            
            # ✅ Verifica token immediatamente
            payload = verify_token(token)
            print(f"🔍 DEBUG: Token verified - Sub: {payload.get('sub')}")
            
            # ✅ Verifica che l'utente sia trovabile con l'email del token
            token_user = db_session.query(User).filter(User.email == payload.get('sub')).first()
            assert token_user is not None, f"Token user lookup failed for {payload.get('sub')}"
            print(f"🔍 DEBUG: Token user lookup successful - User ID: {token_user.id}")
            
            return user, document, token
            
        except Exception as e:
            print(f"❌ DEBUG: Error in fixture: {e}")
            db_session.rollback()
            raise
    
    def test_debug_session_consistency(self, db_session):
        """Test debug per verificare consistenza sessioni"""
        print("\n🔧 DEBUG: Testing session consistency...")
        
        unique_id = str(uuid.uuid4())[:8]
        if not hasattr(self, '_test_unique_ids'):
            self._test_unique_ids = []
        self._test_unique_ids.append(unique_id)
        
        # Crea utente nella sessione di test
        user = User(
            email=f"session_test_{unique_id}@test.com",
            password_hash=hash_password("testpass"),
            display_name="Session Test User",
            role=UserRole.USER
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        print(f"🔍 Created user in test session: {user.email} (ID: {user.id})")
        
        # Crea token
        token = create_access_token(data={"sub": user.email})
        
        # ✅ Test endpoint che usa get_current_user
        response = client.get(
            "/approvals/dashboard/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"🔍 Stats endpoint response: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
        
        assert response.status_code == 200
        print("✅ Session consistency test passed")
    
    def test_create_approval_request_api_fixed(self, test_user_and_document):
        """Test API creazione richiesta approvazione con sessioni corrette"""
        print("\n🔧 DEBUG: Testing create approval request API (FIXED)...")
        
        user, document, token = test_user_and_document
        unique_id = str(uuid.uuid4())[:8]
        
        print(f"🔍 Using user: {user.email} (ID: {user.id})")
        print(f"🔍 Using document: {document.id}")
        print(f"🔍 Token length: {len(token)}")
        
        request_data = {
            "document_id": document.id,
            "title": "API Test Approval Request",
            "description": "Richiesta di test per il service",
            "approval_type": "all",
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
            "recipients": [
                {
                    "recipient_email": f"api_approver1_{unique_id}@test.com",
                    "recipient_name": "API Approver 1"
                },
                {
                    "recipient_email": f"api_approver2_{unique_id}@test.com",
                    "recipient_name": "API Approver 2"
                }
            ],
            "requester_comments": "Commenti del richiedente"
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post(
            "/approvals/",
            json=request_data,
            headers=headers
        )
        
        print(f"🔍 Response status: {response.status_code}")
        
        if response.status_code != 201:
            print(f"❌ Response error: {response.text}")
            
            # ✅ Debug token manualmente se fallisce
            try:
                payload = verify_token(token)
                print(f"🔍 Manual token verification: {payload}")
            except Exception as e:
                print(f"❌ Manual token verification failed: {e}")
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        print(f"✅ Success! Created approval request: {data.get('id', 'NO_ID')}")
        
        # Verifiche
        assert data["title"] == "API Test Approval Request"
        assert data["approval_type"] == "all"
        assert data["status"] == "pending"
        assert len(data["recipients"]) == 2
        
        print("✅ All assertions passed")
    
    def test_list_approval_requests_api_fixed(self, test_user_and_document, db_session):
        """Test API lista richieste approvazione con cleanup corretto"""
        print("\n🔧 DEBUG: Testing list approval requests API (FIXED)...")
        
        user, document, token = test_user_and_document
        unique_id = str(uuid.uuid4())[:8]
        
        # ✅ Crea documento separato per evitare conflitti
        document2 = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            filename=f"list_test_{unique_id}.pdf",
            original_filename=f"list_test_{unique_id}.pdf",
            storage_path=f"/fake/list/{unique_id}",
            content_type="application/pdf",
            size=1024.0,
            file_hash=f"listhash_{unique_id}"
        )
        db_session.add(document2)
        db_session.commit()
        db_session.refresh(document2)
        
        # Prima crea una richiesta
        request_data = {
            "document_id": document2.id,
            "title": "List Test Request",
            "recipients": [
                {
                    "recipient_email": f"list_test_{unique_id}@test.com",
                    "recipient_name": "List Test User"
                }
            ]
        }
        
        create_response = client.post(
            "/approvals/",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"🔍 Create request status: {create_response.status_code}")
        assert create_response.status_code == 201
        
        # Poi lista le richieste
        list_response = client.get(
            "/approvals/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"🔍 List request status: {list_response.status_code}")
        assert list_response.status_code == 200
        
        data = list_response.json()
        print(f"🔍 Found {len(data)} approval requests")
        
        assert len(data) >= 1
        assert any(req["title"] == "List Test Request" for req in data)
        
        print("✅ List test passed")

# ✅ Test standalone semplificato
def run_approval_api_debug_tests():
    """Test standalone semplificato con focus su problemi specifici"""
    print("🔧 Testing Approval API Endpoints (Focused Debug)...")
    print("=" * 70)
    
    try:
        print("\n1️⃣ Test endpoint base...")
        
        # Test endpoint pubblico
        health_response = client.get("/health")
        print(f"🔍 Health endpoint: {health_response.status_code}")
        assert health_response.status_code == 200
        
        # Test endpoint protetto senza auth
        no_auth_response = client.get("/approvals/")
        print(f"🔍 Protected without auth: {no_auth_response.status_code}")
        assert no_auth_response.status_code == 401
        
        print("\n2️⃣ Test token creation...")
        
        # Test token manuale
        test_email = "debug@test.com"
        token = create_access_token(data={"sub": test_email})
        payload = verify_token(token)
        
        print(f"🔍 Token created and verified for: {payload.get('sub')}")
        assert payload.get("sub") == test_email
        
        print("\n✅ Basic tests passed - ready for pytest with fixes")
        return True
        
    except Exception as e:
        print(f"❌ Debug test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_approval_api_debug_tests()
    exit(0 if success else 1)
