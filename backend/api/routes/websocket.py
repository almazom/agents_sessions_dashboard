"""WebSocket route for real-time session updates."""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel

from backend.api.scanner import session_store, session_scanner


router = APIRouter(tags=["WebSocket"])


class WSMessage(BaseModel):
    """WebSocket message format."""
    type: str  # "session_update" | "metrics_update" | "ping" | "pong"
    data: Optional[Dict[str, Any]] = None
    timestamp: str = ""
    
    def __init__(self, **data):
        if "timestamp" not in data:
            data["timestamp"] = datetime.now().isoformat()
        super().__init__(**data)


@dataclass
class ConnectionManager:
    """Manage WebSocket connections."""
    
    active_connections: List[WebSocket] = field(default_factory=list)
    
    async def connect(self, websocket: WebSocket):
        """Accept new connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"🔌 WebSocket подключён. Всего: {len(self.active_connections)}")
        
        # Отправляем приветствие
        await self.send_personal(websocket, WSMessage(
            type="connected",
            data={"message": "Подключено к Agent Nexus", "clients": len(self.active_connections)}
        ))
    
    def disconnect(self, websocket: WebSocket):
        """Remove connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"🔌 WebSocket отключён. Осталось: {len(self.active_connections)}")
    
    async def send_personal(self, websocket: WebSocket, message: WSMessage):
        """Send message to specific client."""
        try:
            await websocket.send_text(message.model_dump_json())
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
    
    async def broadcast(self, message: WSMessage):
        """Broadcast to all connected clients."""
        if not self.active_connections:
            return
            
        message_json = message.model_dump_json()
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception:
                disconnected.append(connection)
        
        # Удаляем отключённые
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_session_update(self, session_data: dict):
        """Broadcast session update to all clients."""
        await self.broadcast(WSMessage(
            type="session_update",
            data=session_data
        ))
    
    async def broadcast_metrics(self, metrics: dict):
        """Broadcast metrics update to all clients."""
        await self.broadcast(WSMessage(
            type="metrics_update",
            data=metrics
        ))


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    🔌 WebSocket endpoint для real-time обновлений
    
    Протокол сообщений:
    
    Сервер → Клиент:
    - {"type": "connected", "data": {...}}
    - {"type": "session_update", "data": {...}}
    - {"type": "metrics_update", "data": {...}}
    - {"type": "pong", "timestamp": "..."}
    
    Клиент → Сервер:
    - {"type": "ping"} → pong
    - {"type": "subscribe", "data": {"session_id": "..."}} 
    - {"type": "rescan"}
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Получаем сообщение
            data = await websocket.receive_text()
            
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "")
                
                # Ping-Pong
                if msg_type == "ping":
                    await manager.send_personal(websocket, WSMessage(type="pong"))
                
                # Запрос на пересканирование
                elif msg_type == "rescan":
                    session_store.sessions.clear()
                    count = session_scanner.scan_all()
                    await manager.send_personal(websocket, WSMessage(
                        type="rescan_complete",
                        data={"sessions_found": count}
                    ))
                    # Транслируем новые метрики
                    await manager.broadcast_metrics(session_store.metrics())
                
                # Подписка на сессию
                elif msg_type == "subscribe":
                    session_id = msg.get("data", {}).get("session_id")
                    if session_id:
                        session = session_store.get(session_id)
                        if session:
                            await manager.send_personal(websocket, WSMessage(
                                type="session_update",
                                data=session
                            ))
                        else:
                            await manager.send_personal(websocket, WSMessage(
                                type="error",
                                data={"message": f"Сессия {session_id} не найдена"}
                            ))
                
                # Неизвестный тип
                else:
                    await manager.send_personal(websocket, WSMessage(
                        type="error",
                        data={"message": f"Неизвестный тип: {msg_type}"}
                    ))
                    
            except json.JSONDecodeError:
                await manager.send_personal(websocket, WSMessage(
                    type="error",
                    data={"message": "Неверный JSON"}
                ))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)


# Функция для внешнего использования (транслировать обновление сессии)
async def notify_session_update(session_data: dict):
    """Call this when a session is updated."""
    await manager.broadcast_session_update(session_data)


async def notify_metrics_update(metrics: dict):
    """Call this when metrics change."""
    await manager.broadcast_metrics(metrics)
