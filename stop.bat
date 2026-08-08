@echo off
taskkill /f /fi "WINDOWTITLE eq *jalan*" >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im ngrok.exe >nul 2>&1
echo Semua proses kasir dihentikan.
timeout /t 3
