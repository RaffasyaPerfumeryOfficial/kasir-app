@echo off
cd /d %~dp0
call .venv\Scripts\activate.bat
start "" /min ngrok.exe http 8000 --domain=unlighted-mahogany-humongous.ngrok-free.dev
:mulai
git pull
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
echo.
echo Server berhenti - restart otomatis dalam 3 detik...
timeout /t 3 >nul
goto mulai
