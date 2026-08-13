Set WshShell = CreateObject("WScript.Shell")
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir

' Start Python FastAPI Job Backend (port 5501) silently in background
WshShell.Run "powershell -NoProfile -ExecutionPolicy Bypass -Command ""if (-not (Get-Process -Name python -ErrorAction SilentlyContinue)) { Start-Process -WindowStyle Hidden -FilePath 'py' -ArgumentList '-m uvicorn backendreal:app --host 127.0.0.1 --port 5501' }""", 0, False

' Start Python FastAPI RAG Resume Analyzer (port 5503) silently in background
WshShell.Run "powershell -NoProfile -ExecutionPolicy Bypass -Command ""Start-Process -WindowStyle Hidden -FilePath 'py' -ArgumentList '-m uvicorn app1:app --host 127.0.0.1 --port 5503'""", 0, False

' Start Express Node Server (port 8800) silently in background
WshShell.Run "powershell -NoProfile -ExecutionPolicy Bypass -Command ""Start-Process -WindowStyle Hidden -FilePath 'node' -ArgumentList 'server.js'""", 0, False
