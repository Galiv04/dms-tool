import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup

import pytest
import uuid
from fastapi.testclient import TestClient
from io import BytesIO
from app.main import app
from app.services.auth import create_user
from app.db.schemas import UserCreate
from app.db.models import User

client = TestClient(app)

@pytest.fixture
def authenticated_user(db_session_real):
    """
    Crea utente autenticato per i test usando sessione REALE
    Cleanup manuale alla fine per evitare conflitti
    """
    # Email univoca per ogni test
    unique_id = str(uuid.uuid4())[:8]
    email = f"test_docs_{unique_id}@example.com"
    
    # Crea utente usando la sessione REALE (non rollback)
    user_data = UserCreate(
        email=email,
        password="testpass123",
        display_name=f"Test User {unique_id}"
    )
    
    user = create_user(db_session_real, user_data)
    
    # Login per ottenere token
    login_response = client.post(
        "/auth/login",
        data={"username": email, "password": "testpass123"}
    )
    
    if login_response.status_code != 200:
        pytest.fail(f"Login fallito: {login_response.json()}")
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    yield headers, user, email
    
    # Cleanup manuale - elimina l'utente dal database reale
    try:
        user_to_delete = db_session_real.query(User).filter(User.email == email).first()
        if user_to_delete:
            db_session_real.delete(user_to_delete)
            db_session_real.commit()
    except Exception as e:
        print(f"⚠️ Warning cleanup utente {email}: {e}")
        db_session_real.rollback()

