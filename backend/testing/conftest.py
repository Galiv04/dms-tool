import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
import uuid
import random
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base, get_db
from app.db.models import User, Document
from app.services.auth import create_user, authenticate_user
from app.db.schemas import UserCreate

# ===== PYTEST CONFIGURATION =====

def pytest_configure(config):
    """Configurazione globale pytest"""
    # Registra markers personalizzati
    config.addinivalue_line(
        "markers", "api: mark test as API integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication related"
    )
    config.addinivalue_line(
        "markers", "documents: mark test as document management related"
    )
    config.addinivalue_line(
        "markers", "approvals: mark test as approval workflow related"
    )
    config.addinivalue_line(
        "markers", "email: mark test as email notification related"
    )
    config.addinivalue_line(
        "markers", "rbac: mark test as role-based access control related"
    )
    # ✅ AGGIUNTI I MARKERS MANCANTI:
    config.addinivalue_line(
        "markers", "admin: mark test as admin related"
    )
    config.addinivalue_line(
        "markers", "db: mark test as database related"
    )
    config.addinivalue_line(
        "markers", "management: mark test as management related"
    )

def pytest_collection_modifyitems(config, items):
    """Modifica items durante collection per aggiungere markers automatici"""
    for item in items:
        # Auto-mark basato sul nome del file
        if "test_auth" in str(item.fspath):
            item.add_marker(pytest.mark.auth)
        elif "test_document" in str(item.fspath):
            item.add_marker(pytest.mark.documents)
        elif "test_approval" in str(item.fspath):
            item.add_marker(pytest.mark.approvals)
        
        # Auto-mark per test lenti (contenenti 'slow' nel nome)
        if "slow" in item.name.lower():
            item.add_marker(pytest.mark.slow)

# ===== DATABASE SETUP =====

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=False  # Set True for SQL debugging
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ===== SESSION SCOPE FIXTURES =====

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Setup dell'ambiente di test per tutta la sessione
    Configurazioni globali che si applicano a tutti i test
    """
    print("\n🚀 Setting up test environment...")
    
    # Override configurazioni per test
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = SQLALCHEMY_TEST_DATABASE_URL
    os.environ["LOG_LEVEL"] = "WARNING"  # Riduci logging durante test
    
    # Setup logging per test
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Disabilita alcuni logger verbose durante i test
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    
    yield
    
    # Session cleanup
    print("\n🧹 Cleaning up test environment...")
    cleanup_environment_vars = ["TESTING", "LOG_LEVEL"]
    for var in cleanup_environment_vars:
        if var in os.environ:
            del os.environ[var]

@pytest.fixture(scope="session")
def setup_logging():
    """Setup logging specifico per test con configurazione ottimizzata"""
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    
    # Console handler per test
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - TEST - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

@pytest.fixture(scope="session")
def test_client():
    """Client di test FastAPI condiviso per la sessione"""
    return TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Setup database di test per l'intera sessione
    Crea engine e prepara struttura database
    """
    print("\n🔧 Setting up test database...")
    
    # Assicurati che il database sia pulito all'inizio
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception as e:
        print(f"⚠️ Warning during initial cleanup: {e}")
    
    # Crea tutte le tabelle
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Session cleanup - rimuovi tutto
    print("\n🧹 Cleaning up test database...")
    try:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
    except Exception as e:
        print(f"⚠️ Warning during database cleanup: {e}")

# ===== FUNCTION SCOPE DATABASE FIXTURES =====

@pytest.fixture(scope="function")
def db_session():
    """
    Sessione database isolata per ogni test
    Ogni test ha una transazione separata con rollback automatico
    """
    # Crea sessione di test
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        # Rollback di tutte le transazioni
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def db_session_real():
    """
    Sessione database reale (con commit)
    Da usare quando serve persistenza tra operazioni nel test
    """
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        # Cleanup esplicito invece di rollback
        try:
            # Rimuovi tutti i dati di test
            session.execute(text("DELETE FROM approval_recipients"))
            session.execute(text("DELETE FROM approval_requests"))
            session.execute(text("DELETE FROM audit_logs"))
            session.execute(text("DELETE FROM documents"))
            session.execute(text("DELETE FROM users"))
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"⚠️ Warning during real session cleanup: {e}")
        finally:
            session.close()

