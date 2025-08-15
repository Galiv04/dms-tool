import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
import universal_setup

import pytest
import uuid
from app.db.base import SessionLocal, engine
from app.db.models import User, UserRole
from app.services.auth import hash_password

@pytest.mark.db
def test_database():
    """Test del database - compatibile pytest e standalone"""
    db = SessionLocal()
    unique_id = str(uuid.uuid4())[:8]
    
    try:
        # Crea email unica
        test_email = f"test_{unique_id}@example.com"  # 🔧 Usa variabile
        
        test_user = User(
            email=test_email,
            password_hash=hash_password("testpassword"),
            display_name="Test User",
            role=UserRole.USER
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        assert test_user.id is not None
        assert test_user.email == test_email  # 🔧 FIX: usa email dinamica
        assert test_user.display_name == "Test User"
        assert test_user.role == UserRole.USER
        assert test_user.created_at is not None
        
        print(f"✅ Database test passed with user: {test_user.email}")
        
    finally:
        db.close()

@pytest.mark.db
def test_user_creation_detailed():
    """Test dettagliato creazione utente"""
    db = SessionLocal()
    unique_id = str(uuid.uuid4())[:8]
    
    try:
        # Crea email unica
        test_email = f"minimal_{unique_id}@test.com"  # 🔧 Usa variabile
        
        user = User(
            email=test_email,
            password_hash=hash_password("password123")
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Test basic properties
        assert user.id is not None
        assert user.email == test_email  # 🔧 FIX: usa email dinamica
        assert user.password_hash is not None
        assert user.password_hash != "password123"  # Verifica che sia hashata
        assert user.created_at is not None
        
        # Test default values
        assert user.role == UserRole.USER  # Default role
        assert user.display_name is None  # Non specificato
        
        # Test database constraints
        assert len(user.email) > 0
        assert "@" in user.email
        
        print(f"✅ Detailed user creation test passed with: {user.email}")
        
    finally:
        db.close()

if __name__ == "__main__":
    # Per esecuzione standalone
    print("🧪 Running database tests...")
    
    test_database()
    print("✅ Database test passed")
    
    test_user_creation_detailed()  
    print("✅ User creation detailed test passed")
    
    print("🎉 All database tests passed!")
