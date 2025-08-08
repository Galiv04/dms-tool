import sys
import os
import pytest

# Setup automatico del path per pytest
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Resto delle fixtures...
@pytest.fixture(scope="session")
def db_session():
    from app.db.base import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def fresh_db_session():
    from app.db.base import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def test_user_data():
    return {
        "email": "pytest_user@test.com",
        "password": "testpass123",
        "display_name": "Pytest Test User"
    }

def pytest_configure(config):
    config.addinivalue_line("markers", "db: marks tests as database tests")
    config.addinivalue_line("markers", "auth: marks tests as authentication tests")
    config.addinivalue_line("markers", "management: marks tests as user management tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