# ===== DB OVERRIDE FIXTURES =====

@pytest.fixture
def db_override(db_session):
    """
    Fixture per override automatico di get_db
    Restituisce un context manager per override temporaneo
    
    Uso:
    def test_something(self, db_override, auth_user_and_headers):
        with db_override:
            # test code here
    """
    @contextmanager
    def override_context():
        def override_get_db():
            return db_session
        
        # Salva override precedenti
        original_overrides = app.dependency_overrides.copy()
        
        # Imposta nuovo override
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            yield
        finally:
            # Ripristina stato precedente
            app.dependency_overrides.clear()
            app.dependency_overrides.update(original_overrides)
    
    return override_context

@pytest.fixture
def db_override_auto(db_session):
    """
    Fixture per override automatico di get_db (autouse)
    Si applica automaticamente al test senza context manager
    
    IMPORTANTE: Questa fixture deve essere richiesta PRIMA di altre fixture
    che dipendono da get_db (come auth_user_and_headers)
    """
    def override_get_db():
        return db_session
    
    # Salva override precedenti
    original_overrides = app.dependency_overrides.copy()
    
    # Imposta nuovo override
    app.dependency_overrides[get_db] = override_get_db
    
    yield db_session  # Restituisce la sessione per eventuale uso diretto
    
    # Ripristina stato precedente
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)

@pytest.fixture
def db_with_override(db_session):
    """
    Fixture combinata: sessione DB + override automatico
    Restituisce la sessione DB con override già attivo
    """
    def override_get_db():
        return db_session
    
    # Salva override precedenti
    original_overrides = app.dependency_overrides.copy()
    
    # Imposta nuovo override
    app.dependency_overrides[get_db] = override_get_db
    
    yield db_session
    
    # Ripristina stato precedente
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)

# ===== USER FIXTURES =====

@pytest.fixture
def test_user_data():
    """Dati standard per utente di test"""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"test_user_{unique_id}@test.com",
        "password": "testpass123",
        "display_name": f"Test User {unique_id}"
    }

@pytest.fixture
def test_user_and_token(db_session, test_client):
    """
    Fixture principale: crea utente di test e genera token JWT
    Restituisce: (user_object, jwt_token_string)
    
    NOTA: Questa fixture richiede che l'override di get_db sia già attivo
    """
    unique_id = str(uuid.uuid4())[:8]
    
    try:
        # Crea utente
        user_data = UserCreate(
            email=f"api_user_{unique_id}@test.com",
            password="testpass123",
            display_name=f"API Test User {unique_id}"
        )
        
        user = create_user(db_session, user_data)
        db_session.commit()
        db_session.refresh(user)
        
        # Genera token tramite login
        login_data = {
            "username": user.email,
            "password": "testpass123"
        }
        
        login_response = test_client.post("/auth/login", data=login_data)
        
        if login_response.status_code != 200:
            raise Exception(f"Login failed for test user: {login_response.json()}")
        
        token = login_response.json()["access_token"]
        return user, token
        
    except Exception as e:
        db_session.rollback()
        raise Exception(f"Failed to create test user and token: {e}")

@pytest.fixture
def auth_headers(test_user_and_token):
    """
    Headers di autenticazione pronti all'uso
    Restituisce: {"Authorization": "Bearer <token>"}
    """
    user, token = test_user_and_token
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_user_and_headers(test_user_and_token):
    """
    Fixture combinata: utente + headers
    Restituisce: (user_object, headers_dict)
    
    NOTA: Richiede che l'override di get_db sia già attivo prima di essere chiamata
    """
    user, token = test_user_and_token
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers

