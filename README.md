# Agent Nexus 🤖

**Real-time AI Coding Agent Monitoring Dashboard**

Мониторинг всех AI агентов в одном месте: Codex, Kimi, Gemini, Qwen, Claude, Pi

## 🚀 Быстрый старт

```bash
# Backend
cd backend
pip install -r requirements.txt
python3 -m uvicorn api.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Открыть: http://localhost:3000

## 📊 Возможности

- **6 агентов**: Codex, Kimi, Gemini, Qwen, Claude, Pi
- **Real-time**: WebSocket обновления
- **Метрики**: Токены, статусы, распределение
- **Поиск**: FTS5 полнотекстовый поиск
- **Безопасность**: 
  - Парольная аутентификация
  - IP whitelist
  - Rate limiting
  - Secret masking (28 паттернов)
- **Handoff**: Передача задач между агентами

## 📁 Структура

```
sessions_landing/
├── backend/
│   ├── api/           # FastAPI endpoints
│   │   ├── main.py    # App + middleware
│   │   ├── routes/    # Sessions, Auth, WebSocket
│   │   ├── database.py # SQLite + FTS5
│   │   └── handoff.py  # Agent handoff
│   ├── parsers/       # 6 agent parsers
│   ├── summarizer/    # Compression + masking
│   └── watcher/       # File watcher
├── frontend/          # Next.js 14
│   ├── app/           # Pages
│   ├── components/    # UI components
│   ├── hooks/         # useWebSocket
│   └── lib/           # API client
└── deploy/            # Systemd + Nginx
```

## 🔧 Конфигурация

```bash
# Environment variables
NEXUS_PASSWORD=secret          # Пароль для входа
NEXUS_IP_WHITELIST=10.0.0.0/8  # Разрешённые IP
RATE_LIMIT_REQUESTS=100        # Лимит запросов
```

## 📡 API

| Endpoint | Description |
|----------|-------------|
| `GET /api/sessions` | Список сессий |
| `GET /api/sessions/{id}` | Детали сессии |
| `GET /api/metrics` | Метрики |
| `POST /api/sessions/scan` | Пересканировать |
| `WS /ws` | Real-time обновления |
| `POST /api/auth/login` | Вход |
| `GET /health` | Health check |

## 🎨 Цвета агентов

| Agent | Color |
|-------|-------|
| Codex | 🟢 Зелёный |
| Kimi | 🟠 Оранжевый |
| Gemini | 🔵 Синий |
| Qwen | 🟣 Фиолетовый |
| Claude | 🩷 Розовый |
| Pi | 🩵 Бирюзовый |

## 📦 Deploy

```bash
# Systemd
sudo cp deploy/nexus.service /etc/systemd/system/
sudo systemctl enable --now nexus

# Nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/nexus
sudo ln -s /etc/nginx/sites-available/nexus /etc/nginx/sites-enabled/
sudo nginx -s reload
```

## 📝 License

MIT
