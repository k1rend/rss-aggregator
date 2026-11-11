# RSS Aggregator — server

Express + SQLite + Redis сервер который парсит RSS ленты из конфига, авторизирует пользователей и хранит per-user историю просмотра в Redis.

## Setup

```bash
npm install
cp .env.example .env
docker compose up -d redis  # или: docker run -d --name rss-redis -p 6379:6379 redis:latest
npm start
```

Swagger UI: "http://localhost:3000/docs" · raw spec: "http://localhost:3000/openapi.json"

RSS ленты указываются тут `config/feeds.json`:
```json
[
  { "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "title": "BBC World", "type": "world" }
]
```
`type` должен быть одним из: `local`, `country`, `world`. 
Ленты обновляются при запуске, затем каждые `FEED_REFRESH_MS` милисекунд.

## Переменные окружения

| Переменная | Стандартная | За что отвечает |
| --- | --- | --- |
| `PORT` | `3000` | HTTP порт |
| `DB_PATH` | `./data/aggregator.db` | SQLite файл |
| `FEEDS_CONFIG` | `./config/feeds.json` | Конфиг RSS-лент |
| `REDIS_URL` | `redis://127.0.0.1:6379` | Подключение к Redis |
| `FEED_REFRESH_MS` | `600000` | Интервал обновления ленты |
| `HISTORY_TTL_SECONDS` | `0` | Опциональный TTL для истории ZSETs (`0` = keep) |
| `JWT_SECRET` | `dev-secret` | секретный ключ JWT |
| `JWT_EXPIRES` | `7d` | Token lifetime |

## API

Все article/feed/history эндпоинты требуют `Authorization: Bearer <token>`.
