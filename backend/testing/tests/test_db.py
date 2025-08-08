# Setup universale - funziona da qualsiasi directory!
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup

# Import diretti
from app.db.base import SessionLocal
from app.db.models import User, UserRole
from app.utils.security import hash_password
import pytest

# ... resto del codice identico


@pytest.mark.db
def test_database():
    """Test del database - compatibile pytest e standalone"""
    db = SessionLocal()
    
    try:
        test_user = User(
            email="test@example.com",
            password_hash=hash_password("testpassword"),
            display_name="Test User",
            role=UserRole.USER
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        assert test_user.id is not None
        assert test_user.email == "test@example.com"
        assert test_user.display_name == "Test User"
        
        user_from_db = db.query(User).filter(User.email == "test@example.com").first()
        assert user_from_db is not None
        assert user_from_db.email == "test@example.com"
        
        db.delete(test_user)
        db.commit()
        
    finally:
        db.close()

@pytest.mark.db
def test_user_creation_detailed():
    """Test dettagliato creazione utente"""
    db = SessionLocal()
    
    try:
        user = User(
            email="minimal@test.com",
            password_hash=hash_password("password123")
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.id is not None
        assert user.email == "minimal@test.com"
        assert user.display_name is None
        assert user.role == UserRole.USER
        
        full_user = User(
            email="full@test.com",
            password_hash=hash_password("password123"),
            display_name="Full Test User",
            role=UserRole.ADMIN
        )
        
        db.add(full_user)
        db.commit()
        db.refresh(full_user)
        
        assert full_user.display_name == "Full Test User"
        assert full_user.role == UserRole.ADMIN
        
        db.delete(user)
        db.delete(full_user)
        db.commit()
        
    finally:
        db.close()

def run_standalone_tests():
    """Esegue test standalone con output verboso"""
    print("🧪 Testing Database...")
    print("=" * 50)
    
    print("\n1️⃣ Test creazione utente base...")
    try:
        test_database()
        print("✅ Test database base completato")
    except Exception as e:
        print(f"❌ Errore test database: {e}")
        return False
    
    print("\n2️⃣ Test creazione utente dettagliato...")
    try:
        test_user_creation_detailed()
        print("✅ Test dettagliato completato")
    except Exception as e:
        print(f"❌ Errore test dettagliato: {e}")
        return False
    
    print("\n🎉 Tutti i test database completati con successo!")
    return True

# Per esecuzione standalone
if __name__ == "__main__":
    run_standalone_tests()
