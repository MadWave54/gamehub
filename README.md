# GameHub — серверное приложение для любителей компьютерных игр

Курсовая работа по дисциплине «Интеграция и управление приложениями на удалённом сервере».
Автор: Карпенко Матвей Геннадьевич, группа 15.27Д-ПИ02/23б. Руководитель: Данилов А. В.

REST API на Django REST Framework, построенный по образцу итогового проекта «Фудграм».
Пользователи публикуют обзоры игр, комментируют их, подписываются на авторов, добавляют
публикации в избранное и ведут список желаемых игр, который можно скачать файлом.

## Стек
Python 3.12, Django 5.1, Django REST Framework 3.17, Djoser (токены), django-filter,
PostgreSQL 16, Gunicorn, Nginx, Docker Compose, GitHub Actions.

## Структура
```
backend/   Django-проект: gamehub (настройки), users, games, api
data/      справочник жанров, платформ и игр (games.json)
infra/     docker-compose.yml, docker-compose.production.yml, nginx.conf
.github/   workflow CI/CD: тесты → сборка образов → деплой
```

## Запуск в контейнерах
```bash
cp .env.example .env        # задать пароли и SECRET_KEY
cd infra
docker compose --project-name gamehub up -d --build
docker compose --project-name gamehub exec backend python manage.py createsuperuser
```
API: http://localhost:8003/api/, админка: http://localhost:8003/admin/.
Порт задаётся `GAMEHUB_PORT` в `.env` (по умолчанию 8003).

Проверенный стенд: PostgreSQL 16, Gunicorn (3 процесса), Nginx.
Проверка внутри контейнера: `docker compose --project-name gamehub exec backend python manage.py test api --noinput` — 5 тестов пройдены.
Коллекция `demo/GameHub_Postman.json`: 18 запросов, 21 проверка без ошибок.
Повторный запуск: `npx newman run demo/GameHub_Postman.json` из корня проекта.
Коллекция автоматически создаёт уникальные учётные записи; токены получает при входе.
В графическом Postman дополнительно проверены создание обзора (201) и изменение чужого обзора (403).
Отчёты текущего прогона находятся в `demo/`. Конфигурация GitHub Actions подготовлена; её выполнение и удалённый деплой не подтверждены.

## Локальный запуск без Docker
```bash
cd backend
pip install -r requirements.txt
export USE_SQLITE=true DEBUG=true
python manage.py migrate
python manage.py load_data --path ../data/games.json
python manage.py runserver
```

## Запуск на Windows одним скриптом
Двойной щелчок по `run_local.bat`: создаст окружение, применит миграции, загрузит справочник,
прогонит тесты, запустит сервер http://127.0.0.1:8000/api/ и наполнит его тестовыми данными.
Вход: matvey@gamehub.ru / Pixel-Quest-77, админка: admin@gamehub.ru / Admin-Pixel-26.

## Тесты
```bash
cd backend && USE_SQLITE=true python manage.py test api
```

## Основные эндпоинты
| Ресурс | Методы |
|---|---|
| /api/users/, /api/users/{id}/, /api/users/me/ | GET, POST |
| /api/users/me/avatar/ | PUT, DELETE |
| /api/auth/token/login/, /api/auth/token/logout/ | POST |
| /api/users/subscriptions/, /api/users/{id}/subscribe/ | GET; POST, DELETE |
| /api/genres/, /api/platforms/ | GET |
| /api/games/, /api/games/{id}/wishlist/, /api/games/download_wishlist/ | GET; POST, DELETE; GET |
| /api/posts/, /api/posts/{id}/ | GET, POST; GET, PUT, PATCH, DELETE |
| /api/posts/feed/, /api/posts/{id}/favorite/, /api/posts/{id}/get-link/ | GET; POST, DELETE; GET |
| /api/posts/{id}/comments/ | GET, POST (+ PUT, PATCH, DELETE по id) |
| /s/{code}/ | GET (редирект по короткой ссылке) |
