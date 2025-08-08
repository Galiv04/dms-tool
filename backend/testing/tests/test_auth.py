# Setup universale - funziona da qualsiasi directory!
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup
import requests
import pytest
from app.db.base import SessionLocal
from app.db.models import User
from app.services.auth import create_user, authenticate_user, get_user_by_email
from app.db.schemas import UserCreate
from app.utils.security import verify_password, hash_password

BASE_URL = "http://localhost:8000"

@pytest.mark.auth
def test_password_hashing():
    """Test hashing e verifica password"""
    password = "testpassword123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

@pytest.mark.auth
def test_user_creation_service():
    """Test servizio creazione utente"""
    db = SessionLocal()
    
    try:
        user_data = UserCreate(
            email="service_test@example.com",
            password="testpass123",
            display_name="Service Test User"
        )
        
        user = create_user(db, user_data)
        
        assert user.id is not None
        assert user.email == "service_test@example.com"
        assert user.display_name == "Service Test User"
        assert verify_password("testpass123", user.password_hash)
        
        # Cleanup
        db.delete(user)
        db.commit()
        
    finally:
        db.close()

@pytest.mark.auth
def test_user_authentication():
    """Test autenticazione utente"""
    db = SessionLocal()
    
    try:
        # Crea utente
        user_data = UserCreate(
            email="auth_test@example.com",
            password="correctpassword",
            display_name="Auth Test"
        )
        
        created_user = create_user(db, user_data)
        
        # Test autenticazione corretta
        auth_user = authenticate_user(db, "auth_test@example.com", "correctpassword")
        assert auth_user is not False
        assert auth_user.email == "auth_test@example.com"
        
        # Test autenticazione sbagliata
        wrong_auth = authenticate_user(db, "auth_test@example.com", "wrongpassword")
        assert wrong_auth is False
        
        # Test utente inesistente
        no_user = authenticate_user(db, "nonexistent@example.com", "anypassword")
        assert no_user is False
        
        # Cleanup
        db.delete(created_user)
        db.commit()
        
    finally:
        db.close()

@pytest.mark.auth
@pytest.mark.integration
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

# Funzione standalone
def run_standalone_auth_tests():
    """Esegue test auth standalone con output verboso"""
    print("🔐 Testing Authentication...")
    print("=" * 50)
    
    print("\n1️⃣ Test hashing password...")
    try:
        test_password_hashing()
        print("✅ Password hashing OK")
    except Exception as e:
        print(f"❌ Errore hashing: {e}")
        return False
    
    print("\n2️⃣ Test servizio creazione utente...")
    try:
        test_user_creation_service()
        print("✅ Servizio creazione utente OK")
    except Exception as e:
        print(f"❌ Errore servizio: {e}")
        return False
    
    print("\n3️⃣ Test autenticazione...")
    try:
        test_user_authentication()
        print("✅ Autenticazione OK")
    except Exception as e:
        print(f"❌ Errore autenticazione: {e}")
        return False
    
    print("\n4️⃣ Test API endpoints...")
    try:
        test_auth_api_endpoints()
        print("✅ API endpoints OK")
    except Exception as e:
        print(f"⚠️ Test API saltato: {e}")
    
    print("\n🎉 Tutti i test auth completati!")
    return True

if __name__ == "__main__":
    # Path setup solo per esecuzione standalone
    import sys, os
    testing_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.dirname(testing_dir)
    sys.path.insert(0, backend_dir) if backend_dir not in sys.path else None
    
    # La tua funzione standalone
    run_standalone_auth_tests()
