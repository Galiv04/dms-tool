from datetime import datetime, timedelta, timezone
from typing import Union, Optional
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from app.configurations import settings
from app.db.base import get_db
from app.db.models import User

# Configurazione logging per debug
logger = logging.getLogger(__name__)

# Configurazione
ph = PasswordHasher()
security = HTTPBearer(auto_error=False)  # ✅ auto_error=False per gestire manualmente gli errori

def hash_password(password: str) -> str:
    """Hash password usando Argon2id"""
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica password contro hash Argon2id"""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """
    Crea JWT token
    
    Args:
        data: Dati da includere nel token (tipicamente {"sub": email})
        expires_delta: Durata personalizzata del token
        
    Returns:
        str: Token JWT codificato
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access_token"  # ✅ Aggiungiamo tipo per sicurezza
    })
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        logger.debug(f"Token created successfully for {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating token: {e}")
        raise

def verify_token(token: str) -> dict:
    """
    Verifica JWT token
    
    Args:
        token: Token JWT da verificare
        
    Returns:
        dict: Payload del token se valido
        
    Raises:
        HTTPException: Se il token è scaduto o non valido
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        # ✅ Verifica tipo token se presente
        if payload.get("type") and payload.get("type") != "access_token":
            logger.warning(f"Invalid token type: {payload.get('type')}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tipo token non valido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"Token verified successfully for {payload.get('sub')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token scaduto",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError as e:
        logger.warning(f"JWT error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error verifying token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Errore di autenticazione",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency per ottenere l'utente corrente dal token JWT
    
    Args:
        credentials: Credenziali Bearer token
        db: Sessione database
        
    Returns:
        User: Utente autenticato
        
    Raises:
        HTTPException: Se il token non è valido o l'utente non esiste
    """
    # ✅ Gestione esplicita dell'assenza di credenziali
    if not credentials:
        logger.warning("No authorization header provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token di autenticazione richiesto",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Verifica e decodifica il token
        payload = verify_token(credentials.credentials)
        email: str = payload.get("sub")
        
        if email is None:
            logger.warning("Token payload missing 'sub' field")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token malformato",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Trova l'utente nel database
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            logger.warning(f"User not found in database: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,  # ✅ 401 invece di 403
                detail="Utente non trovato",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"User authenticated successfully: {user.email} (ID: {user.id})")
        return user
        
    except HTTPException:
        # ✅ Re-raise HTTPException senza modificarle
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Impossibile validare le credenziali",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency per ottenere un utente attivo
    
    Args:
        current_user: Utente corrente
        
    Returns:
        User: Utente attivo
    """
    # ✅ Per ora non controlliamo is_active, ma se hai il campo nel modello decommentalo
    # if hasattr(current_user, 'is_active') and not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Utente inattivo")
    
    return current_user

# ✅ Utility per debug dei token nei test
def debug_token(token: str) -> dict:
    """
    Debug utility per ispezionare un token senza validazione
    
    Args:
        token: Token da ispezionare
        
    Returns:
        dict: Informazioni sul token
    """
    try:
        # Decode senza verifica per debug
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        
        # Verifica con signature
        verified_payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        return {
            "valid": True,
            "unverified_payload": unverified_payload,
            "verified_payload": verified_payload,
            "secret_key_length": len(settings.secret_key),
            "algorithm": settings.algorithm
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "secret_key_length": len(settings.secret_key),
            "algorithm": settings.algorithm
        }
