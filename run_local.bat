@echo off
rem GameHub local run on Windows (SQLite, Django dev server)
chcp 65001 >nul
setlocal
cd /d "%~dp0backend"

where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")

echo === 1. Virtual environment and dependencies
if not exist .venv %PY% -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -q --disable-pip-version-check -r requirements-local.txt

set USE_SQLITE=true
set DEBUG=true
set ALLOWED_HOSTS=localhost,127.0.0.1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo === 2. Migrations and game catalog
if exist db.sqlite3 del db.sqlite3
python manage.py migrate -v 0
python manage.py load_data --path ..\data\games.json

echo === 3. Automated tests
python manage.py test api -v 2

echo === 4. Starting server http://127.0.0.1:8000/api/
start "GameHub server" cmd /k "cd /d %~dp0backend && set USE_SQLITE=true&& set DEBUG=true&& .venv\Scripts\python manage.py runserver 127.0.0.1:8000"
timeout /t 6 /nobreak >nul

echo === 5. Demo data via API
python ..\demo\seed.py http://127.0.0.1:8000
set DJANGO_SUPERUSER_PASSWORD=Admin-Pixel-26
python manage.py createsuperuser --noinput --email admin@gamehub.ru --username admin --first_name Admin --last_name GameHub

echo === 6. curl requests
python ..\demo\curl_demo.py http://127.0.0.1:8000

echo.
echo Done. Server keeps running in the "GameHub server" window.
pause
