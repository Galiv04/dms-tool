from datetime import timedelta
from sqlalchemy.orm import Session
from app.db.models import User
from app.db.schemas import UserCreate, UserResponse
from app.utils.security import hash_password, verify_password, create_access_token
from app.configurations import settings


def create_user(db: Session, user_create: UserCreate) -> User:
    """Crea un nuovo utente con password hashata"""
    hashed_password = hash_password(user_create.password)
    
    db_user = User(
        email=user_create.email,
        password_hash=hashed_password,
        display_name=user_create.display_name
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def get_user_by_email(db: Session, email: str) -> User:
    """Trova utente per email"""
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Autentica utente con email e password"""
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


def create_user_token(user: User) -> str:
    """Crea token JWT per l'utente"""
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}, 
        expires_delta=access_token_expires
    )
    return access_token
