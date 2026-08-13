@echo off
REM Launch AutoHire Backends silently in the background and open chatbot.html in the browser.
cd /d "%~dp0"

REM Trigger silent background server launch via VBScript
cscript //nologo start-autohire-background.vbs

REM Wait 2 seconds for background servers to initialize
timeout /t 2 /nobreak >nul

REM Open chatbot.html in default web browser
start "" "%~dp0chatbot.html"
