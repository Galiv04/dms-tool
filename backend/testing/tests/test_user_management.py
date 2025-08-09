import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup

import pytest
import uuid
from app.db.base import SessionLocal
from app.db.models import User, UserRole
from app.utils.security import hash_password

@pytest.mark.management
class TestUserManagement:
    """Test class per gestione utenti con isolamento database completo"""
    
    def test_list_users(self, db_session):
        """Test listing utenti con isolamento garantito"""
        # Conta gli utenti iniziali
        initial_count = db_session.query(User).count()
        
        # Crea utenti di test con email univoche
        unique_id = str(uuid.uuid4())[:8]
        test_users = []
        
        for i in range(3):
            user = User(
                email=f"list_test_{unique_id}_{i}@test.com",
                password_hash=hash_password("testpass"),
                display_name=f"List Test User {i}"
            )
            db_session.add(user)
            test_users.append(user)
        
        db_session.commit()
        
        # Verifica conteggio
        new_count = db_session.query(User).count()
        assert new_count == initial_count + 3
        
        # Test query specifica
        users = db_session.query(User).filter(
            User.email.like(f"list_test_{unique_id}_%")
        ).all()
        assert len(users) == 3
        
        # Il rollback automatico della fixture pulirà tutto
    
    @pytest.mark.parametrize("display_name,role", [
        ("Param User 1", UserRole.USER),
        ("Param User 2", UserRole.ADMIN),
        (None, UserRole.USER)
    ])
    def test_create_users_parametrized(self, db_session, display_name, role):
        """Test creazione utenti parametrizzato con email univoche"""
        # Genera email univoca per ogni test
        unique_id = str(uuid.uuid4())[:8]
        email = f"param_{unique_id}@test.com"
        
        user = User(
            email=email,
            password_hash=hash_password("testpass"),
            display_name=display_name,
            role=role
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == email
        assert user.display_name == display_name
        assert user.role == role
        
        # Il rollback automatico della fixture pulirà tutto
    
    @pytest.mark.management
    @pytest.mark.slow
    def test_bulk_operations(self, db_session):
        """Test operazioni bulk con isolamento garantito"""
        # Genera ID univoco per questo test
        unique_id = str(uuid.uuid4())[:8]
        
        # Crea molti utenti con email univoche
        users = []
        for i in range(10):
            user = User(
                email=f"bulk_{unique_id}_{i}@test.com",
                password_hash=hash_password("testpass"),
                display_name=f"Bulk User {i}"
            )
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        # Verifica creazione
        bulk_users = db_session.query(User).filter(
            User.email.like(f"bulk_{unique_id}_%")
        ).all()
        assert len(bulk_users) == 10
        
        # Test eliminazione bulk
        for user in bulk_users:
            db_session.delete(user)
        db_session.commit()
        
        # Verifica eliminazione
        remaining = db_session.query(User).filter(
            User.email.like(f"bulk_{unique_id}_%")
        ).count()
        assert remaining == 0

@pytest.mark.management
def test_user_search_and_filter():
    """Test ricerca e filtro utenti - standalone con cleanup manuale"""
    db = SessionLocal()
    
    try:
        # Genera ID univoco per questo test
        unique_id = str(uuid.uuid4())[:8]
        
        # Crea utenti con pattern diversi e email univoche
        test_data = [
            (f"admin_{unique_id}@test.com", "Admin User", UserRole.ADMIN),
            (f"user1_{unique_id}@test.com", "Regular User 1", UserRole.USER),
            (f"user2_{unique_id}@test.com", "Regular User 2", UserRole.USER),
            (f"special_{unique_id}@example.com", "Special User", UserRole.USER)
        ]
        
        created_users = []
        for email, name, role in test_data:
            user = User(
                email=email,
                password_hash=hash_password("testpass"),
                display_name=name,
                role=role
            )
            db.add(user)
            created_users.append(user)
        
        db.commit()
        
        # Test filtro per ruolo
        admins = db.query(User).filter(User.role == UserRole.ADMIN).filter(
            User.email.like(f"%_{unique_id}@%")
        ).all()
        assert len(admins) == 1
        assert admins[0].email.startswith(f"admin_{unique_id}")
        
        # Test filtro per dominio email
        test_domain_users = db.query(User).filter(
            User.email.like(f"%_{unique_id}@test.com")
        ).all()
        assert len(test_domain_users) == 3
        
        # Cleanup manuale per test standalone
        for user in created_users:
            db.delete(user)
        db.commit()
        
    finally:
        db.close()

# Funzioni standalone per compatibilità
def run_management_tests():
    """Esegue test management standalone"""
    print("👥 Testing User Management...")
    print("=" * 50)
    
    print("\n1️⃣ Test ricerca e filtro...")
    try:
        test_user_search_and_filter()
        print("✅ Ricerca e filtro OK")
    except Exception as e:
        print(f"❌ Errore ricerca: {e}")
        return False
    
    print("\n2️⃣ Test operazioni base...")
    db = SessionLocal()
    try:
        unique_id = str(uuid.uuid4())[:8]
        initial_count = db.query(User).count()
        print(f"📊 Utenti attuali nel DB: {initial_count}")
        
        # Crea un utente di test con email univoca
        test_user = User(
            email=f"standalone_test_{unique_id}@test.com",
            password_hash=hash_password("testpass"),
            display_name="Standalone Test User"
        )
        db.add(test_user)
        db.commit()
        
        new_count = db.query(User).count()
        assert new_count == initial_count + 1
        print("✅ Creazione utente OK")
        
        # Cleanup
        db.delete(test_user)
        db.commit()
        print("✅ Eliminazione utente OK")
        
    finally:
        db.close()
    
    print("\n🎉 Test user management completati!")
    return True

if __name__ == "__main__":
    run_management_tests()
