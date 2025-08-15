import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup
import requests
import pytest
from app.db.base import SessionLocal
from app.db.models import UserRole
from app.services.auth import create_user, authenticate_user, get_user_by_email
from app.db.schemas import UserCreate
from app.utils.security import verify_password, hash_password
import uuid

BASE_URL = "http://localhost:8000" 

@pytest.mark.auth
def test_password_hashing():
    """Test hash delle password"""
    password = "testpassword123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert len(hashed) > 0
    assert "$argon2id$" in hashed

@pytest.mark.auth
def test_user_creation_service():
    """Test servizio creazione utente"""
    db = SessionLocal()
    unique_id = str(uuid.uuid4())[:8]
    
    try:
        # Crea email unica
        test_email = f"service_test_{unique_id}@example.com"
        
        user_data = UserCreate(
            email=test_email,  # 🔧 Usa variabile
            password="testpass123",
            display_name="Service Test User"
        )
        
        user = create_user(db, user_data)
        
        assert user.id is not None
        assert user.email == test_email  # 🔧 Fix: confronta con email dinamica
        assert user.display_name == "Service Test User"
        assert user.role == UserRole.USER
        assert user.password_hash != "testpass123"  # Verifica che sia hashata
        
        print(f"✅ Created user: {user.email}")
        
    finally:
        db.close()

@pytest.mark.auth
def test_user_authentication():
    """Test autenticazione utente"""
    db = SessionLocal()
    unique_id = str(uuid.uuid4())[:8]
    
    try:
        # Crea email unica
        test_email = f"auth_test_{unique_id}@example.com"
        test_password = "correctpassword"
        
        # Crea utente
        user_data = UserCreate(
            email=test_email,  # 🔧 Fix: usa stessa email per creazione
            password=test_password,
            display_name="Auth Test User"
        )
        created_user = create_user(db, user_data)
        
        print(f"✅ Created user for auth test: {created_user.email}")
        
        # Test autenticazione corretta con STESSA email
        auth_user = authenticate_user(db, test_email, test_password)  # 🔧 Fix: usa stessa email
        assert auth_user is not False
        assert auth_user.email == test_email
        
        # Test autenticazione con password sbagliata
        false_auth = authenticate_user(db, test_email, "wrongpassword")
        assert false_auth is False
        
        # Test autenticazione con email inesistente
        false_auth2 = authenticate_user(db, f"nonexistent_{unique_id}@example.com", test_password)
        assert false_auth2 is False
        
        print(f"✅ Authentication tests passed for: {test_email}")
        
    finally:
        db.close()

@pytest.mark.auth
def test_auth_api_endpoints():
    """Test endpoint API autenticazione"""
    # Test registrazione
    register_data = {
        "email": "api_test@example.com",
        "password": "testpass123",
        "display_name": "API Test User"
    }
    
    try:
        register_response = requests.post(
            f"{BASE_URL}/auth/register",
            json=register_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if register_response.status_code == 200:
            user_data = register_response.json()
            assert user_data["email"] == "api_test@example.com"
            
            # Test login
            login_data = {
                "username": "api_test@example.com",
                "password": "testpass123"
            }
            
            login_response = requests.post(
                f"{BASE_URL}/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=5
            )
            
            if login_response.status_code == 200:
                login_result = login_response.json()
                token = login_result["access_token"]
                assert token is not None
                
                # Test /me endpoint
                headers = {"Authorization": f"Bearer {token}"}
                me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=5)
                
                if me_response.status_code == 200:
                    me_data = me_response.json()
                    assert me_data["email"] == "api_test@example.com"
                
        # Cleanup - elimina utente creato
        db = SessionLocal()
        try:
            user = get_user_by_email(db, "api_test@example.com")
            if user:
                db.delete(user)
                db.commit()
        finally:
            db.close()
            
    except requests.exceptions.RequestException:
        pytest.skip("Backend non raggiungibile per test API")

if __name__ == "__main__":
    # Per esecuzione standalone
    print("🧪 Running auth tests...")
    test_password_hashing()
    print("✅ Password hashing test passed")
    
    test_user_creation_service()
    print("✅ User creation service test passed")
    
    test_user_authentication()
    print("✅ User authentication test passed")
    
    test_auth_api_endpoints()
    print("✅ Auth API endpoints test passed")
    
    print("🎉 All auth tests passed!")
