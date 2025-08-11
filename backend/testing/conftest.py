import sys
import os
import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Setup automatico del path per pytest
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import dopo setup del path
from app.db.base import Base
from app.db.models import User, UserRole
from app.utils.security import hash_password, create_access_token
from app.main import app

# ✅ Database URL per test - In-memory per evitare locking
TEST_DATABASE_URL = "sqlite://"  # In-memory database

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture database con isolamento completo per test API
    Usa database in-memory per evitare conflitti e locking
    """
    # Crea engine con StaticPool per database in-memory
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Cambia a True per debug SQL queries
    )
    
    # Crea tutte le tabelle nel database in-memory
    Base.metadata.create_all(bind=engine)
    
    # Crea sessione
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        # Cleanup completo
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

@pytest.fixture
def db_session_real():
    """
    Fixture database per sessione REALE (senza rollback)
    Usata quando serve persistenza reale tra operazioni
    ⚠️ ATTENZIONE: Questa fixture non fa rollback automatico
    """
    from app.db.base import SessionLocal
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def test_user_data():
    """Fixture con dati utente di test standardizzati"""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"pytest_user_{unique_id}@test.com",
        "password": "testpass123",
        "display_name": f"Pytest Test User {unique_id}"
    }

@pytest.fixture
def test_user_and_token(db_session):
    """
    Fixture che crea un utente di test e il suo token JWT
    Perfetta per test API che richiedono autenticazione
    """
    unique_id = str(uuid.uuid4())[:8]
    
    # Crea utente di test
    user = User(
        email=f"api_user_{unique_id}@test.com",
        password_hash=hash_password("testpass123"),
        display_name=f"API Test User {unique_id}",
        role=UserRole.USER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Crea token JWT
    token = create_access_token(data={"sub": user.email})
    
    return user, token

@pytest.fixture
def test_admin_and_token(db_session):
    """
    Fixture che crea un admin di test e il suo token JWT
    Per test che richiedono privilegi amministrativi
    """
    unique_id = str(uuid.uuid4())[:8]
    
    # Crea admin di test
    admin = User(
        email=f"api_admin_{unique_id}@test.com",
        password_hash=hash_password("adminpass123"),
        display_name=f"API Test Admin {unique_id}",
        role=UserRole.ADMIN
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    
    # Crea token JWT
    token = create_access_token(data={"sub": admin.email})
    
    return admin, token

@pytest.fixture
def test_client():
    """
    Fixture per TestClient FastAPI
    Con configurazione ottimizzata per test
    """
    return TestClient(app)

@pytest.fixture
def test_multiple_users(db_session):
    """
    Fixture che crea multipli utenti di test per test complessi
    Restituisce lista di (user, token) tuple
    """
    users_and_tokens = []
    
    for i in range(3):
        unique_id = str(uuid.uuid4())[:8]
        
        user = User(
            email=f"multi_user_{i}_{unique_id}@test.com",
            password_hash=hash_password("testpass123"),
            display_name=f"Multi Test User {i} {unique_id}",
            role=UserRole.USER
        )
        db_session.add(user)
        db_session.flush()  # Per ottenere ID senza commit finale
        
        token = create_access_token(data={"sub": user.email})
        users_and_tokens.append((user, token))
    
    db_session.commit()
    
    # Refresh tutti gli utenti
    for user, _ in users_and_tokens:
        db_session.refresh(user)
    
    return users_and_tokens

# ✅ Configurazione markers pytest
def pytest_configure(config):
    """Configurazione automatica pytest con markers"""
    config.addinivalue_line("markers", "db: marks tests as database tests")
    config.addinivalue_line("markers", "admin: tests for admin functionality")
    config.addinivalue_line("markers", "auth: marks tests as authentication tests")
    config.addinivalue_line("markers", "management: marks tests as user management tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "api: marks tests as API endpoint tests")
    config.addinivalue_line("markers", "approval: marks tests as approval workflow tests")
    config.addinivalue_line("markers", "security: marks tests as security-related tests")

# ✅ Hook per cleanup automatico alla fine della sessione
def pytest_sessionfinish(session, exitstatus):
    """
    Hook eseguito alla fine di tutta la sessione pytest
    Cleanup finale per sicurezza
    """
    try:
        # Cleanup finale del database di test se necessario
        from app.db.base import SessionLocal
        db = SessionLocal()
        
        # Rimuovi eventuali utenti di test rimasti
        test_users = db.query(User).filter(
            User.email.like('%pytest%') | 
            User.email.like('%api_test_%') |
            User.email.like('%api_user_%') |
            User.email.like('%multi_user_%')
        ).all()
        
        if test_users:
            print(f"\n🧹 Final cleanup: removing {len(test_users)} test users")
            for user in test_users:
                db.delete(user)
            db.commit()
        
        db.close()
        
    except Exception as e:
        print(f"⚠️ Final cleanup error: {e}")

# ✅ Setup logging automatico per i test
@pytest.fixture(autouse=True)
def setup_logging():
    """
    Fixture automatica per setup logging nei test
    Configura logging per debug dei test
    """
    import logging
    
    # Configura logging per test
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Silenzia log troppo verbosi durante test
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