# ===== FIXTURE COMBINATE CON OVERRIDE =====

@pytest.fixture
def auth_user_and_headers_with_override(db_session, test_client):
    """
    Fixture all-in-one: crea utente, token, headers E attiva override
    Questa fixture garantisce l'ordine corretto delle operazioni
    
    Restituisce: (user_object, headers_dict)
    """
    # Prima attiva l'override
    def override_get_db():
        return db_session
    
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # Poi crea utente
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"api_user_{unique_id}@test.com",
            password="testpass123",
            display_name=f"API Test User {unique_id}"
        )
        
        user = create_user(db_session, user_data)
        db_session.commit()
        db_session.refresh(user)
        
        # Genera token
        login_data = {
            "username": user.email,
            "password": "testpass123"
        }
        
        login_response = test_client.post("/auth/login", data=login_data)
        
        if login_response.status_code != 200:
            raise Exception(f"Login failed: {login_response.json()}")
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        yield user, headers
        
    finally:
        # Cleanup
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

@pytest.fixture
def test_admin_and_token(db_session, test_client):
    """
    Crea utente admin di test con token
    TODO: Implementare quando avremo RBAC
    """
    unique_id = str(uuid.uuid4())[:8]
    
    try:
        # Crea admin user
        admin_data = UserCreate(
            email=f"admin_{unique_id}@test.com",
            password="adminpass123",
            display_name=f"Admin User {unique_id}"
        )
        
        admin = create_user(db_session, admin_data)
        # TODO: Assegnare ruolo admin quando implementeremo RBAC
        db_session.commit()
        db_session.refresh(admin)
        
        # Genera token con override temporaneo
        login_data = {
            "username": admin.email,
            "password": "adminpass123"
        }
        
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            login_response = test_client.post("/auth/login", data=login_data)
        finally:
            if get_db in app.dependency_overrides:
                del app.dependency_overrides[get_db]
        
        if login_response.status_code != 200:
            raise Exception(f"Admin login failed: {login_response.json()}")
        
        token = login_response.json()["access_token"]
        return admin, token
        
    except Exception as e:
        db_session.rollback()
        raise Exception(f"Failed to create admin user: {e}")

@pytest.fixture
def test_multiple_users(db_session):
    """
    Crea multipli utenti di test per scenari complessi
    Restituisce: [user1, user2, user3]
    """
    users = []
    try:
        for i in range(3):
            unique_id = str(uuid.uuid4())[:8]
            user_data = UserCreate(
                email=f"multiuser_{i}_{unique_id}@test.com",
                password="testpass123",
                display_name=f"Multi Test User {i}"
            )
            user = create_user(db_session, user_data)
            users.append(user)
        
        db_session.commit()
        for user in users:
            db_session.refresh(user)
        
        return users
        
    except Exception as e:
        db_session.rollback()
        raise Exception(f"Failed to create multiple users: {e}")

# ===== DOCUMENT FIXTURES =====

@pytest.fixture
def test_document(auth_user_and_headers_with_override, db_session):
    """
    Crea un documento di test standard
    Usa la fixture combinata per garantire l'override
    Restituisce: document_object
    """
    user, headers = auth_user_and_headers_with_override
    unique_id = str(uuid.uuid4())[:8]
    
    try:
        doc = Document(
            id=str(uuid.uuid4()),
            owner_id=user.id,
            filename=f"test_doc_{unique_id}.pdf",
            original_filename=f"Test Document {unique_id}.pdf",
            storage_path=f"/uploads/test_doc_{unique_id}.pdf",
            content_type="application/pdf",
            size=random.randint(1000, 5000),
            file_hash=f"testhash_{unique_id}"
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)
        return doc
        
    except Exception as e:
        db_session.rollback()
        raise Exception(f"Failed to create test document: {e}")

