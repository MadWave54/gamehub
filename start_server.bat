@echo off
rem Start GameHub dev server with the existing database
cd /d "%~dp0backend"
set USE_SQLITE=true
set DEBUG=true
set ALLOWED_HOSTS=localhost,127.0.0.1
set PYTHONUTF8=1
.venv\Scripts\python manage.py runserver 127.0.0.1:8000
pause
