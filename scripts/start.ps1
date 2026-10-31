param([ValidateSet('all','backend','frontend')][string]$Service = 'all')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $projectRoot '.alibi'
New-Item -ItemType Directory -Force $runtimeDir | Out-Null
if ($Service -in @('all','backend')) {
    $pythonExe = Join-Path $projectRoot '.venv/Scripts/python.exe'
    if (!(Test-Path -LiteralPath $pythonExe)) { throw 'Run scripts/setup.ps1 first.' }
    $running = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($running) { Write-Host 'Port 8000 already has a listener; backend was not started again.' }
    else {
        $backendProcess = Start-Process -FilePath $pythonExe -ArgumentList '-m uvicorn alibi.main:app --app-dir src/backend --host 127.0.0.1 --port 8000' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimeDir 'backend.stdout.log') -RedirectStandardError (Join-Path $runtimeDir 'backend.stderr.log') -PassThru
        $backendProcess.Id | Set-Content (Join-Path $runtimeDir 'backend.pid')
        Write-Host "Backend PID $($backendProcess.Id): http://127.0.0.1:8000/api/docs"
    }
}
if ($Service -in @('all','frontend')) {
    $nodeExe = (Get-Command node -ErrorAction Stop).Source
    $frontendDir = Join-Path $projectRoot 'src/frontend'
    if (!(Test-Path (Join-Path $frontendDir 'node_modules/vite/bin/vite.js'))) { throw 'Run scripts/setup.ps1 first.' }
    $running = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
    if ($running) { Write-Host 'Port 5173 already has a listener; frontend was not started again.' }
    else {
        $frontendProcess = Start-Process -FilePath $nodeExe -ArgumentList 'node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173' -WorkingDirectory $frontendDir -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimeDir 'frontend.stdout.log') -RedirectStandardError (Join-Path $runtimeDir 'frontend.stderr.log') -PassThru
        $frontendProcess.Id | Set-Content (Join-Path $runtimeDir 'frontend.pid')
        Write-Host "Frontend PID $($frontendProcess.Id): http://127.0.0.1:5173"
    }
}
