"""Session API routes."""

from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, Query, HTTPException

from backend.api.scanner import session_store, session_scanner
from backend.parsers.base import SessionStatus

router = APIRouter(prefix="/api", tags=["Sessions"])


@router.get("/sessions")
async def list_sessions(
    status: Optional[str] = Query(None, description="Filter by status: active, completed, error"),
    agent: Optional[str] = Query(None, description="Filter by agent type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    📋 Получить список всех сессий
    
    - **status**: Фильтр по статусу (active, completed, error, paused)
    - **agent**: Фильтр по типу агента (codex, kimi, gemini, qwen, claude, pi)
    - **limit**: Максимальное количество результатов
    - **offset**: Смещение для пагинации
    """
    # Сканируем сессии если магазин пуст
    if session_store.count() == 0:
        print("📂 Сканирование сессий...")
        session_scanner.scan_all()
    
    sessions = session_store.get_all()
    
    # Фильтрация
    if status:
        sessions = [s for s in sessions if s.get("status") == status]
    
    if agent:
        sessions = [s for s in sessions if s.get("agent_type") == agent]
    
    # Сортировка по времени (новые первыми)
    sessions.sort(key=lambda x: x.get("timestamp_start", ""), reverse=True)
    
    # Пагинация
    total = len(sessions)
    sessions = sessions[offset:offset + limit]
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "sessions": sessions,
    }


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    🔍 Получить детали сессии по ID
    
    - **session_id**: UUID сессии
    """
    # Сканируем если пусто
    if session_store.count() == 0:
        session_scanner.scan_all()
    
    session = session_store.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail=f"Сессия {session_id} не найдена")
    
    return session


@router.get("/metrics")
async def get_metrics():
    """
    📊 Агрегированные метрики по всем сессиям
    
    Возвращает:
    - Общее количество сессий
    - Распределение по агентам
    - Распределение по статусам
    - Общее количество токенов
    """
    # Сканируем если пусто
    if session_store.count() == 0:
        session_scanner.scan_all()
    
    metrics = session_store.metrics()
    
    return {
        "success": True,
        "data": metrics,
    }


@router.post("/sessions/scan")
async def rescan_sessions():
    """
    🔄 Принудительное пересканирование всех директорий агентов
    
    Полезно когда появились новые сессии
    """
    print("📂 Принудительное сканирование...")
    
    # Очищаем старые данные
    session_store.sessions.clear()
    
    # Сканируем заново
    count = session_scanner.scan_all()
    errors = session_scanner.get_errors()
    
    return {
        "success": True,
        "sessions_found": count,
        "errors": errors if errors else None,
        "scanned_at": datetime.now().isoformat(),
    }


@router.get("/agents")
async def list_agents():
    """
    🤖 Получить список поддерживаемых агентов и их статусов
    """
    from ...parsers import PARSER_REGISTRY
    from ..scanner import SessionScanner
    
    agents = []
    
    for agent_type in PARSER_REGISTRY.keys():
        watch_path = Path(SessionScanner.WATCH_PATHS.get(agent_type, "")).expanduser()
        
        agents.append({
            "type": agent_type,
            "watch_path": str(watch_path),
            "path_exists": watch_path.exists(),
            "session_count": len([
                s for s in session_store.get_all() 
                if s.get("agent_type") == agent_type
            ]),
        })
    
    return {
        "total": len(agents),
        "agents": agents,
    }
