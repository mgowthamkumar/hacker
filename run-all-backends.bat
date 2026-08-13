@echo off
REM AutoHire Silent Background Server Launcher
cd /d "%~dp0"
echo Starting AutoHire Backends silently in background...
cscript //nologo start-autohire-background.vbs
echo AutoHire Backends are now running!
echo - FastAPI Jobs Backend: http://127.0.0.1:5501
echo - FastAPI RAG Analyzer: http://127.0.0.1:5503
echo - Node Express Server: http://127.0.0.1:8800
timeout /t 2 >nul
