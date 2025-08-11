# testing/tests/test_admin_api_real_auth.py
"""
Test completi per API admin con autenticazione reale
Supporta sia esecuzione standalone che pytest
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup

import pytest
import requests
import time
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import SessionLocal
from app.db.models import User, UserRole
from app.services.auth import create_user, get_user_by_email
from app.db.schemas import UserCreate
from app.utils.security import hash_password
import uuid

# Base URL per test API esterni
BASE_URL = "http://localhost:8000"

class TestAdminAPIRealAuth:
    """Test API admin con autenticazione reale usando TestClient"""
    
    def setup_method(self):
        """Setup per ogni test con utente reale"""
        self.client = TestClient(app)
        
        # Crea utente di test con ID univoco
        self.unique_id = str(uuid.uuid4())[:8]
        self.test_user_email = f"admin_test_{self.unique_id}@example.com"
        self.test_password = "admin_test_pass_123"
        
        # Crea utente nel database
        db = SessionLocal()
        try:
            user_data = UserCreate(
                email=self.test_user_email,
                password=self.test_password,
                display_name=f"Admin Test User {self.unique_id}"
            )
            
            self.test_user = create_user(db, user_data)
            
            # Login per ottenere token reale
            login_data = {
                "username": self.test_user_email,
                "password": self.test_password
            }
            
            login_response = self.client.post("/auth/login", data=login_data)
            assert login_response.status_code == 200
            
            login_result = login_response.json()
            self.token = login_result["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            
        finally:
            db.close()
    
    def teardown_method(self):
        """Cleanup dopo ogni test"""
        # Rimuovi utente di test
        db = SessionLocal()
        try:
            user = get_user_by_email(db, self.test_user_email)
            if user:
                db.delete(user)
                db.commit()
        finally:
            db.close()
    
    def test_real_auth_scheduler_status(self):
        """Test status scheduler con autenticazione reale"""
        response = self.client.get("/admin/scheduler/status", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        
        scheduler_data = data["data"]
        assert "scheduler" in scheduler_data
        assert "configuration" in scheduler_data
        assert "tasks" in scheduler_data
        assert "status_generated_at" in scheduler_data
        
        # Verifica struttura scheduler
        scheduler_info = scheduler_data["scheduler"]
        assert "is_running" in scheduler_info
        assert "config_enabled" in scheduler_info
        assert "max_workers" in scheduler_info
        
        # Verifica tasks
        assert isinstance(scheduler_data["tasks"], list)
        assert len(scheduler_data["tasks"]) > 0
    
    def test_real_auth_scheduler_tasks_list(self):
        """Test lista task scheduler con autenticazione reale"""
        response = self.client.get("/admin/scheduler/tasks", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        
        tasks_data = data["data"]
        assert "tasks" in tasks_data
        assert "configuration" in tasks_data
        
        # Verifica che ci siano i task standard
        tasks = tasks_data["tasks"]
        assert isinstance(tasks, list)
        assert len(tasks) >= 6  # I 6 task standard
        
        task_names = [task["name"] for task in tasks]
        expected_tasks = [
            "approval_reminders",
            "expire_tokens", 
            "expire_overdue",
            "completion_notifications",
            "weekly_statistics",
            "audit_cleanup"
        ]
        
        for expected_task in expected_tasks:
            assert expected_task in task_names
    
    def test_real_auth_system_info(self):
        """Test informazioni sistema con autenticazione reale"""
        response = self.client.get("/admin/system/info", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        
        system_data = data["data"]
        assert "app_name" in system_data
        assert "app_version" in system_data
        assert "app_features" in system_data
        assert "scheduler_enabled" in system_data
        assert "scheduler_running" in system_data
        assert "tasks_configured" in system_data
        assert "tasks_enabled" in system_data
        
        # Verifica valori sensati
        # assert system_data["app_name"] == "DMS Tool"
        assert isinstance(system_data["tasks_configured"], int)
        assert system_data["tasks_configured"] >= 6
    
    def test_real_auth_manual_task_execution(self):
        """Test esecuzione manuale task con autenticazione reale"""
        # Test task sicuro: weekly_statistics
        response = self.client.post(
            "/admin/scheduler/tasks/weekly_statistics/run",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        
        task_result = data["data"]
        assert task_result["success"] == True
        assert task_result["task_name"] == "weekly_statistics"
        assert "result" in task_result
        assert "execution_time_seconds" in task_result
        
        # Verifica struttura risultato
        result = task_result["result"]
        assert "period" in result
        assert "approval_requests" in result
        assert "users" in result
        assert "generated_at" in result
    
    def test_real_auth_scheduler_start_stop(self):
        """Test start/stop scheduler con autenticazione reale"""
        # Prima ottieni lo stato corrente
        status_response = self.client.get("/admin/scheduler/status", headers=self.headers)
        current_status = status_response.json()["data"]["scheduler"]["is_running"]
        
        if current_status:
            # Se running, ferma
            stop_response = self.client.post("/admin/scheduler/stop", headers=self.headers)
            assert stop_response.status_code == 200
            stop_data = stop_response.json()
            assert stop_data["success"] == True
            assert "stopped" in stop_data["message"]
            
            # Poi riavvia
            start_response = self.client.post("/admin/scheduler/start", headers=self.headers)
            assert start_response.status_code == 200
            start_data = start_response.json()
            assert start_data["success"] == True
            assert "started" in start_data["message"]
        else:
            # Se stopped, avvia
            start_response = self.client.post("/admin/scheduler/start", headers=self.headers)
            assert start_response.status_code == 200
            start_data = start_response.json()
            assert start_data["success"] == True
            assert "started" in start_data["message"]
    
    def test_real_auth_invalid_task(self):
        """Test esecuzione task inesistente con autenticazione reale"""
        response = self.client.post(
            "/admin/scheduler/tasks/nonexistent_task/run",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        
        task_result = data["data"]
        # Controlla che sia un errore invece che cercare 'success'
        assert "error" in task_result
        assert "Unknown task" in task_result["error"]
        assert "available_tasks" in task_result
    
    def test_real_auth_unauthorized_access(self):
        """Test accesso non autorizzato"""
        # Test senza header Authorization
        response = self.client.get("/admin/scheduler/status")
        assert response.status_code == 401
        
        # Test con token invalido
        invalid_headers = {"Authorization": "Bearer invalid-token-123"}
        response = self.client.get("/admin/scheduler/status", headers=invalid_headers)
        assert response.status_code == 401
        
        # Test con format Authorization invalido
        malformed_headers = {"Authorization": "InvalidFormat token123"}
        response = self.client.get("/admin/scheduler/status", headers=malformed_headers)
        assert response.status_code == 401


@pytest.mark.admin
@pytest.mark.integration
class TestAdminAPIExternalAuth:
    """Test API admin con server esterno usando requests (se disponibile)"""
    
    def setup_method(self):
        """Setup per test con server esterno"""
        self.unique_id = str(uuid.uuid4())[:8]
        self.test_user_email = f"admin_external_{self.unique_id}@example.com"
        self.test_password = "admin_external_pass_123"
        self.token = None
        self.created_user = False
    
    def teardown_method(self):
        """Cleanup utente di test"""
        if self.created_user:
            # Cleanup tramite database diretto
            db = SessionLocal()
            try:
                user = get_user_by_email(db, self.test_user_email)
                if user:
                    db.delete(user)
                    db.commit()
            finally:
                db.close()
    
    def _register_and_login(self):
        """Helper per registrazione e login"""
        try:
            # Registrazione
            register_data = {
                "email": self.test_user_email,
                "password": self.test_password,
                "display_name": f"Admin External User {self.unique_id}"
            }
            
            register_response = requests.post(
                f"{BASE_URL}/auth/register",
                json=register_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if register_response.status_code == 200:
                self.created_user = True
                
                # Login
                login_data = {
                    "username": self.test_user_email,
                    "password": self.test_password
                }
                
                login_response = requests.post(
                    f"{BASE_URL}/auth/login",
                    data=login_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=5
                )
                
                if login_response.status_code == 200:
                    login_result = login_response.json()
                    self.token = login_result["access_token"]
                    return True
            
            return False
            
        except requests.exceptions.RequestException:
            return False
    
    def test_external_auth_scheduler_status(self):
        """Test status scheduler con server esterno"""
        if not self._register_and_login():
            pytest.skip("Backend non raggiungibile per test API esterni")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(
                f"{BASE_URL}/admin/scheduler/status",
                headers=headers,
                timeout=5
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "data" in data
            
        except requests.exceptions.RequestException:
            pytest.skip("Errore connessione durante test esterno")
    
    def test_external_auth_system_info(self):
        """Test system info con server esterno"""
        if not self._register_and_login():
            pytest.skip("Backend non raggiungibile per test API esterni")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(
                f"{BASE_URL}/admin/system/info",
                headers=headers,
                timeout=5
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "app_name" in data["data"]
            
        except requests.exceptions.RequestException:
            pytest.skip("Errore connessione durante test esterno")


# =============================================================================
# ESECUZIONE STANDALONE
# =============================================================================

def run_admin_real_auth_tests():
    """Test standalone con autenticazione reale"""
    print("🔐 Testing Admin API - Real Authentication")
    print("=" * 60)
    
    # Setup TestClient
    client = TestClient(app)
    unique_id = str(uuid.uuid4())[:8]
    test_email = f"standalone_admin_{unique_id}@example.com"
    test_password = "standalone_admin_pass_123"
    
    db = SessionLocal()
    test_user = None
    
    try:
        print(f"\n🔧 Setup utente test: {test_email}")
        
        # Crea utente
        user_data = UserCreate(
            email=test_email,
            password=test_password,
            display_name=f"Standalone Admin User {unique_id}"
        )
        
        test_user = create_user(db, user_data)
        print("✅ Utente di test creato")
        
        # Login per ottenere token
        print("\n1️⃣ Test Login e Token...")
        login_data = {
            "username": test_email,
            "password": test_password
        }
        
        login_response = client.post("/auth/login", data=login_data)
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print(f"✅ Token ottenuto: {token[:20]}...")
        else:
            print(f"❌ Login fallito: {login_response.status_code}")
            return False
        
        # Test scheduler status
        print("\n2️⃣ Test Scheduler Status...")
        response = client.get("/admin/scheduler/status", headers=headers)
        if response.status_code == 200:
            data = response.json()
            scheduler_info = data["data"]["scheduler"]
            config_info = data["data"]["configuration"]
            print(f"✅ Scheduler Status: running={scheduler_info['is_running']}")
            print(f"✅ Tasks configurati: {config_info['tasks_configured']}")
            print(f"✅ Tasks abilitati: {config_info['tasks_enabled']}")
        else:
            print(f"❌ Scheduler status fallito: {response.status_code}")
            return False
        
        # Test system info
        print("\n3️⃣ Test System Info...")
        response = client.get("/admin/system/info", headers=headers)
        if response.status_code == 200:
            data = response.json()
            system_data = data["data"]
            print(f"✅ App: {system_data['app_name']} v{system_data['app_version']}")
            print(f"✅ Features: {len(system_data.get('app_features', []))}")
        else:
            print(f"❌ System info fallito: {response.status_code}")
        
        # Test lista tasks
        print("\n4️⃣ Test Tasks List...")
        response = client.get("/admin/scheduler/tasks", headers=headers)
        if response.status_code == 200:
            data = response.json()
            tasks = data["data"]["tasks"]
            task_names = [task["name"] for task in tasks]
            print(f"✅ Tasks disponibili: {len(tasks)}")
            print(f"   📋 {', '.join(task_names)}")
        else:
            print(f"❌ Tasks list fallito: {response.status_code}")
        
        # Test esecuzione task manuale
        print("\n5️⃣ Test Manual Task Execution...")
        response = client.post("/admin/scheduler/tasks/weekly_statistics/run", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data["data"]["success"]:
                exec_time = data["data"]["execution_time_seconds"]
                print(f"✅ Task eseguito in {exec_time:.3f}s")
            else:
                error = data["data"].get("error", "Unknown error")
                print(f"⚠️ Task error: {error[:50]}...")
        else:
            print(f"❌ Manual task fallito: {response.status_code}")
        
        # Test accesso non autorizzato
        print("\n6️⃣ Test Unauthorized Access...")
        response = client.get("/admin/scheduler/status")
        if response.status_code == 401:
            print("✅ Accesso non autorizzato bloccato correttamente")
        else:
            print(f"⚠️ Accesso non autorizzato: {response.status_code}")
        
        # Test token invalido
        invalid_headers = {"Authorization": "Bearer invalid-token-123"}
        response = client.get("/admin/scheduler/status", headers=invalid_headers)
        if response.status_code == 401:
            print("✅ Token invalido respinto correttamente")
        else:
            print(f"⚠️ Token invalido: {response.status_code}")
        
    except Exception as e:
        print(f"\n❌ ERRORE NEI TEST: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup garantito
        if test_user:
            try:
                db.delete(test_user)
                db.commit()
                print(f"\n🧹 Cleanup: utente {test_email} rimosso")
            except Exception as e:
                print(f"⚠️ Warning cleanup: {e}")
        
        db.close()
    
    print("\n" + "=" * 60)
    print("✅ TUTTI I TEST ADMIN API REAL AUTH COMPLETATI!")
    return True


if __name__ == "__main__":
    """Esecuzione standalone del test"""
    print("🚀 Esecuzione Test Admin API Real Auth")
    
    if len(sys.argv) > 1 and sys.argv[1] == "standalone":
        # Modalità standalone
        success = run_admin_real_auth_tests()
        sys.exit(0 if success else 1)
    else:
        # Modalità pytest  
        print("💡 Per esecuzione standalone: python testing/tests/test_admin_api_real_auth.py standalone")
        print("💡 Per esecuzione pytest: pytest testing/tests/test_admin_api_real_auth.py -v")
        
        # Esegui comunque test standalone se chiamato direttamente
        run_admin_real_auth_tests()
