$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir
$logPath = Join-Path $scriptDir "backendreal.log"

Write-Output "Starting backendreal FastAPI backend on 0.0.0.0:5501..." | Tee-Object -FilePath $logPath

$command = "py -m uvicorn backendreal:app --host 0.0.0.0 --port 5501"
& py -m uvicorn backendreal:app --host 0.0.0.0 --port 5501 2>&1 | Tee-Object -FilePath $logPath
