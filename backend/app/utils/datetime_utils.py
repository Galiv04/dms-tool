# backend/app/utils/datetime_utils.py
from datetime import datetime, timezone
from typing import Optional

def get_utc_now() -> datetime:
    """Restituisce il datetime corrente in UTC"""
    return datetime.now(timezone.utc)

def ensure_utc(dt: datetime) -> datetime:
    """Assicura che un datetime abbia timezone UTC"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Se è naive, assume che sia già in UTC
        return dt.replace(tzinfo=timezone.utc)
    # Se ha già timezone, convertilo a UTC
    return dt.astimezone(timezone.utc)

# backend/app/utils/datetime_utils.py
def format_datetime_for_api(dt: Optional[datetime]) -> Optional[str]:
    """Formatta datetime per response API in formato ISO con timezone"""
    if dt is None:
        return None
    
    # Assicura che sia in UTC
    utc_dt = ensure_utc(dt)
    # Aggiungi 'Z' per indicare UTC
    return utc_dt.isoformat().replace('+00:00', 'Z')

def parse_datetime_from_api(iso_string: str) -> datetime:
    """Parse datetime da string ISO ricevuta dal frontend"""
    return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
