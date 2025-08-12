import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

import universal_setup

import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.api
class TestApprovalModalAPI:
    """Test per API endpoints necessari al Modal Creazione Approvazioni"""

    def test_get_available_users(self, auth_user_and_headers_with_override, user_factory):
        """Test endpoint per ottenere utenti disponibili"""
        user, headers = auth_user_and_headers_with_override
        
        # Crea utenti aggiuntivi usando factory
        approver1 = user_factory("approver", "Test Approver 1")
        approver2 = user_factory("manager", "Test Manager")

        # Test dell'endpoint
        response = client.get("/approvals/users", headers=headers)

        print(f"🔍 GET /approvals/users - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Error Response: {response.json()}")
        else:
            print(f"📄 Response: {response.json()}")

        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 2
        
        user_emails = [u["email"] for u in users]
        assert approver1.email in user_emails
        assert approver2.email in user_emails
        assert user.email not in user_emails
        print("✅ Test get_available_users passed")

    def test_get_user_documents_for_approval(self, auth_user_and_headers_with_override, db_session):
        """Test endpoint per ottenere documenti utente"""
        user, headers = auth_user_and_headers_with_override
        
        # Crea documento usando la stessa sessione
        unique_id = str(uuid.uuid4())[:8]
        from app.db.models import Document
        doc = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            filename=f"test_doc_{unique_id}.pdf",
            original_filename=f"Test Document {unique_id}.pdf",
            storage_path=f"/uploads/test_doc_{unique_id}.pdf",
            content_type="application/pdf",
            size=2048.5,
            file_hash=f"testhash_{unique_id}"
        )
        db_session.add(doc)
        db_session.commit()

        response = client.get("/approvals/documents", headers=headers)

        print(f"🔍 GET /approvals/documents - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Error Response: {response.json()}")
        else:
            print(f"📄 Response: {response.json()}")

        assert response.status_code == 200
        documents = response.json()
        assert len(documents) >= 1
        
        test_doc = next((d for d in documents if d["id"] == doc.id), None)
        assert test_doc is not None
        assert test_doc["filename"] == doc.original_filename
        print("✅ Test get_user_documents_for_approval passed")

    def test_validate_approval_data(self, auth_user_and_headers_with_override, db_session):
        """Test validazione dati approvazione"""
        user, headers = auth_user_and_headers_with_override
        
        # Crea documento
        unique_id = str(uuid.uuid4())[:8]
        from app.db.models import Document
        doc = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            filename=f"validation_doc_{unique_id}.pdf",
            original_filename=f"Validation Document {unique_id}.pdf",
            storage_path=f"/uploads/validation_doc_{unique_id}.pdf",
            content_type="application/pdf",
            size=1024.0,
            file_hash=f"validationhash_{unique_id}"
        )
        db_session.add(doc)
        db_session.commit()

        validation_data = {
            "title": "Contract Review Request",
            "description": "Please review this important contract",
            "document_id": doc.id,
            "approval_type": "all",
            "recipients": [
                {
                    "recipient_email": "approver1@test.com",
                    "recipient_name": "Approver One"
                },
                {
                    "recipient_email": "approver2@test.com", 
                    "recipient_name": "Approver Two"
                }
            ]
        }

        response = client.post("/approvals/validate", json=validation_data, headers=headers)

        print(f"🔍 POST /approvals/validate - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Error Response: {response.json()}")
        else:
            print(f"📄 Response: {response.json()}")

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is True
        assert result["document_name"] == doc.original_filename
        assert result["recipient_count"] == 2
        print("✅ Test validate_approval_data passed")

    def test_validate_approval_data_invalid_document(self, auth_user_and_headers_with_override):
        """Test validazione con documento inesistente"""
        user, headers = auth_user_and_headers_with_override
        
        validation_data = {
            "title": "Invalid Document Test",
            "description": "This should fail",
            "document_id": "00000000-0000-0000-0000-000000000000",  # UUID inesistente
            "approval_type": "all",
            "recipients": [
                {
                    "recipient_email": "test@test.com",
                    "recipient_name": "Test User"
                }
            ]
        }

        response = client.post("/approvals/validate", json=validation_data, headers=headers)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert "Document not found" in result["errors"][0]
        print("✅ Test validation with invalid document passed")

    def test_create_approval_request_with_validation(self, auth_user_and_headers_with_override, db_session, unique_id):
        """Test completo: validazione + creazione richiesta approvazione"""
        user, headers = auth_user_and_headers_with_override
        
        # Crea documento
        from app.db.models import Document
        doc = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            filename=f"integration_doc_{unique_id}.pdf",
            original_filename=f"Integration Document {unique_id}.pdf",
            storage_path=f"/uploads/integration_doc_{unique_id}.pdf",
            content_type="application/pdf",
            size=3072.0,
            file_hash=f"integrationhash_{unique_id}"
        )
        db_session.add(doc)
        db_session.commit()

        approval_data = {
            "title": f"Final Contract Approval {unique_id}",
            "description": "This is the final version of the contract, please review and approve",
            "document_id": doc.id,
            "approval_type": "all",
            "recipients": [
                {
                    "recipient_email": f"manager_{unique_id}@company.com",
                    "recipient_name": "Department Manager"
                },
                {
                    "recipient_email": f"legal_{unique_id}@company.com",
                    "recipient_name": "Legal Team"
                }
            ],
            "requester_comments": "All changes from previous review have been incorporated"
        }

        # Step 1: Validazione
        validation_response = client.post("/approvals/validate", json=approval_data, headers=headers)
        assert validation_response.status_code == 200
        assert validation_response.json()["valid"] is True
        print("✅ Step 1: Validation passed")

        # Step 2: Creazione
        creation_response = client.post("/approvals/", json=approval_data, headers=headers)

        print(f"🔍 POST /approvals/ - Status: {creation_response.status_code}")
        if creation_response.status_code not in [200, 201]:
            print(f"❌ Error Response: {creation_response.json()}")
        else:
            print(f"📄 Response: {creation_response.json()}")

        assert creation_response.status_code == 201
        result = creation_response.json()
        assert result["title"] == f"Final Contract Approval {unique_id}"
        assert result["status"] == "pending"
        assert len(result["recipients"]) == 2
        print("✅ Step 2: Creation passed")

    def test_get_available_users_excludes_current_user(self, auth_user_and_headers_with_override, test_multiple_users):
        """Test che l'endpoint users escluda l'utente corrente"""
        user, headers = auth_user_and_headers_with_override
        multi_users = test_multiple_users  # 3 utenti aggiuntivi

        response = client.get("/approvals/users", headers=headers)

        assert response.status_code == 200
        users = response.json()
        
        # Verifica che ci siano almeno i 3 utenti multipli
        assert len(users) >= 3
        
        # Verifica che l'utente corrente non sia nella lista
        current_user_emails = [u["email"] for u in users if u["email"] == user.email]
        assert len(current_user_emails) == 0
        
        # Verifica che ci siano gli utenti multipli
        multi_user_emails = [u.email for u in multi_users]
        response_emails = [u["email"] for u in users]
        for email in multi_user_emails:
            assert email in response_emails
            
        print("✅ Test current user exclusion and multiple users presence passed")

    def test_multiple_documents_per_user(self, auth_user_and_headers_with_override, document_factory):
        """Test con multipli documenti per lo stesso utente"""
        user, headers = auth_user_and_headers_with_override
        
        # Crea multipli documenti usando factory
        doc1 = document_factory(user.id, "contract")
        doc2 = document_factory(user.id, "invoice") 
        doc3 = document_factory(user.id, "report")

        response = client.get("/approvals/documents", headers=headers)

        assert response.status_code == 200
        documents = response.json()
        assert len(documents) >= 3
        
        # Verifica che tutti i documenti siano presenti
        doc_ids = [d["id"] for d in documents]
        assert doc1.id in doc_ids
        assert doc2.id in doc_ids
        assert doc3.id in doc_ids
        
        print("✅ Test multiple documents per user passed")

    def test_with_context_manager(self, db_override, auth_user_and_headers_with_override, user_factory):
        """Test usando il context manager per override selettivo"""
        user, headers = auth_user_and_headers_with_override
        
        # Setup fuori dal context
        approver = user_factory("contexttest", "Context Test User")
        
        # Override già attivo dalla fixture auth_user_and_headers_with_override
        response = client.get("/approvals/users", headers=headers)
        
        assert response.status_code == 200
        users = response.json()
        user_emails = [u["email"] for u in users]
        assert approver.email in user_emails
            
        print("✅ Test with context manager passed")

    def test_debug_session_sync(self, auth_user_and_headers_with_override, db_session):
        """Test di debug per verificare sincronizzazione sessioni"""
        user, headers = auth_user_and_headers_with_override
        
        print(f"🔍 DEBUG - User ID: {user.id}")
        print(f"🔍 DEBUG - User Email: {user.email}")
        print(f"🔍 DEBUG - DB Session ID: {id(db_session)}")
        
        # Verifica che l'utente sia visibile nella sessione corrente
        from app.db.models import User
        db_user = db_session.query(User).filter(User.email == user.email).first()
        
        if db_user:
            print(f"✅ DEBUG - User found in session: {db_user.email}")
        else:
            print(f"❌ DEBUG - User NOT found in session!")
            
        # Test semplice per vedere se l'override funziona
        response = client.get("/approvals/users", headers=headers)
        print(f"🔍 DEBUG - Response status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"❌ DEBUG - Auth failed: {response.json()}")
        else:
            print(f"✅ DEBUG - Auth success!")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
