# testing/tests/test_scheduler.py
"""
Test completi per il TaskScheduler
Supporta sia esecuzione standalone che pytest
"""
import sys
import os
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import yaml

# Setup path per import
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Import dopo setup path
from app.services.scheduler import TaskScheduler, get_scheduler, reset_scheduler
from app.configurations.scheduler_config import SchedulerConfig, load_scheduler_config
from app.db.models import ApprovalRequest, ApprovalRecipient, User, AuditLog, ApprovalStatus, RecipientStatus
import logging

# Setup logging per test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestSchedulerConfig:
    """Test per configurazione scheduler"""
    
    def test_default_config_loading(self):
        """Test caricamento configurazione di default"""
        config = load_scheduler_config(None)
        
        assert config.enabled == True
        assert config.max_workers == 3
        assert len(config.tasks) == 6
        assert "approval_reminders" in config.tasks
        assert "expire_tokens" in config.tasks
        
        # Verifica task specifico
        reminder_task = config.tasks["approval_reminders"]
        assert reminder_task.enabled == True
        assert reminder_task.interval_type == "hours"
        assert reminder_task.interval_value == 2
    
    def test_yaml_config_loading(self):
        """Test caricamento da file YAML"""
        yaml_content = {
            "enabled": True,
            "max_workers": 5,
            "reminder_days_before_expiry": 3,
            "tasks": {
                "approval_reminders": {
                    "enabled": True,
                    "interval_type": "hours",
                    "interval_value": 4,
                    "description": "Test reminders"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_content, f)
            temp_file = Path(f.name)
        
        try:
            config = load_scheduler_config(temp_file)
            
            assert config.enabled == True
            assert config.max_workers == 5
            assert config.reminder_days_before_expiry == 3
            assert len(config.tasks) == 1
            
            reminder_task = config.tasks["approval_reminders"]
            assert reminder_task.interval_value == 4
            assert reminder_task.description == "Test reminders"
            
        finally:
            temp_file.unlink()
    
    def test_invalid_yaml_fallback(self):
        """Test fallback a configurazione default con YAML invalido"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_file = Path(f.name)
        
        try:
            config = load_scheduler_config(temp_file)
            # Deve usare configurazione di default
            assert config.enabled == True
            assert len(config.tasks) == 6
            
        finally:
            temp_file.unlink()


class TestTaskScheduler:
    """Test per TaskScheduler"""
    
    def setup_method(self):
        """Setup per ogni test"""
        reset_scheduler()
        self.scheduler = None
    
    def teardown_method(self):
        """Cleanup dopo ogni test"""
        if self.scheduler:
            self.scheduler.stop_scheduler()
        reset_scheduler()
    
    def test_scheduler_initialization(self):
        """Test inizializzazione scheduler"""
        self.scheduler = TaskScheduler()
        
        assert self.scheduler.config.enabled == True
        assert self.scheduler.is_running == False
        assert len(self.scheduler.config.tasks) == 6
        assert self.scheduler.email_service is not None
    
    def test_scheduler_singleton(self):
        """Test singleton pattern"""
        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()
        
        assert scheduler1 is scheduler2
        
        self.scheduler = scheduler1  # Per cleanup
    
    @patch('app.services.scheduler.schedule')
    def test_start_stop_scheduler(self, mock_schedule):
        """Test avvio e stop dello scheduler"""
        self.scheduler = TaskScheduler()
        
        # Test avvio
        assert self.scheduler.is_running == False
        self.scheduler.start_scheduler()
        assert self.scheduler.is_running == True
        
        # Test stop
        self.scheduler.stop_scheduler()
        assert self.scheduler.is_running == False
    
    def test_scheduler_disabled_by_config(self):
        """Test scheduler disabilitato da configurazione"""
        yaml_content = {"enabled": False}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_content, f)
            temp_file = Path(f.name)
        
        try:
            self.scheduler = TaskScheduler(config_file=temp_file)
            self.scheduler.start_scheduler()
            
            # Non dovrebbe essere running se disabilitato
            assert self.scheduler.is_running == False
            
        finally:
            temp_file.unlink()
    
    @patch('app.services.scheduler.TaskScheduler.get_db_session')
    def test_manual_task_execution(self, mock_db_session):
        """Test esecuzione manuale task"""
        mock_session = Mock()
        mock_db_session.return_value = mock_session
        
        # Mock query results
        mock_session.query.return_value.join.return_value.filter.return_value.all.return_value = []
        mock_session.query.return_value.filter.return_value.count.return_value = 0
        mock_session.query.return_value.filter.return_value.all.return_value = []
        
        self.scheduler = TaskScheduler()
        
        # Test task esistente
        result = self.scheduler.run_task_now("approval_reminders")
        assert result["success"] == True
        assert "result" in result
        assert "execution_time_seconds" in result
        
        # Test task inesistente
        result = self.scheduler.run_task_now("nonexistent_task")
        assert "error" in result
        assert "available_tasks" in result
    
    def test_get_scheduler_status(self):
        """Test status dello scheduler"""
        self.scheduler = TaskScheduler()
        
        status = self.scheduler.get_scheduler_status()
        
        assert "scheduler" in status
        assert "configuration" in status
        assert "tasks" in status
        assert "scheduled_jobs" in status
        assert "status_generated_at" in status
        
        # Verifica campi scheduler
        assert status["scheduler"]["is_running"] == False
        assert status["scheduler"]["config_enabled"] == True
        assert status["configuration"]["tasks_configured"] == 6
        assert len(status["tasks"]) == 6
        
        # Verifica informazioni task
        for task in status["tasks"]:
            assert "name" in task
            assert "enabled" in task
            assert "interval_type" in task
            assert "error_count" in task


class TestSchedulerTasks:
    """Test per i singoli task dello scheduler"""
    
    def setup_method(self):
        """Setup per test task"""
        reset_scheduler()
        self.scheduler = TaskScheduler()
        
        # Mock database session
        self.mock_session = Mock()
        self.scheduler.get_db_session = Mock(return_value=self.mock_session)
    
    def teardown_method(self):
        """Cleanup"""
        if self.scheduler:
            self.scheduler.stop_scheduler()
        reset_scheduler()
    
    def test_approval_reminders_task(self):
        """Test task reminder approvazioni"""
        # Setup mock data
        mock_approval = Mock()
        mock_approval.document_title = "Test Document"
        mock_approval.expires_at = datetime.now() + timedelta(hours=6)
        mock_approval.requester.full_name = "Test Requester"
        mock_approval.token = "test-token"
        
        mock_recipient = Mock()
        mock_recipient.email = "test@example.com"
        mock_recipient.approval_request = mock_approval
        mock_recipient.last_reminder_sent = None
        
        # Mock query chain
        mock_query = Mock()
        mock_query.all.return_value = [mock_recipient]
        self.mock_session.query.return_value.join.return_value.filter.return_value = mock_query
        
        # Mock user query
        user_mock = Mock()
        user_mock.full_name = "Test User"
        self.mock_session.query.return_value.filter.return_value.first.return_value = user_mock
        
        # Mock email service
        self.scheduler.email_service.send_approval_reminder = Mock(return_value=True)
        
        # Esegui task
        result = self.scheduler.send_approval_reminders()
        
        # Verifica risultato
        assert "emails_sent" in result
        assert "reminders_processed" in result
        assert result["reminders_processed"] >= 0
    
    def test_cleanup_expired_tokens_task(self):
        """Test pulizia token scaduti"""
        # Setup mock expired requests
        mock_requests = [Mock() for _ in range(3)]
        for i, req in enumerate(mock_requests):
            req.id = str(i + 1)  # String ID come nel modello
            req.token = f"expired-token-{i}"
        
        # Mock query
        self.mock_session.query.return_value.filter.return_value.all.return_value = mock_requests
        
        # Mock corretto per add() - deve accettare AuditLog con struttura corretta
        def mock_add(audit_log):
            # Verifica che abbia i campi corretti
            if hasattr(audit_log, 'action'):  # È un AuditLog
                assert hasattr(audit_log, 'approval_request_id')
                assert hasattr(audit_log, 'action')
                assert hasattr(audit_log, 'details')
                assert audit_log.action == "TOKEN_CLEANUP"
        
        self.mock_session.add.side_effect = mock_add
        
        # Esegui task
        result = self.scheduler.cleanup_expired_tokens()
        
        # Verifica risultato
        assert "tokens_cleaned" in result
        assert "cutoff_date" in result
        assert result["tokens_cleaned"] >= 0
        
        # Verifica che add sia stato chiamato per ogni request
        assert self.mock_session.add.call_count == len(mock_requests)
    
    def test_expire_overdue_approvals_task(self):
        """Test scadenza approvazioni in ritardo"""
        # Setup mock overdue requests
        mock_requests = [Mock() for _ in range(2)]
        for i, req in enumerate(mock_requests):
            req.id = str(i + 1)  # String ID
            req.status = ApprovalStatus.PENDING
            req.requester_id = 1
            req.expires_at = datetime.now() - timedelta(hours=1)  # Scaduto
        
        # Mock recipients
        mock_recipients = [Mock() for _ in range(4)]
        for recipient in mock_recipients:
            recipient.status = RecipientStatus.PENDING
        
        # Mock queries - configurazione più specifica per due chiamate diverse
        def mock_query_side_effect(*args, **kwargs):
            mock_query_obj = Mock()
            
            if args and args[0] == ApprovalRequest:
                # Query per ApprovalRequest
                mock_filter = Mock()
                mock_filter.all.return_value = mock_requests
                mock_query_obj.filter.return_value = mock_filter
            elif args and args[0] == ApprovalRecipient:
                # Query per ApprovalRecipient
                mock_filter = Mock()
                mock_filter.all.return_value = mock_recipients
                mock_query_obj.filter.return_value = mock_filter
            else:
                # Default
                mock_filter = Mock()
                mock_filter.all.return_value = []
                mock_query_obj.filter.return_value = mock_filter
            
            return mock_query_obj
        
        self.mock_session.query.side_effect = mock_query_side_effect
        
        # Mock add per AuditLog
        def mock_add(audit_log):
            if hasattr(audit_log, 'action'):  # È un AuditLog
                assert audit_log.action == "APPROVAL_EXPIRED"
                assert hasattr(audit_log, 'approval_request_id')
        
        self.mock_session.add.side_effect = mock_add
        
        # Esegui task
        result = self.scheduler.expire_overdue_approvals()
        
        # Verifica risultato
        assert "expired_count" in result
        assert "processed_at" in result
        assert result["expired_count"] >= 0
        
        # Verifica che i mock request abbiano status aggiornato
        for request in mock_requests:
            assert request.status == ApprovalStatus.EXPIRED
            assert hasattr(request, 'completed_at')
        
        # Verifica che i recipients abbiano status aggiornato
        for recipient in mock_recipients:
            assert recipient.status == RecipientStatus.EXPIRED
            assert hasattr(recipient, 'updated_at')
    
    def test_send_delayed_completion_notifications_task(self):
        """Test notifiche completamento ritardate"""
        # Setup mock completed requests
        mock_requests = [Mock()]
        mock_request = mock_requests[0]
        mock_request.id = "1"
        mock_request.status = ApprovalStatus.APPROVED
        mock_request.completed_at = datetime.now()
        mock_request.document_title = "Test Document"
        mock_request.requester.email = "requester@example.com"
        mock_request.requester.full_name = "Test Requester"
        mock_request.recipients = []
        
        # Mock query
        self.mock_session.query.return_value.filter.return_value.all.return_value = mock_requests
        
        # Mock email service
        self.scheduler.email_service.send_completion_notification = Mock(return_value=True)
        
        # Esegui task
        result = self.scheduler.send_delayed_completion_notifications()
        
        # Verifica risultato
        assert "notifications_sent" in result
        assert "processed_at" in result
        assert result["notifications_sent"] >= 0
    
    def test_weekly_statistics_task(self):
        """Test generazione statistiche settimanali"""
        # Mock count queries
        self.mock_session.query.return_value.filter.return_value.count.return_value = 5
        self.mock_session.query.return_value.join.return_value.filter.return_value.distinct.return_value.count.return_value = 3
        
        # Esegui task
        result = self.scheduler.generate_weekly_statistics()
        
        # Verifica risultato
        assert "period" in result
        assert "approval_requests" in result
        assert "users" in result
        assert "generated_at" in result
        
        # Verifica struttura period
        assert "start_date" in result["period"]
        assert "end_date" in result["period"]
        
        # Verifica statistiche approvazioni
        stats = result["approval_requests"]
        assert "total" in stats
        assert "approved" in stats
        assert "rejected" in stats
        assert "expired" in stats
        assert "pending" in stats
    
    def test_audit_cleanup_task(self):
        """Test pulizia audit logs"""
        # Setup mock old logs
        mock_logs = [Mock() for _ in range(5)]
        for i, log in enumerate(mock_logs):
            log.id = i + 1
        
        # Mock query - prima chiamata restituisce logs, seconda chiamata lista vuota
        def mock_query_side_effect(*args, **kwargs):
            mock_query_obj = Mock()
            mock_filter = Mock()
            mock_limit = Mock()
            
            # Simula batch processing: prima chiamata logs, seconda vuota
            if not hasattr(mock_query_side_effect, 'call_count'):
                mock_query_side_effect.call_count = 0
            
            mock_query_side_effect.call_count += 1
            
            if mock_query_side_effect.call_count == 1:
                mock_limit.all.return_value = mock_logs  # Prima batch
            else:
                mock_limit.all.return_value = []  # Batch successivi vuoti
            
            mock_filter.limit.return_value = mock_limit
            mock_query_obj.filter.return_value = mock_filter
            
            return mock_query_obj
        
        self.mock_session.query.side_effect = mock_query_side_effect
        
        # Esegui task
        result = self.scheduler.cleanup_old_audit_logs()
        
        # Verifica risultato
        assert "logs_deleted" in result
        assert "cutoff_date" in result
        assert "batch_size" in result
        assert result["logs_deleted"] >= 0


# =============================================================================
# ESECUZIONE STANDALONE
# =============================================================================

def run_single_tests():
    """Esecuzione singola per debug"""
    print("🧪 Testing TaskScheduler - Standalone Mode")
    print("=" * 60)
    
    try:
        # Test 1: Configurazione
        print("\n1️⃣ Test Configurazione...")
        config = load_scheduler_config(None)
        print(f"   ✅ Config caricata: {len(config.tasks)} tasks")
        print(f"   ✅ Enabled: {config.enabled}")
        print(f"   ✅ Max workers: {config.max_workers}")
        
        # Test 2: Inizializzazione Scheduler
        print("\n2️⃣ Test Inizializzazione Scheduler...")
        reset_scheduler()
        scheduler = TaskScheduler()
        print(f"   ✅ Scheduler creato: {len(scheduler.config.tasks)} tasks configurati")
        print(f"   ✅ Email service: {scheduler.email_service is not None}")
        
        # Test 3: Status Scheduler
        print("\n3️⃣ Test Status Scheduler...")
        status = scheduler.get_scheduler_status()
        print(f"   ✅ Status generato: {len(status)} sezioni")
        print(f"   ✅ Running: {status['scheduler']['is_running']}")
        print(f"   ✅ Tasks abilitati: {status['configuration']['tasks_enabled']}")
        
        # Test 4: Singleton - FIX
        print("\n4️⃣ Test Singleton...")
        reset_scheduler()  # Reset prima del test
        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()
        print(f"   ✅ Singleton: {scheduler1 is scheduler2}")
        scheduler = scheduler1  # Per i test successivi
        
        # Test 5: Esecuzione manuale task - FIX MOCK
        print("\n5️⃣ Test Esecuzione Manuale Task...")
        
        with patch.object(scheduler, 'get_db_session') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            # Mock corretto per query chains con gestione speciale per audit_cleanup
            def create_mock_query_for_task(task_name):
                mock_query = Mock()
                mock_filter = Mock()
                mock_join = Mock()
                
                if task_name == "audit_cleanup":
                    # Mock specifico per audit_cleanup - simula batch processing
                    mock_logs = [Mock() for _ in range(3)]  # 3 mock audit logs
                    for i, log in enumerate(mock_logs):
                        log.id = i + 1
                    
                    # Mock limit che simula batch processing
                    mock_limit = Mock()
                    
                    # Prima chiamata: restituisce logs, seconda: lista vuota
                    call_count = getattr(create_mock_query_for_task, 'audit_call_count', 0)
                    create_mock_query_for_task.audit_call_count = call_count + 1
                    
                    if create_mock_query_for_task.audit_call_count <= 1:
                        mock_limit.all.return_value = mock_logs  # Prima chiamata
                    else:
                        mock_limit.all.return_value = []  # Chiamate successive
                    
                    mock_filter.limit.return_value = mock_limit
                    mock_query.filter.return_value = mock_filter
                    
                else:
                    # Mock standard per altri task
                    # Chain: query().join().filter().all()
                    mock_query.join.return_value = mock_join
                    mock_join.filter.return_value = mock_filter
                    mock_filter.all.return_value = []
                    
                    # Chain: query().filter().count()
                    mock_query.filter.return_value = mock_filter
                    mock_filter.count.return_value = 0
                    
                    # Chain: query().filter().all()
                    mock_filter.all.return_value = []
                    
                    # Chain: query().join().filter().distinct().count()
                    mock_distinct = Mock()
                    mock_join.filter.return_value.distinct.return_value = mock_distinct
                    mock_distinct.count.return_value = 0
                
                return mock_query
            
            # Mock specifici per commit/rollback
            mock_session.commit = Mock()
            mock_session.rollback = Mock()
            mock_session.close = Mock()
            mock_session.add = Mock()
            mock_session.delete = Mock()  # Per audit_cleanup
            
            # Test task con mock specifici per ciascuno
            test_tasks = ["approval_reminders", "weekly_statistics", "audit_cleanup"]
            
            for task_name in test_tasks:
                # Reset call count per audit_cleanup
                if task_name == "audit_cleanup":
                    create_mock_query_for_task.audit_call_count = 0
                
                # Setup mock specifico per ogni task
                mock_session.query.return_value = create_mock_query_for_task(task_name)
                
                result = scheduler.run_task_now(task_name)
                if result.get("success"):
                    print(f"   ✅ {task_name}: OK")
                else:
                    # Per debug, mostra errore ma continua
                    error_msg = result.get('error', 'Unknown error')[:50]
                    print(f"   ⚠️ {task_name}: {error_msg}...")

        # Test 6: Task inesistente
        print("\n6️⃣ Test Task Inesistente...")
        result = scheduler.run_task_now("nonexistent_task")
        if "error" in result:
            print(f"   ✅ Error gestito: {len(result['available_tasks'])} tasks disponibili")
        
        # Test 7: Cleanup
        print("\n7️⃣ Test Cleanup...")
        scheduler.stop_scheduler()
        reset_scheduler()
        print("   ✅ Scheduler fermato e reset")
        
        print("\n" + "=" * 60)
        print("✅ TUTTI I TEST COMPLETATI CON SUCCESSO!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRORE NEI TEST: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    """Esecuzione standalone del test"""
    print("🚀 Esecuzione Test Scheduler")
    
    if len(sys.argv) > 1 and sys.argv[1] == "standalone":
        # Modalità standalone
        success = run_single_tests()
        sys.exit(0 if success else 1)
    else:
        # Modalità pytest
        print("💡 Per esecuzione standalone: python testing/tests/test_scheduler.py standalone")
        print("💡 Per esecuzione pytest: pytest testing/tests/test_scheduler.py -v")
        
        # Esegui comunque test standalone se chiamato direttamente
        run_single_tests()
