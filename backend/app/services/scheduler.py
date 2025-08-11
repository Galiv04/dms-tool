# app/services/scheduler.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import schedule
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.db.base import SessionLocal
from app.db.models import (
    ApprovalRequest, ApprovalRecipient, User, AuditLog,
    ApprovalStatus, RecipientStatus
)
from app.services.email import EmailService
from app.configurations.scheduler_config import SchedulerConfig, load_scheduler_config

logger = logging.getLogger(__name__)

class TaskScheduler:
    """Service per la gestione di task schedulati del sistema di approvazioni"""
    
    def __init__(self, config_file: Path = None):
        # Carica configurazione
        if config_file and config_file.exists():
            self.config = load_scheduler_config(config_file)
        else:
            # Cerca file configurazione in directory standard
            default_config = Path("app/config/scheduler.yaml")
            self.config = load_scheduler_config(
                default_config if default_config.exists() else None
            )
        
        self.email_service = EmailService()
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self.is_running = False
        self.scheduler_thread = None
        self.error_counts = {}
        
        logger.info(f"TaskScheduler initialized with {len(self.config.tasks)} tasks")
    
    def get_db_session(self) -> Session:
        """Crea una nuova sessione database per i task"""
        return SessionLocal()
    
    def start_scheduler(self):
        """Avvia il scheduler in background"""
        if not self.config.enabled:
            logger.info("Scheduler disabled by configuration")
            return
            
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        self.is_running = True
        self._setup_scheduled_tasks()
        
        self.scheduler_thread = threading.Thread(
            target=self._run_scheduler, daemon=True
        )
        self.scheduler_thread.start()
        logger.info("Task Scheduler started successfully")
    
    def stop_scheduler(self):
        """Ferma il scheduler"""
        self.is_running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        self.executor.shutdown(wait=True)
        schedule.clear()
        logger.info("Task Scheduler stopped")
    
    def _setup_scheduled_tasks(self):
        """Configura tutti i task schedulati"""
        task_methods = {
            "approval_reminders": self.send_approval_reminders,
            "expire_tokens": self.cleanup_expired_tokens,
            "expire_overdue": self.expire_overdue_approvals,
            "completion_notifications": self.send_delayed_completion_notifications,
            "weekly_statistics": self.generate_weekly_statistics,
            "audit_cleanup": self.cleanup_old_audit_logs
        }
        
        scheduled_count = 0
        for task_name, task_config in self.config.tasks.items():
            if not task_config.enabled:
                logger.info(f"Skipping disabled task: {task_name}")
                continue
                
            if task_name not in task_methods:
                logger.warning(f"Unknown task method: {task_name}")
                continue
            
            task_method = task_methods[task_name]
            
            try:
                if task_config.interval_type == "minutes":
                    job = schedule.every(task_config.interval_value).minutes.do(
                        self._safe_task_wrapper, task_method, task_name
                    )
                elif task_config.interval_type == "hours":
                    job = schedule.every(task_config.interval_value).hours.do(
                        self._safe_task_wrapper, task_method, task_name
                    )
                elif task_config.interval_type == "daily":
                    job = schedule.every().day.do(
                        self._safe_task_wrapper, task_method, task_name
                    )
                    if task_config.time_at:
                        job.at(task_config.time_at)
                elif task_config.interval_type == "weekly":
                    job = schedule.every().monday.do(
                        self._safe_task_wrapper, task_method, task_name
                    )
                    if task_config.time_at:
                        job.at(task_config.time_at)
                else:
                    logger.error(f"Unknown interval type: {task_config.interval_type}")
                    continue
                
                scheduled_count += 1
                logger.info(f"✅ Scheduled: {task_name} - {task_config.description}")
                
            except Exception as e:
                logger.error(f"Failed to schedule {task_name}: {e}")
        
        logger.info(f"Scheduling completed: {scheduled_count}/{len(self.config.tasks)}")
    
    def _safe_task_wrapper(self, task_func, task_name: str, *args, **kwargs):
        """Wrapper sicuro per task con timeout e error handling"""
        start_time = datetime.now()
        try:
            logger.info(f"Starting task: {task_name}")
            
            future = self.executor.submit(task_func, *args, **kwargs)
            result = future.result(timeout=self.config.task_timeout_minutes * 60)
            
            # Reset contatore errori su successo
            if task_name in self.error_counts:
                del self.error_counts[task_name]
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Completed {task_name} in {duration:.2f}s: {result}")
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.error_counts[task_name] = self.error_counts.get(task_name, 0) + 1
            logger.error(f"❌ Error in {task_name} after {duration:.2f}s: {e}")
    
    def _run_scheduler(self):
        """Loop principale dello scheduler"""
        logger.info("Scheduler loop started")
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check ogni minuto
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
        logger.info("Scheduler loop stopped")
    
    # =============================================================================
    # TASK IMPLEMENTATIONS
    # =============================================================================
    
    def send_approval_reminders(self) -> Dict[str, Any]:
        """Invia reminder per approvazioni in scadenza"""
        db = self.get_db_session()
        try:
            emails_sent = 0
            reminders_processed = 0
            
            cutoff_date = datetime.now() + timedelta(days=self.config.reminder_days_before_expiry)
            min_interval = timedelta(hours=self.config.reminder_min_interval_hours)
            
            recipients_query = db.query(ApprovalRecipient).join(ApprovalRequest).filter(
                and_(
                    ApprovalRequest.status == ApprovalStatus.PENDING,
                    ApprovalRequest.expires_at.isnot(None),
                    ApprovalRequest.expires_at <= cutoff_date,
                    ApprovalRecipient.status == RecipientStatus.PENDING,
                    or_(
                        ApprovalRecipient.last_reminder_sent.is_(None),
                        ApprovalRecipient.last_reminder_sent <= datetime.now() - min_interval
                    )
                )
            )
            
            recipients = recipients_query.all()
            
            for recipient in recipients:
                try:
                    approval_request = recipient.approval_request
                    user = db.query(User).filter(User.email == recipient.email).first()
                    
                    template_data = {
                        "recipient_name": user.full_name if user else recipient.email,
                        "document_title": approval_request.document_title,
                        "requester_name": approval_request.requester.full_name,
                        "expires_at": approval_request.expires_at.strftime("%d/%m/%Y %H:%M"),
                        "approval_url": f"http://localhost:3000/approval/{approval_request.token}",
                        "days_remaining": (approval_request.expires_at - datetime.now()).days
                    }
                    
                    success = self.email_service.send_approval_reminder(
                        to_email=recipient.email,
                        template_data=template_data
                    )
                    
                    if success:
                        recipient.last_reminder_sent = datetime.now()
                        emails_sent += 1
                    
                    reminders_processed += 1
                    
                except Exception as e:
                    logger.error(f"Error sending reminder to {recipient.email}: {e}")
            
            db.commit()
            
            result = {
                "emails_sent": emails_sent,
                "reminders_processed": reminders_processed,
                "cutoff_date": cutoff_date.isoformat()
            }
            
            logger.info(f"Approval reminders: {emails_sent}/{reminders_processed}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in send_approval_reminders: {e}")
            raise
        finally:
            db.close()


    def cleanup_expired_tokens(self) -> Dict[str, Any]:
        """Pulisce token di approvazione scaduti"""
        db = self.get_db_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.expired_tokens_cleanup_days)
            
            expired_requests = db.query(ApprovalRequest).filter(
                and_(
                    ApprovalRequest.expires_at < datetime.now(),
                    ApprovalRequest.created_at < cutoff_date,
                    ApprovalRequest.status.in_([ApprovalStatus.EXPIRED, ApprovalStatus.REJECTED])
                )
            ).all()
            
            tokens_cleaned = 0
            for request in expired_requests:
                # ✅ Usa la struttura corretta del tuo AuditLog
                db.add(AuditLog(
                    approval_request_id=request.id,  # ✅ Campo corretto
                    user_id=None,
                    action="TOKEN_CLEANUP",
                    details=f"Cleaned expired token for approval request {request.id}",
                    metadata_json='{"reason": "expired_token_cleanup", "original_token_prefix": "' + request.token[:8] + '..."}'
                ))
                
                request.token = None
                tokens_cleaned += 1
                
                logger.info(f"Cleaned expired token for request {request.id}")
            
            db.commit()
            
            result = {
                "tokens_cleaned": tokens_cleaned,
                "cutoff_date": cutoff_date.isoformat()
            }
            
            logger.info(f"Token cleanup: {tokens_cleaned} tokens cleaned")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in cleanup_expired_tokens: {e}")
            raise
        finally:
            db.close()
    

    def expire_overdue_approvals(self) -> Dict[str, Any]:
        """Marca come scadute le approvazioni oltre la data limite"""
        db = self.get_db_session()
        try:
            expired_count = 0
            
            overdue_requests = db.query(ApprovalRequest).filter(
                and_(
                    ApprovalRequest.status == ApprovalStatus.PENDING,
                    ApprovalRequest.expires_at < datetime.now()
                )
            ).all()
            
            for request in overdue_requests:
                request.status = ApprovalStatus.EXPIRED
                request.completed_at = datetime.now()
                
                pending_recipients = db.query(ApprovalRecipient).filter(
                    and_(
                        ApprovalRecipient.approval_request_id == request.id,
                        ApprovalRecipient.status == RecipientStatus.PENDING
                    )
                ).all()
                
                for recipient in pending_recipients:
                    recipient.status = RecipientStatus.EXPIRED
                    recipient.updated_at = datetime.now()
                
                # ✅ Usa la struttura corretta del tuo AuditLog
                db.add(AuditLog(
                    approval_request_id=request.id,  # ✅ Campo corretto
                    user_id=request.requester_id,
                    action="APPROVAL_EXPIRED",
                    details=f"Approval request {request.id} expired automatically",
                    metadata_json='{"expired_at": "' + datetime.now().isoformat() + '", "original_expires_at": "' + request.expires_at.isoformat() + '"}'
                ))
                
                expired_count += 1
                logger.info(f"Expired approval request {request.id}")
            
            db.commit()
            
            result = {
                "expired_count": expired_count,
                "processed_at": datetime.now().isoformat()
            }
            
            logger.info(f"Overdue approvals: {expired_count} expired")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in expire_overdue_approvals: {e}")
            raise
        finally:
            db.close()


    def send_delayed_completion_notifications(self) -> Dict[str, Any]:
        """Invia notifiche di completamento ritardate"""
        db = self.get_db_session()
        try:
            notifications_sent = 0
            
            completed_requests = db.query(ApprovalRequest).filter(
                and_(
                    ApprovalRequest.status.in_([ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]),
                    ApprovalRequest.completion_notification_sent.is_(None),
                    ApprovalRequest.completed_at.isnot(None)
                )
            ).all()
            
            for request in completed_requests:
                try:
                    template_data = {
                        "requester_name": request.requester.full_name,
                        "document_title": request.document_title,
                        "final_status": request.status.value,
                        "completed_at": request.completed_at.strftime("%d/%m/%Y %H:%M"),
                        "approval_summary": self._get_approval_summary(request)
                    }
                    
                    success = self.email_service.send_completion_notification(
                        to_email=request.requester.email,
                        template_data=template_data
                    )
                    
                    if success:
                        request.completion_notification_sent = datetime.now()
                        notifications_sent += 1
                        
                except Exception as e:
                    logger.error(f"Error sending completion notification for request {request.id}: {e}")
            
            db.commit()
            
            result = {
                "notifications_sent": notifications_sent,
                "processed_at": datetime.now().isoformat()
            }
            
            logger.info(f"Completion notifications: {notifications_sent} sent")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in send_delayed_completion_notifications: {e}")
            raise
        finally:
            db.close()
    
    def generate_weekly_statistics(self) -> Dict[str, Any]:
        """Genera e invia statistiche settimanali"""
        db = self.get_db_session()
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            total_requests = db.query(ApprovalRequest).filter(
                ApprovalRequest.created_at.between(start_date, end_date)
            ).count()
            
            approved_count = db.query(ApprovalRequest).filter(
                and_(
                    ApprovalRequest.created_at.between(start_date, end_date),
                    ApprovalRequest.status == ApprovalStatus.APPROVED
                )
            ).count()
            
            rejected_count = db.query(ApprovalRequest).filter(
                and_(
                    ApprovalRequest.created_at.between(start_date, end_date),
                    ApprovalRequest.status == ApprovalStatus.REJECTED
                )
            ).count()
            
            expired_count = db.query(ApprovalRequest).filter(
                and_(
                    ApprovalRequest.created_at.between(start_date, end_date),
                    ApprovalRequest.status == ApprovalStatus.EXPIRED
                )
            ).count()
            
            pending_count = db.query(ApprovalRequest).filter(
                and_(
                    ApprovalRequest.created_at.between(start_date, end_date),
                    ApprovalRequest.status == ApprovalStatus.PENDING
                )
            ).count()
            
            active_users = db.query(User).join(ApprovalRequest).filter(
                ApprovalRequest.created_at.between(start_date, end_date)
            ).distinct().count()
            
            stats = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "approval_requests": {
                    "total": total_requests,
                    "approved": approved_count,
                    "rejected": rejected_count,
                    "expired": expired_count,
                    "pending": pending_count
                },
                "users": {
                    "active_requesters": active_users
                },
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Weekly stats: {total_requests} requests, {active_users} active users")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error in generate_weekly_statistics: {e}")
            raise
        finally:
            db.close()
    
    def cleanup_old_audit_logs(self) -> Dict[str, Any]:
        """Pulisce audit logs vecchi"""
        db = self.get_db_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.audit_logs_retention_days)
            batch_size = self.config.audit_cleanup_batch_size
            
            total_deleted = 0
            
            while True:
                old_logs = db.query(AuditLog).filter(
                    AuditLog.created_at < cutoff_date
                ).limit(batch_size).all()
                
                if not old_logs:
                    break
                
                batch_count = len(old_logs)
                for log in old_logs:
                    db.delete(log)
                
                db.commit()
                total_deleted += batch_count
                
                logger.info(f"Deleted {batch_count} audit logs (total: {total_deleted})")
                
                if batch_count == batch_size:
                    time.sleep(1)
                else:
                    break
            
            result = {
                "logs_deleted": total_deleted,
                "cutoff_date": cutoff_date.isoformat(),
                "batch_size": batch_size
            }
            
            logger.info(f"Audit cleanup: {total_deleted} logs deleted")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in cleanup_old_audit_logs: {e}")
            raise
        finally:
            db.close()
    
    def _get_approval_summary(self, request: ApprovalRequest) -> Dict[str, Any]:
        """Crea sommario dello stato approvazione"""
        recipients = request.recipients
        
        return {
            "total_recipients": len(recipients),
            "approved": len([r for r in recipients if r.status == RecipientStatus.APPROVED]),
            "rejected": len([r for r in recipients if r.status == RecipientStatus.REJECTED]),
            "pending": len([r for r in recipients if r.status == RecipientStatus.PENDING]),
            "expired": len([r for r in recipients if r.status == RecipientStatus.EXPIRED])
        }
    
    # =============================================================================
    # MANUAL TASK EXECUTION & STATUS
    # =============================================================================
    
    def run_task_now(self, task_name: str) -> Dict[str, Any]:
        """Esegue task manualmente per testing"""
        task_methods = {
            "approval_reminders": self.send_approval_reminders,
            "expire_tokens": self.cleanup_expired_tokens,
            "expire_overdue": self.expire_overdue_approvals,
            "completion_notifications": self.send_delayed_completion_notifications,
            "weekly_statistics": self.generate_weekly_statistics,
            "audit_cleanup": self.cleanup_old_audit_logs
        }
        
        if task_name not in task_methods:
            return {
                "error": f"Unknown task: {task_name}",
                "available_tasks": list(task_methods.keys())
            }
        
        try:
            logger.info(f"Running manual task: {task_name}")
            start_time = datetime.now()
            
            result = task_methods[task_name]()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "task_name": task_name,
                "result": result,
                "execution_time_seconds": duration,
                "executed_at": start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in manual task {task_name}: {e}")
            return {
                "success": False,
                "task_name": task_name,
                "error": str(e),
                "executed_at": datetime.now().isoformat()
            }
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Stato completo dello scheduler"""
        return {
            "scheduler": {
                "is_running": self.is_running,
                "config_enabled": self.config.enabled,
                "thread_alive": self.scheduler_thread.is_alive() if self.scheduler_thread else False,
                "pending_jobs": len(schedule.jobs),
                "max_workers": self.config.max_workers,
                "error_counts": self.error_counts
            },
            "configuration": {
                "tasks_configured": len(self.config.tasks),
                "tasks_enabled": len([t for t in self.config.tasks.values() if t.enabled]),
                "reminder_days_before_expiry": self.config.reminder_days_before_expiry,
                "reminder_min_interval_hours": self.config.reminder_min_interval_hours,
                "expired_tokens_cleanup_days": self.config.expired_tokens_cleanup_days,
                "audit_logs_retention_days": self.config.audit_logs_retention_days
            },
            "tasks": [
                {
                    "name": task_name,
                    "enabled": task_config.enabled,
                    "interval_type": task_config.interval_type,
                    "interval_value": task_config.interval_value,
                    "time_at": task_config.time_at,
                    "description": task_config.description,
                    "error_count": self.error_counts.get(task_name, 0)
                }
                for task_name, task_config in self.config.tasks.items()
            ],
            "scheduled_jobs": [
                {
                    "job": str(job.job_func.__name__ if hasattr(job.job_func, '__name__') else job.job_func),
                    "next_run": job.next_run.isoformat() if job.next_run else None,
                    "interval": str(job.interval),
                    "unit": job.unit
                } for job in schedule.jobs
            ] if self.is_running else [],
            "status_generated_at": datetime.now().isoformat()
        }

# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# app/services/scheduler.py - Aggiorna la parte singleton alla fine del file

_scheduler_instance = None

def get_scheduler() -> TaskScheduler:
    """Ottiene istanza singleton dello scheduler"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = TaskScheduler()
    return _scheduler_instance

def reset_scheduler():
    """Reset dello scheduler (per testing)"""
    global _scheduler_instance
    if _scheduler_instance:
        _scheduler_instance.stop_scheduler()
    _scheduler_instance = None  # ← Importante: mettere a None dopo lo stop