@pytest.mark.integration
class TestDocumentsAPI:
    """Test per API documenti con autenticazione"""
    
    def test_upload_document_success(self, authenticated_user):
        """Test upload documento valido"""
        headers, user, email = authenticated_user
        
        # Crea file di test
        file_content = b"Test PDF content for upload"
        files = {
            "file": ("test_upload.pdf", BytesIO(file_content), "application/pdf")
        }
        
        response = client.post("/documents/upload", files=files, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "document" in data
        assert "message" in data
        assert data["document"]["filename"] == "test_upload.pdf"
        assert data["document"]["content_type"] == "application/pdf"
        assert data["document"]["size"] == len(file_content)
        assert data["document"]["owner_id"] == user.id
    
    def test_upload_document_no_auth(self):
        """Test upload senza autenticazione"""
        file_content = b"Test content - no auth"
        files = {
            "file": ("test_no_auth.pdf", BytesIO(file_content), "application/pdf")
        }
        
        response = client.post("/documents/upload", files=files)
        # Accetta sia 401 che 403 per compatibilità
        assert response.status_code in [401, 403]
    
    def test_upload_invalid_file_type(self, authenticated_user):
        """Test upload file non consentito"""
        headers, user, email = authenticated_user
        
        file_content = b"Test executable content"
        files = {
            "file": ("malware.exe", BytesIO(file_content), "application/octet-stream")
        }
        
        response = client.post("/documents/upload", files=files, headers=headers)
        assert response.status_code == 400
        assert "non valido" in response.json()["detail"].lower()
    
    def test_list_documents(self, authenticated_user):
        """Test lista documenti utente"""
        headers, user, email = authenticated_user
        
        # Upload documento per il test
        file_content = b"Test PDF for listing"
        files = {
            "file": ("list_test.pdf", BytesIO(file_content), "application/pdf")
        }
        upload_response = client.post("/documents/upload", files=files, headers=headers)
        assert upload_response.status_code == 200
        
        # Lista documenti
        response = client.get("/documents/", headers=headers)
        
        assert response.status_code == 200
        documents = response.json()
        assert len(documents) >= 1
        
        # Trova il documento caricato
        uploaded_doc = next(
            (doc for doc in documents if doc["filename"] == "list_test.pdf"), 
            None
        )
        assert uploaded_doc is not None
        assert uploaded_doc["owner_id"] == user.id
    
    def test_get_document_details(self, authenticated_user):
        """Test dettagli documento specifico"""
        headers, user, email = authenticated_user
        
        # Upload documento
        file_content = b"Test PDF for details"
        files = {
            "file": ("details_test.pdf", BytesIO(file_content), "application/pdf")
        }
        upload_response = client.post("/documents/upload", files=files, headers=headers)
        document_id = upload_response.json()["document"]["id"]
        
        # Ottieni dettagli
        response = client.get(f"/documents/{document_id}", headers=headers)
        
        assert response.status_code == 200
        document = response.json()
        assert document["id"] == document_id
        assert document["filename"] == "details_test.pdf"
        assert document["owner_id"] == user.id
    
    def test_download_document(self, authenticated_user):
        """Test download documento"""
        headers, user, email = authenticated_user
        
        # Upload documento
        file_content = b"Test PDF for download"
        files = {
            "file": ("download_test.pdf", BytesIO(file_content), "application/pdf")
        }
        upload_response = client.post("/documents/upload", files=files, headers=headers)
        document_id = upload_response.json()["document"]["id"]
        
        # Download
        response = client.get(f"/documents/{document_id}/download", headers=headers)
        
        assert response.status_code == 200
        assert response.content == file_content
        assert response.headers["content-type"] == "application/pdf"
    
    def test_preview_document(self, authenticated_user):
        """Test preview documento PDF"""
        headers, user, email = authenticated_user
        
        # Upload documento PDF
        file_content = b"Test PDF for preview"
        files = {
            "file": ("preview_test.pdf", BytesIO(file_content), "application/pdf")
        }
        upload_response = client.post("/documents/upload", files=files, headers=headers)
        document_id = upload_response.json()["document"]["id"]
        
        # Preview
        response = client.get(f"/documents/{document_id}/preview", headers=headers)
        
        assert response.status_code == 200
        assert "content-disposition" in response.headers
        assert "inline" in response.headers["content-disposition"]
    
    def test_delete_document(self, authenticated_user):
        """Test eliminazione documento"""
        headers, user, email = authenticated_user
        
        # Upload documento
        file_content = b"Test PDF to be deleted"
        files = {
            "file": ("delete_test.pdf", BytesIO(file_content), "application/pdf")
        }
        upload_response = client.post("/documents/upload", files=files, headers=headers)
        document_id = upload_response.json()["document"]["id"]
        
        # Elimina documento
        delete_response = client.delete(f"/documents/{document_id}", headers=headers)
        
        assert delete_response.status_code == 200
        assert "eliminato con successo" in delete_response.json()["message"]
        
        # Verifica che non esista più
        get_response = client.get(f"/documents/{document_id}", headers=headers)
        assert get_response.status_code == 404

# Test standalone semplificato
def run_documents_api_tests():
    """Test standalone per API documenti"""
    print("📄 Testing Documents API (Fixed)...")
    print("=" * 50)
    
    # Verifica backend
    try:
        health_response = client.get("/health")
        if health_response.status_code != 200:
            print("❌ Backend non raggiungibile. Avvia: uvicorn app.main:app --reload")
            return False
    except Exception:
        print("❌ Backend non raggiungibile")
        return False
    
    print("✅ Backend raggiungibile")
    
    # Test usando le API dirette
    unique_id = str(uuid.uuid4())[:8]
    test_email = f"standalone_fixed_{unique_id}@example.com"
    
    try:
        # Registrazione
        register_data = {
            "email": test_email,
            "password": "testpass123",
            "display_name": f"Standalone User {unique_id}"
        }
        
        register_response = client.post("/auth/register", json=register_data)
        if register_response.status_code != 200:
            print(f"❌ Registrazione fallita: {register_response.json()}")
            return False
        
        # Login
        login_data = {"username": test_email, "password": "testpass123"}
        login_response = client.post("/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("✅ Utente creato e autenticato")
        
        # Test upload
        print("\n📤 Test upload...")
        file_content = b"Standalone test PDF content"
        files = {"file": ("standalone.pdf", BytesIO(file_content), "application/pdf")}
        
        upload_response = client.post("/documents/upload", files=files, headers=headers)
        assert upload_response.status_code == 200
        document_id = upload_response.json()["document"]["id"]
        print(f"✅ Upload: {document_id[:8]}...")
        
        # Test lista
        print("\n📋 Test lista...")
        list_response = client.get("/documents/", headers=headers)
        assert list_response.status_code == 200
        print(f"✅ Lista: {len(list_response.json())} documenti")
        
        # Test download
        print("\n📥 Test download...")
        download_response = client.get(f"/documents/{document_id}/download", headers=headers)
        assert download_response.status_code == 200
        assert download_response.content == file_content
        print("✅ Download corretto")
        
        print("\n🎉 Test completati con successo!")
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

if __name__ == "__main__":
    run_documents_api_tests()