@pytest.fixture
def test_document_with_custom_owner(db_session):
    """
    Factory per creare documento con owner specifico
    Uso: test_document_with_custom_owner(user_id)
    """
    def create_document(owner_id, filename_prefix="custom_doc"):
        unique_id = str(uuid.uuid4())[:8]
        try:
            doc = Document(
                id=str(uuid.uuid4()),
                owner_id=owner_id,
                filename=f"{filename_prefix}_{unique_id}.pdf",
                original_filename=f"Custom Document {unique_id}.pdf",
                storage_path=f"/uploads/{filename_prefix}_{unique_id}.pdf",
                content_type="application/pdf",
                size=random.randint(1000, 5000),
                file_hash=f"customhash_{unique_id}"
            )
            db_session.add(doc)
            db_session.commit()
            db_session.refresh(doc)
            return doc
        except Exception as e:
            db_session.rollback()
            raise Exception(f"Failed to create custom document: {e}")
    return create_document

# ===== FACTORY FIXTURES =====

@pytest.fixture
def user_factory(db_session):
    """
    Factory per creare utenti al volo nei test
    Uso: user_factory(email_prefix="approver", display_name="Approver")
    """
    def create_test_user(email_prefix="test", display_name=None):
        unique_id = str(uuid.uuid4())[:8]
        try:
            user_data = UserCreate(
                email=f"{email_prefix}_{unique_id}@test.com",
                password="testpass123",
                display_name=display_name or f"Test User {unique_id}"
            )
            user = create_user(db_session, user_data)
            db_session.commit()
            db_session.refresh(user)
            return user
        except Exception as e:
            db_session.rollback()
            raise Exception(f"Failed to create user via factory: {e}")
    return create_test_user

@pytest.fixture
def document_factory(db_session):
    """
    Factory per creare documenti al volo
    Uso: document_factory(owner_id, filename_prefix="contract")
    """
    def create_test_document(owner_id, filename_prefix="test_doc", content_type="application/pdf"):
        unique_id = str(uuid.uuid4())[:8]
        try:
            doc = Document(
                id=str(uuid.uuid4()),
                owner_id=owner_id,
                filename=f"{filename_prefix}_{unique_id}.pdf",
                original_filename=f"Factory Document {unique_id}.pdf",
                storage_path=f"/uploads/{filename_prefix}_{unique_id}.pdf",
                content_type=content_type,
                size=random.randint(1000, 5000),
                file_hash=f"factoryhash_{unique_id}"
            )
            db_session.add(doc)
            db_session.commit()
            db_session.refresh(doc)
            return doc
        except Exception as e:
            db_session.rollback()
            raise Exception(f"Failed to create document via factory: {e}")
    return create_test_document

# ===== UTILITY FIXTURES =====

@pytest.fixture
def unique_id():
    """Genera un ID univoco per il test corrente"""
    return str(uuid.uuid4())[:8]

@pytest.fixture
def test_email_domain():
    """Dominio email standard per i test"""
    return "test.com"

@pytest.fixture
def cleanup_test_files():
    """
    Cleanup automatico dei file di test
    TODO: Implementare quando avremo file storage reale
    """
    created_files = []
    
    def add_file(file_path):
        created_files.append(file_path)
    
    yield add_file
    
    # Cleanup dopo il test
    for file_path in created_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"⚠️ Warning: Could not cleanup file {file_path}: {e}")

# ===== MOCK SERVICES =====

@pytest.fixture
def mock_email_service():
    """
    Mock del servizio email per i test
    Utile per testare notifiche senza inviare email reali
    """
    class MockEmailService:
        def __init__(self):
            self.sent_emails = []
            self.should_fail = False
        
        def send_email(self, to, subject, body, **kwargs):
            if self.should_fail:
                raise Exception("Mock email service failure")
            
            self.sent_emails.append({
                "to": to,
                "subject": subject, 
                "body": body,
                "kwargs": kwargs
            })
            return True
        
        def send_approval_notification(self, approval_request, recipient):
            return self.send_email(
                to=recipient.recipient_email,
                subject=f"Approval Request: {approval_request.title}",
                body=f"Please review and approve: {approval_request.description}"
            )
        
        def clear(self):
            self.sent_emails = []
            self.should_fail = False
        
        def fail_next(self):
            self.should_fail = True
    
    return MockEmailService()

