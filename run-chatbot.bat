@echo off
REM Launch the FastAPI backend and then open chatbot.html in the default browser.
cd /d "%~dp0"

REM Start the backend in a hidden PowerShell window if it is not already running.
powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command "if (-not (Get-Process -Name python -ErrorAction SilentlyContinue)) { Start-Process -WindowStyle Hidden -FilePath 'py' -ArgumentList '-m uvicorn backendreal:app --host 0.0.0.0 --port 5501' }"

REM Wait a few seconds for the backend to start.
timeout /t 3 /nobreak >nul

REM Open chatbot.html in the default browser.
start "" "%~dp0chatbot.html"
