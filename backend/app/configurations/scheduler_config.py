# app/config/scheduler_config.py
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import time

class SchedulerTaskConfig(BaseModel):
    enabled: bool = True
    interval_type: str = Field(..., description="minutes, hours, daily, weekly")
    interval_value: Optional[int] = None
    time_at: Optional[str] = None
    description: Optional[str] = None

class SchedulerConfig(BaseModel):
    enabled: bool = True
    max_workers: int = 3
    task_timeout_minutes: int = 10
    reminder_days_before_expiry: int = 2
    reminder_min_interval_hours: int = 12
    expired_tokens_cleanup_days: int = 7
    audit_logs_retention_days: int = 60
    audit_cleanup_batch_size: int = 500
    weekly_stats_day: int = 1
    weekly_stats_time: str = "08:30"
    
    tasks: Dict[str, SchedulerTaskConfig] = {}
    
    scheduler_notifications: Dict[str, Any] = {
        "enabled": False,
        "admin_emails": [],
        "notify_on_errors": True,
        "notify_on_stats": False,
        "error_threshold": 2
    }

def load_scheduler_config(config_file: Optional[Path] = None) -> SchedulerConfig:
    """Carica configurazione scheduler da file YAML"""
    
    if config_file and config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
            
            # Parse tasks
            tasks = {}
            if 'tasks' in yaml_data:
                for task_name, task_data in yaml_data['tasks'].items():
                    tasks[task_name] = SchedulerTaskConfig(**task_data)
            
            yaml_data['tasks'] = tasks
            
            return SchedulerConfig(**yaml_data)
            
        except Exception as e:
            print(f"⚠️ Error loading scheduler config from {config_file}: {e}")
            print("Using default configuration")
    
    # Default configuration
    default_tasks = {
        "approval_reminders": SchedulerTaskConfig(
            enabled=True,
            interval_type="hours",
            interval_value=2,
            description="Reminder per approvazioni in scadenza"
        ),
        "expire_tokens": SchedulerTaskConfig(
            enabled=True,
            interval_type="daily",
            time_at="01:30",
            description="Pulizia token scaduti"
        ),
        "expire_overdue": SchedulerTaskConfig(
            enabled=True,
            interval_type="minutes",
            interval_value=20,
            description="Controllo approvazioni scadute"
        ),
        "completion_notifications": SchedulerTaskConfig(
            enabled=True,
            interval_type="minutes",
            interval_value=10,
            description="Notifiche completamento ritardate"
        ),
        "weekly_statistics": SchedulerTaskConfig(
            enabled=True,
            interval_type="weekly",
            time_at="08:30",
            description="Report statistiche settimanali"
        ),
        "audit_cleanup": SchedulerTaskConfig(
            enabled=True,
            interval_type="daily",
            time_at="02:30",
            description="Pulizia audit logs vecchi"
        )
    }
    
    return SchedulerConfig(tasks=default_tasks)
