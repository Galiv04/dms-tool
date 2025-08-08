# Setup universale - funziona da qualsiasi directory!
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup
import pytest
from app.db.base import SessionLocal
from app.db.models import User, UserRole
from app.utils.security import hash_password

@pytest.mark.management
class TestUserManagement:
    """Test class per gestione utenti"""
    
    def test_list_users(self, fresh_db_session):
        """Test listing utenti"""
        initial_count = fresh_db_session.query(User).count()
        
        # Crea utenti di test
        test_users = []
        for i in range(3):
            user = User(
                email=f"list_test_{i}@test.com",
                password_hash=hash_password("testpass"),
                display_name=f"List Test User {i}"
            )
            fresh_db_session.add(user)
            test_users.append(user)
        
        fresh_db_session.commit()
        
        # Verifica conteggio
        new_count = fresh_db_session.query(User).count()
        assert new_count == initial_count + 3
        
        # Test query specifica
        users = fresh_db_session.query(User).filter(
            User.email.like("list_test_%")
        ).all()
        assert len(users) == 3
        
        # Cleanup
        for user in test_users:
            fresh_db_session.delete(user)
        fresh_db_session.commit()
    
    @pytest.mark.parametrize("email,display_name,role", [
        ("param1@test.com", "Param User 1", UserRole.USER),
        ("param2@test.com", "Param User 2", UserRole.ADMIN),
        ("param3@test.com", None, UserRole.USER)
    ])
    def test_create_users_parametrized(self, fresh_db_session, email, display_name, role):
        """Test creazione utenti parametrizzato"""
        user = User(
            email=email,
            password_hash=hash_password("testpass"),
            display_name=display_name,
            role=role
        )
        
        fresh_db_session.add(user)
        fresh_db_session.commit()
        fresh_db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == email
        assert user.display_name == display_name
        assert user.role == role
        
        # Cleanup
        fresh_db_session.delete(user)
        fresh_db_session.commit()
    
    @pytest.mark.management
    @pytest.mark.slow
    def test_bulk_operations(self, fresh_db_session):
        """Test operazioni bulk"""
        # Crea molti utenti
        users = []
        for i in range(10):
            user = User(
                email=f"bulk_{i}@test.com",
                password_hash=hash_password("testpass"),
                display_name=f"Bulk User {i}"
            )
            users.append(user)
        
        fresh_db_session.add_all(users)
        fresh_db_session.commit()
        
        # Verifica creazione
        bulk_users = fresh_db_session.query(User).filter(
            User.email.like("bulk_%")
        ).all()
        assert len(bulk_users) == 10
        
        # Test eliminazione bulk
        for user in bulk_users:
            fresh_db_session.delete(user)
        fresh_db_session.commit()
        
        # Verifica eliminazione
        remaining = fresh_db_session.query(User).filter(
            User.email.like("bulk_%")
        ).count()
        assert remaining == 0

@pytest.mark.management
def test_user_search_and_filter():
    """Test ricerca e filtro utenti"""
    db = SessionLocal()
    
    try:
        # Crea utenti con pattern diversi
        test_data = [
            ("admin@test.com", "Admin User", UserRole.ADMIN),
            ("user1@test.com", "Regular User 1", UserRole.USER),
            ("user2@test.com", "Regular User 2", UserRole.USER),
            ("special@example.com", "Special User", UserRole.USER)
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
            User.email.in_([u.email for u in created_users])
        ).all()
        assert len(admins) == 1
        assert admins[0].email == "admin@test.com"
        
        # Test filtro per dominio email
        test_domain_users = db.query(User).filter(
            User.email.like("%@test.com")
        ).filter(
            User.email.in_([u.email for u in created_users])
        ).all()
        assert len(test_domain_users) == 3
        
        # Cleanup
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
        # Simula test di listing
        initial_count = db.query(User).count()
        print(f"📊 Utenti attuali nel DB: {initial_count}")
        
        # Crea un utente di test
        test_user = User(
            email="standalone_test@test.com",
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
    # Path setup solo per esecuzione standalone
    import sys, os
    testing_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.dirname(testing_dir)
    sys.path.insert(0, backend_dir) if backend_dir not in sys.path else None
    
    # La tua funzione standalone
    run_management_tests()
