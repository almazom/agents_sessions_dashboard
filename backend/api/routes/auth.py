"""Authentication routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from ..deps import (
    verify_password,
    create_session,
    delete_session,
    get_current_user,
    get_current_user_optional,
    User,
    NEXUS_PASSWORD,
)


router = APIRouter(prefix="/api/auth", tags=["Auth"])
security = HTTPBasic(auto_error=False)


class LoginRequest(BaseModel):
    """Запрос на вход."""
    password: str


class LoginResponse(BaseModel):
    """Ответ на вход."""
    success: bool
    message: str
    expires_at: Optional[str] = None


class UserResponse(BaseModel):
    """Информация о пользователе."""
    username: str
    is_authenticated: bool
    password_required: bool


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    response: Response,
):
    """
    🔐 Вход в систему
    
    Устанавливает httpOnly cookie с session_id
    """
    if not verify_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный пароль",
        )
    
    # Создаём сессию
    client_ip = http_request.client.host if http_request.client else None
    session_id = create_session(ip_address=client_ip)
    
    # Устанавливаем cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,  # Только HTTPS в продакшене
        samesite="strict",
        max_age=60 * 60 * 24,  # 24 часа
    )
    
    return LoginResponse(
        success=True,
        message="Успешный вход",
        expires_at=datetime.now().isoformat(),  # Упрощённо
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
):
    """
    🚪 Выход из системы
    
    Удаляет сессию и очищает cookie
    """
    session_id = request.cookies.get("session_id")
    
    if session_id:
        delete_session(session_id)
    
    response.delete_cookie("session_id")
    
    return {"success": True, "message": "Успешный выход"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user_optional)):
    """
    👤 Информация о текущем пользователе
    
    Возвращает статус авторизации
    """
    return UserResponse(
        username=user.username if user.is_authenticated else "",
        is_authenticated=user.is_authenticated,
        password_required=bool(NEXUS_PASSWORD),
    )


@router.get("/status")
async def auth_status(user: User = Depends(get_current_user_optional)):
    """
    🔍 Статус авторизации (упрощённый)
    
    Полезно для проверки фронтом
    """
    return {
        "authenticated": user.is_authenticated,
        "password_required": bool(NEXUS_PASSWORD),
    }
