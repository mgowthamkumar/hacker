@echo off
REM AutoHire Server Launcher
cd /d "%~dp0"
echo Starting AutoHire Express & Auth Server...
start "" node server.js
echo AutoHire Backend is now running!
echo - Web & Auth Server: http://127.0.0.1:8800
echo - Sign in page: http://127.0.0.1:8800/sign-in.html
timeout /t 2 >nul