@pytest.fixture
def mock_file_storage():
    """
    Mock del file storage per i test
    TODO: Implementare quando testiamo upload/download file
    """
    class MockFileStorage:
        def __init__(self):
            self.stored_files = {}
        
        def store_file(self, file_data, filename):
            file_id = str(uuid.uuid4())
            self.stored_files[file_id] = {
                "filename": filename,
                "data": file_data,
                "size": len(file_data) if isinstance(file_data, bytes) else 0
            }
            return file_id
        
        def get_file(self, file_id):
            return self.stored_files.get(file_id)
        
        def delete_file(self, file_id):
            return self.stored_files.pop(file_id, None)
        
        def clear(self):
            self.stored_files = {}
    
    return MockFileStorage()

# ===== CLEANUP HOOKS =====

@pytest.fixture(autouse=True)
def cleanup_dependency_overrides():
    """
    Cleanup automatico degli override delle dependency FastAPI
    Previene interferenze tra test
    """
    # Salva override esistenti
    original_overrides = app.dependency_overrides.copy()
    
    yield
    
    # Ripristina stato originale
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)

def pytest_runtest_teardown(item, nextitem):
    """
    Hook per cleanup dopo ogni test
    Assicura che non ci siano side effects tra test
    """
    # Cleanup degli override FastAPI dependency
    app.dependency_overrides.clear()
    
    # Force garbage collection per test pesanti
    if hasattr(item, 'get_closest_marker'):
        if item.get_closest_marker('slow'):
            import gc
            gc.collect()

def pytest_sessionfinish(session, exitstatus):
    """
    Hook per cleanup finale della sessione di test
    Eseguito alla fine di tutti i test
    """
    print(f"\n🏁 Test session finished with exit status: {exitstatus}")
    
    # Cleanup finale del database di test
    try:
        if os.path.exists("./test.db"):
            os.remove("./test.db")
            print("🧹 Removed test database file")
    except Exception as e:
        print(f"⚠️ Warning: Could not remove test database: {e}")
    
    # Cleanup di eventuali file temporanei
    cleanup_temp_files()

def cleanup_temp_files():
    """Rimuovi file temporanei creati durante i test"""
    temp_patterns = ["test_*.tmp", "*.test", "temp_*"]
    
    for pattern in temp_patterns:
        import glob
        for filepath in glob.glob(pattern):
            try:
                os.remove(filepath)
                print(f"🧹 Removed temp file: {filepath}")
            except Exception as e:
                print(f"⚠️ Warning: Could not remove temp file {filepath}: {e}")

# ===== TEST DATA GENERATORS =====

@pytest.fixture
def sample_approval_data():
    """Dati di esempio per test approvazioni"""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "title": f"Sample Approval {unique_id}",
        "description": "This is a sample approval request for testing",
        "approval_type": "all",
        "recipients": [
            {
                "recipient_email": f"approver1_{unique_id}@test.com",
                "recipient_name": "First Approver"
            },
            {
                "recipient_email": f"approver2_{unique_id}@test.com",
                "recipient_name": "Second Approver"
            }
        ],
        "requester_comments": "Please review this as soon as possible"
    }

@pytest.fixture
def sample_document_data():
    """Dati di esempio per test documenti"""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "filename": f"sample_doc_{unique_id}.pdf",
        "original_filename": f"Sample Document {unique_id}.pdf",
        "content_type": "application/pdf",
        "size": random.randint(1000, 10000),
        "file_hash": f"samplehash_{unique_id}"
    }
