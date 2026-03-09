'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { api } from '@/lib/api';

interface WSMessage {
  type: string;
  data?: any;
  timestamp: string;
}

export function useWebSocket(onMessage?: (msg: WSMessage) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = api.getWebSocketUrl();
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('🔌 WebSocket подключён');
      setConnected(true);
      setError(null);
    };

    ws.onclose = () => {
      console.log('🔌 WebSocket отключён');
      setConnected(false);
      
      // Переподключение через 5 сек
      setTimeout(connect, 5000);
    };

    ws.onerror = (err) => {
      console.error('❌ WebSocket ошибка:', err);
      setError('Ошибка подключения');
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        onMessage?.(msg);
      } catch (e) {
        console.error('Ошибка парсинга сообщения:', e);
      }
    };

    wsRef.current = ws;
  }, [onMessage]);

  const send = useCallback((msg: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const ping = useCallback(() => {
    send({ type: 'ping' });
  }, [send]);

  useEffect(() => {
    connect();
    
    // Ping каждые 30 сек
    const interval = setInterval(ping, 30000);
    
    return () => {
      clearInterval(interval);
      wsRef.current?.close();
    };
  }, [connect, ping]);

  return { connected, error, send };
}
