# app/routers/admin.py
"""
Admin endpoints per gestione sistema e scheduler
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import logging

from app.db.models import User
from app.utils.security import get_current_active_user  # ✅ Import corretto da utils/security
from app.services.scheduler import get_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    dependencies=[],
)

def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Verifica che l'utente corrente sia admin"""
    # TODO: Implementare controllo ruolo admin quando aggiungeremo i ruoli
    # Per ora, tutti gli utenti autenticati possono accedere agli admin endpoints
    return current_user

@router.get("/scheduler/status")
async def get_scheduler_status(
    admin_user: User = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Ottiene stato completo dello scheduler"""
    try:
        scheduler = get_scheduler()
        status_data = scheduler.get_scheduler_status()
        return {
            "success": True,
            "data": status_data
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scheduler status: {str(e)}"
        )

@router.post("/scheduler/start")
async def start_scheduler(
    admin_user: User = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Avvia lo scheduler"""
    try:
        scheduler = get_scheduler()
        if scheduler.is_running:
            return {
                "success": True,
                "message": "Scheduler is already running",
                "was_running": True
            }
        
        scheduler.start_scheduler()
        return {
            "success": True,
            "message": "Scheduler started successfully",
            "was_running": False
        }
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start scheduler: {str(e)}"
        )

@router.post("/scheduler/stop")
async def stop_scheduler(
    admin_user: User = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Ferma lo scheduler"""
    try:
        scheduler = get_scheduler()
        if not scheduler.is_running:
            return {
                "success": True,
                "message": "Scheduler is already stopped",
                "was_running": False
            }
        
        scheduler.stop_scheduler()
        return {
            "success": True,
            "message": "Scheduler stopped successfully",
            "was_running": True
        }
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop scheduler: {str(e)}"
        )

@router.post("/scheduler/tasks/{task_name}/run")
async def run_task_manually(
    task_name: str,
    admin_user: User = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Esegue un task manualmente"""
    try:
        scheduler = get_scheduler()
        result = scheduler.run_task_now(task_name)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error running task {task_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run task {task_name}: {str(e)}"
        )

@router.get("/scheduler/tasks")
async def list_scheduler_tasks(
    admin_user: User = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Lista tutti i task disponibili dello scheduler"""
    try:
        scheduler = get_scheduler()
        status_data = scheduler.get_scheduler_status()
        
        return {
            "success": True,
            "data": {
                "tasks": status_data["tasks"],
                "scheduled_jobs": status_data["scheduled_jobs"],
                "configuration": status_data["configuration"]
            }
        }
    except Exception as e:
        logger.error(f"Error listing scheduler tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scheduler tasks: {str(e)}"
        )

@router.get("/system/info")
async def get_system_info(
    admin_user: User = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Informazioni generali del sistema"""
    try:
        from app.configurations import settings
        scheduler = get_scheduler()
        scheduler_status = scheduler.get_scheduler_status()
        
        return {
            "success": True,
            "data": {
                "app_name": settings.app_name,
                "app_version": settings.app_version,
                "app_features": settings.app_features,
                "scheduler_enabled": scheduler_status["scheduler"]["config_enabled"],
                "scheduler_running": scheduler_status["scheduler"]["is_running"],
                "tasks_configured": scheduler_status["configuration"]["tasks_configured"],
                "tasks_enabled": scheduler_status["configuration"]["tasks_enabled"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system info: {str(e)}"
        )
