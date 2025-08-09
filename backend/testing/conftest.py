import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup automatico del path per pytest
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

@pytest.fixture
def db_session():
    """
    Fixture database con isolamento completo tramite transazioni
    Ogni test ottiene una sessione pulita con rollback garantito
    """
    from app.db.base import SessionLocal, engine
    
    # Crea una connessione dedicata per il test
    connection = engine.connect()
    
    # Inizia una transazione che wrappa tutto il test
    transaction = connection.begin()
    
    # Crea una sessione legata alla transazione
    Session = sessionmaker(bind=connection)
    session = Session()
    
    try:
        yield session
    finally:
        # Chiudi la sessione
        session.close()
        
        # Rollback della transazione (elimina tutti i cambiamenti)
        transaction.rollback()
        
        # Chiudi la connessione
        connection.close()

@pytest.fixture
def db_session_real():
    """
    Fixture database per sessione REALE (senza rollback)
    Usata dal TestClient per persistere utenti per l'autenticazione
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
    return {
        "email": "pytest_user@test.com",
        "password": "testpass123",
        "display_name": "Pytest Test User"
    }

# Configurazione pytest markers
def pytest_configure(config):
    """Configurazione automatica pytest con markers"""
    config.addinivalue_line("markers", "db: marks tests as database tests")
    config.addinivalue_line("markers", "auth: marks tests as authentication tests")
    config.addinivalue_line("markers", "management: marks tests as user management tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
