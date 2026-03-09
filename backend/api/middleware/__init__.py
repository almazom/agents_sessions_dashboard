"""Security middleware - IP whitelist, rate limiting, etc."""

import os
import time
from collections import defaultdict
from datetime import datetime
from typing import Optional, Callable

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

# Конфигурация
IP_WHITELIST = os.getenv("NEXUS_IP_WHITELIST", "")
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds


def parse_ip_whitelist() -> list:
    """Парсит список разрешённых IP из env."""
    if not IP_WHITELIST:
        return []  # Пустой список = все разрешены
    
    ips = []
    for ip in IP_WHITELIST.split(","):
        ip = ip.strip()
        if ip:
            ips.append(ip)
    return ips


WHITELIST = parse_ip_whitelist()


class RateLimiter:
    """Простой rate limiter на основе IP."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = defaultdict(list)  # ip -> [timestamps]
    
    def is_allowed(self, ip: str) -> bool:
        """Проверяет, разрешён ли запрос."""
        now = time.time()
        
        # Удаляем старые запросы
        self.requests[ip] = [
            ts for ts in self.requests[ip]
            if now - ts < self.window
        ]
        
        # Проверяем лимит
        if len(self.requests[ip]) >= self.max_requests:
            return False
        
        # Добавляем текущий запрос
        self.requests[ip].append(now)
        return True
    
    def remaining(self, ip: str) -> int:
        """Оставшиеся запросы."""
        return max(0, self.max_requests - len(self.requests[ip]))


# Глобальный rate limiter
rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware для безопасности:
    - IP whitelist
    - Rate limiting
    - Логирование запросов
    """
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        
        # 1. IP Whitelist проверка
        if WHITELIST and client_ip not in WHITELIST:
            print(f"🚫 IP заблокирован: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещён"
            )
        
        # 2. Rate limiting (кроме health check)
        if not request.url.path.startswith("/health"):
            if not rate_limiter.is_allowed(client_ip):
                print(f"⚠️ Rate limit превышен: {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Слишком много запросов"
                )
        
        # 3. Логирование
        start_time = time.time()
        
        # Выполняем запрос
        response = await call_next(request)
        
        # Логируем
        duration = time.time() - start_time
        if request.url.path.startswith("/api"):
            print(f"📡 {request.method} {request.url.path} [{response.status_code}] {duration*1000:.1f}ms")
        
        # Добавляем заголовки rate limit
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(rate_limiter.remaining(client_ip))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Получает реальный IP клиента."""
        # Проверяем заголовки прокси
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback на direct connection
        if request.client:
            return request.client.host
        
        return "unknown"
