"""Authentication dependencies and utilities."""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

# Конфигурация
NEXUS_PASSWORD = os.getenv("NEXUS_PASSWORD", "")
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_hex(32))
SESSION_EXPIRE_HOURS = int(os.getenv("SESSION_EXPIRE_HOURS", "24"))

# In-memory сессии (для продакшена использовать Redis)
active_sessions: dict = {}


class User(BaseModel):
    """Модель пользователя."""
    username: str = "admin"
    is_authenticated: bool = False


class SessionData(BaseModel):
    """Данные сессии."""
    session_id: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None


def verify_password(password: str) -> bool:
    """Проверка пароля."""
    if not NEXUS_PASSWORD:
        # Если пароль не задан - доступ разрешён (только для разработки!)
        return True
    return secrets.compare_digest(password, NEXUS_PASSWORD)


def create_session(ip_address: str = None) -> str:
    """Создать новую сессию."""
    session_id = secrets.token_urlsafe(32)
    now = datetime.now()
    
    active_sessions[session_id] = SessionData(
        session_id=session_id,
        created_at=now,
        expires_at=now + timedelta(hours=SESSION_EXPIRE_HOURS),
        ip_address=ip_address,
    )
    
    return session_id


def get_session(session_id: str) -> Optional[SessionData]:
    """Получить сессию по ID."""
    session = active_sessions.get(session_id)
    
    if not session:
        return None
    
    # Проверяем истечение
    if session.expires_at < datetime.now():
        del active_sessions[session_id]
        return None
    
    return session


def delete_session(session_id: str):
    """Удалить сессию."""
    if session_id in active_sessions:
        del active_sessions[session_id]


def clean_expired_sessions():
    """Очистить истёкшие сессии."""
    now = datetime.now()
    expired = [
        sid for sid, sess in active_sessions.items()
        if sess.expires_at < now
    ]
    for sid in expired:
        del active_sessions[sid]


async def get_current_user(request: Request) -> User:
    """
    Получить текущего пользователя из сессии.
    
    Проверяет:
    1. Cookie session_id
    2. Валидность сессии
    3. IP адрес (опционально)
    """
    # Получаем session_id из cookie
    session_id = request.cookies.get("session_id")
    
    # Если пароль не задан - доступ разрешён
    if not NEXUS_PASSWORD:
        return User(username="admin", is_authenticated=True)
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован",
        )
    
    session = get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия истекла или недействительна",
        )
    
    return User(username="admin", is_authenticated=True)


async def get_current_user_optional(request: Request) -> User:
    """Получить пользователя (опционально, без ошибки)."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return User(username="", is_authenticated=False)


# Зависимости для использования в роутах
RequireAuth = Depends(get_current_user)
OptionalAuth = Depends(get_current_user_optional)
